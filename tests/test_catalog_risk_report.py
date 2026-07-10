"""Contract tests for deterministic catalog risk report generation."""

from __future__ import annotations

import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from scripts import audit_catalog, build_catalog_risk_report


SNAPSHOT_COMMIT = "a" * 40


def valid_paper(paper_id: str) -> dict:
    """Return one minimal valid canonical paper fixture."""
    return {
        "title": f"Looped model {paper_id}",
        "authors": ["Ada Example"],
        "year": 2026,
        "published_date": "2026-01-02",
        "venue": "arXiv",
        "category": "designs",
        "mechanism_tags": ["flat-loop"],
        "domain_tags": ["shared-domain"],
        "focus_tags": ["architecture"],
        "desc": "Reuses one learned block within a single forward pass.",
        "links": {"arxiv": f"https://arxiv.org/abs/{paper_id}"},
    }


def write_paper(root: Path, paper_id: str, paper: object) -> Path:
    """Write one raw paper fixture and return its canonical path."""
    path = root / "papers" / f"{paper_id}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(paper, sort_keys=False), encoding="utf-8")
    return path


def build_four_priority_report(root: Path) -> dict:
    """Create a four-paper catalog exercising every priority and reason type."""
    p0 = valid_paper("2601.00001")
    del p0["domain_tags"]
    write_paper(root, "2601.00001", p0)

    p1 = valid_paper("2510.03206")
    p1["mechanism_tags"] = ["flat-loop", "parallel-loop"]
    p1["domain_tags"] = ["MoE"]
    p1["tags"] = ["zeta-alias"]
    write_paper(root, "2510.03206", p1)

    p2 = valid_paper("2601.00003")
    p2["year"] = 2027
    write_paper(root, "2601.00003", p2)

    p3 = valid_paper("2601.00004")
    p3["tags"] = ["MoE"]
    write_paper(root, "2601.00004", p3)

    findings = audit_catalog.audit_catalog(root)
    return build_catalog_risk_report.build_catalog_risk_report(
        root=root,
        findings=findings,
        generated_on="2026-07-10",
        catalog_commit=SNAPSHOT_COMMIT,
    )


class CatalogRiskReportTests(unittest.TestCase):
    """Exercise priority, singleton, parity, and rendering contracts."""

    def test_build_report_assigns_all_priorities_with_sorted_reasons(self):
        """P0-P3 precedence and reason ordering should be deterministic."""
        with TemporaryDirectory() as tmpdir:
            report = build_four_priority_report(Path(tmpdir))

        self.assertEqual(
            report["batches"],
            {
                "P0": ["2601.00001"],
                "P1": ["2510.03206"],
                "P2": ["2601.00003"],
                "P3": ["2601.00004"],
            },
        )
        rows = {row["paper_id"]: row for row in report["papers"]}
        self.assertEqual(rows["2601.00001"]["reasons"], ["auditor:missing-field"])
        self.assertEqual(
            rows["2510.03206"]["reasons"],
            [
                "manual-scope-review-seed",
                "multiple-mechanism-tags",
                "singleton-alias-tag:zeta-alias",
            ],
        )
        self.assertEqual(
            rows["2601.00003"]["reasons"],
            ["auditor:year-date-mismatch"],
        )
        self.assertEqual(rows["2601.00004"]["reasons"], [])

    def test_cross_axis_occurrences_share_one_singleton_frequency_table(self):
        """A tag seen once per axis should have combined frequency two, not one."""
        with TemporaryDirectory() as tmpdir:
            report = build_four_priority_report(Path(tmpdir))

        rows = {row["paper_id"]: row for row in report["papers"]}
        self.assertNotIn(
            "singleton-domain-tag:MoE",
            rows["2510.03206"]["reasons"],
        )
        self.assertEqual(rows["2601.00004"]["priority"], "P3")
        self.assertNotIn(
            "singleton-alias-tag:MoE",
            rows["2601.00004"]["reasons"],
        )

    def test_small_fixture_has_dynamic_id_and_batch_parity(self):
        """Parity should derive from the fixture catalog rather than a 112-paper constant."""
        with TemporaryDirectory() as tmpdir:
            report = build_four_priority_report(Path(tmpdir))

        row_ids = [row["paper_id"] for row in report["papers"]]
        batch_ids = [paper_id for ids in report["batches"].values() for paper_id in ids]
        self.assertEqual(report["paper_count"], 4)
        self.assertEqual(len(row_ids), len(set(row_ids)))
        self.assertEqual(sorted(row_ids), sorted(batch_ids))
        self.assertIn(
            "all 4 canonical paper records",
            report["priority_rules"]["singleton_frequency"],
        )

    def test_markdown_is_rendered_from_report_counts_and_batch_ids(self):
        """Markdown counts and coverage IDs should agree with the JSON report dict."""
        with TemporaryDirectory() as tmpdir:
            report = build_four_priority_report(Path(tmpdir))

        markdown = build_catalog_risk_report.render_catalog_risk_markdown(report)

        self.assertIn("**1 errors / 1 warnings**", markdown)
        self.assertIn("**P0 1 / P1 1 / P2 1 / P3 1**", markdown)
        self.assertIn("### P2 — 1 papers", markdown)
        self.assertIn("- 2601.00003", markdown)
        self.assertIn("### P3 — 1 papers", markdown)
        self.assertIn("- 2601.00004", markdown)

    def test_unsafe_raw_yaml_fails_before_classification(self):
        """Malformed and non-mapping YAML should fail with a clear source path."""
        cases = {
            "malformed.yaml": "title: [unterminated\n",
            "non-mapping.yaml": "- not\n- a\n- mapping\n",
        }
        for filename, raw_yaml in cases.items():
            with self.subTest(filename=filename):
                with TemporaryDirectory() as tmpdir:
                    root = Path(tmpdir)
                    path = root / "papers" / filename
                    path.parent.mkdir(parents=True)
                    path.write_text(raw_yaml, encoding="utf-8")
                    findings = audit_catalog.audit_catalog(root)

                    with self.assertRaisesRegex(
                        build_catalog_risk_report.CatalogRiskReportError,
                        f"papers/{filename}",
                    ):
                        build_catalog_risk_report.build_catalog_risk_report(
                            root=root,
                            findings=findings,
                            generated_on="2026-07-10",
                            catalog_commit=SNAPSHOT_COMMIT,
                        )


class CatalogRiskReportCliTests(unittest.TestCase):
    """Exercise snapshot argument validation and report-only writes."""

    def test_cli_writes_both_reports_without_modifying_papers(self):
        """The CLI should write requested outputs while preserving raw paper bytes."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper_path = write_paper(root, "2601.00001", valid_paper("2601.00001"))
            original_paper = paper_path.read_bytes()

            exit_code = build_catalog_risk_report.main(
                [
                    "--root",
                    str(root),
                    "--generated-on",
                    "2026-07-10",
                    "--catalog-commit",
                    SNAPSHOT_COMMIT,
                    "--json-output",
                    "exports/risk.json",
                    "--markdown-output",
                    "exports/risk.md",
                ]
            )

            json_path = root / "exports" / "risk.json"
            markdown_path = root / "exports" / "risk.md"
            report = json.loads(json_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")
            final_paper = paper_path.read_bytes()

        self.assertEqual(exit_code, 0)
        self.assertEqual(final_paper, original_paper)
        self.assertEqual(
            markdown,
            build_catalog_risk_report.render_catalog_risk_markdown(report),
        )

    def test_cli_rejects_invalid_snapshot_arguments(self):
        """Invalid dates and non-40-hex commits should exit through argparse."""
        cases = (
            ("not-a-date", SNAPSHOT_COMMIT),
            ("2026-07-10", "6b460f1"),
        )
        for generated_on, catalog_commit in cases:
            with self.subTest(
                generated_on=generated_on,
                catalog_commit=catalog_commit,
            ):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as raised:
                        build_catalog_risk_report.main(
                            [
                                "--generated-on",
                                generated_on,
                                "--catalog-commit",
                                catalog_commit,
                            ]
                        )

                self.assertEqual(raised.exception.code, 2)
                self.assertIn("error:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
