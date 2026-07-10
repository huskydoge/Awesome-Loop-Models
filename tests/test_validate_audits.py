"""Contract tests for per-paper evidence audit record validation."""

from __future__ import annotations

import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from scripts import validate_audits


def canonical_paper(paper_id: str = "2601.00001") -> dict:
    """Return a canonical paper fixture with all audited taxonomy axes."""
    return {
        "title": "A Looped Model",
        "authors": ["Ada Example"],
        "year": 2026,
        "published_date": "2026-01-02",
        "venue": "arXiv",
        "category": "designs",
        "mechanism_tags": ["flat-loop"],
        "focus_tags": ["architecture"],
        "domain_tags": ["reasoning"],
        "tags": ["looped-transformer"],
        "desc": "Reuses a learned block within one forward pass.",
        "links": {"arxiv": f"https://arxiv.org/abs/{paper_id}"},
    }


def valid_audit(paper_id: str = "2601.00001") -> dict:
    """Return a complete verified audit matching ``canonical_paper``."""
    return {
        "paper_id": paper_id,
        "status": "verified",
        "source": {
            "url": f"https://arxiv.org/abs/{paper_id}",
            "version": "v2",
            "verified_on": "2026-07-10",
        },
        "reviewer": "Codex review run 2026-07-10",
        "confidence": "high",
        "scope": {
            "verdict": "in-scope",
            "evidence": "The same learned block is applied at every recurrent step.",
            "locator": "Section 3, Equation 2",
        },
        "taxonomy": {
            "category": {
                "value": "designs",
                "rationale": "The primary contribution is a recurrent architecture.",
            },
            "mechanism_tags": {
                "values": ["flat-loop"],
                "rationale": "One flat recurrent block is reused.",
            },
            "focus_tags": {
                "values": ["architecture"],
                "rationale": "The paper changes the model architecture.",
            },
            "domain_tags": {
                "values": ["reasoning"],
                "rationale": "The evaluated domain is multi-step reasoning.",
            },
            "tags": {
                "values": ["looped-transformer"],
                "rationale": "The alias matches the authors' model family.",
            },
        },
        "content_checks": {
            name: {
                "status": "verified",
                "evidence": f"Primary source confirms {name.replace('_', ' ')}.",
            }
            for name in ("title_authors", "publication", "description", "links")
        },
        "unresolved_questions": [],
    }


def write_yaml(root: Path, relative_path: str, value: object) -> Path:
    """Write a YAML fixture beneath ``root`` and return its path."""
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    return path


def write_raw(root: Path, relative_path: str, value: str) -> Path:
    """Write a raw fixture beneath ``root`` and return its path."""
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    return path


class AuditValidationTests(unittest.TestCase):
    """Exercise schema, parity, decision, coverage, and output contracts."""

    def test_missing_papers_directory_fails_partial_and_complete_modes(self):
        """A missing canonical source directory must never look like 0/0 success."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            partial = validate_audits.validate_audits(root)
            complete = validate_audits.validate_audits(
                root, require_complete=True
            )

        for result in (partial, complete):
            self.assertFalse(result.valid)
            self.assertIn(
                "missing-papers-directory",
                {finding.code for finding in result.findings},
            )
            self.assertEqual(result.coverage.canonical_papers, 0)

    def test_complete_mode_rejects_an_empty_canonical_directory(self):
        """An existing but empty papers directory cannot satisfy the final gate."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "papers").mkdir()

            result = validate_audits.validate_audits(
                root, require_complete=True
            )

        self.assertFalse(result.valid)
        self.assertIn(
            "empty-canonical-catalog",
            {finding.code for finding in result.findings},
        )

    def test_valid_verified_record_is_a_complete_decision(self):
        """A fully evidenced matching record should pass complete mode."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_yaml(root, "papers/2601.00001.yaml", canonical_paper())
            write_yaml(root, "audits/papers/2601.00001.yaml", valid_audit())

            result = validate_audits.validate_audits(root, require_complete=True)

        self.assertEqual(result.findings, ())
        self.assertEqual(result.coverage.canonical_papers, 1)
        self.assertEqual(result.coverage.audit_records, 1)
        self.assertEqual(result.coverage.covered_papers, 1)
        self.assertEqual(result.coverage.verified, 1)
        self.assertEqual(result.coverage.complete_decisions, 1)
        self.assertEqual(result.coverage.missing_papers, 0)

    def test_needs_review_and_missing_records_are_valid_in_partial_mode(self):
        """Migration mode should count incomplete coverage without failing it."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_yaml(root, "papers/2601.00001.yaml", canonical_paper())
            write_yaml(root, "papers/2601.00002.yaml", canonical_paper("2601.00002"))
            audit = valid_audit()
            audit["status"] = "needs-review"
            audit["confidence"] = "low"
            audit["scope"]["verdict"] = "uncertain"
            audit["content_checks"]["description"]["status"] = "unresolved"
            audit["unresolved_questions"] = ["Does the ablation isolate weight reuse?"]
            write_yaml(root, "audits/papers/2601.00001.yaml", audit)

            result = validate_audits.validate_audits(root)

        self.assertEqual(result.findings, ())
        self.assertEqual(result.coverage.needs_review, 1)
        self.assertEqual(result.coverage.missing_papers, 1)
        self.assertEqual(result.coverage.complete_decisions, 0)

    def test_require_complete_rejects_missing_and_needs_review_records(self):
        """The final gate should require one completed decision for every paper."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_yaml(root, "papers/2601.00001.yaml", canonical_paper())
            write_yaml(root, "papers/2601.00002.yaml", canonical_paper("2601.00002"))
            audit = valid_audit()
            audit["status"] = "needs-review"
            write_yaml(root, "audits/papers/2601.00001.yaml", audit)

            result = validate_audits.validate_audits(root, require_complete=True)

        self.assertEqual(
            {finding.code for finding in result.findings},
            {"incomplete-review", "missing-audit"},
        )

    def test_remove_is_complete_only_with_out_of_scope_evidence(self):
        """An evidenced out-of-scope removal should satisfy complete mode."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_yaml(root, "papers/2601.00001.yaml", canonical_paper())
            audit = valid_audit()
            audit["status"] = "remove"
            audit["confidence"] = "medium"
            audit["scope"] = {
                "verdict": "out-of-scope",
                "evidence": "Each layer has distinct learned parameters.",
                "locator": "Appendix A, Table 7",
            }
            audit["content_checks"]["description"]["status"] = "issue"
            audit["unresolved_questions"] = ["Should this move to a related-work list?"]
            write_yaml(root, "audits/papers/2601.00001.yaml", audit)

            valid_result = validate_audits.validate_audits(
                root, require_complete=True
            )

            audit["scope"]["verdict"] = "uncertain"
            write_yaml(root, "audits/papers/2601.00001.yaml", audit)
            invalid_result = validate_audits.validate_audits(root)

        self.assertEqual(valid_result.findings, ())
        self.assertEqual(valid_result.coverage.remove, 1)
        self.assertEqual(valid_result.coverage.complete_decisions, 1)
        self.assertIn(
            "remove-scope",
            {finding.code for finding in invalid_result.findings},
        )
        self.assertEqual(invalid_result.coverage.remove, 0)
        self.assertEqual(invalid_result.coverage.complete_decisions, 0)

    def test_filename_paper_id_and_canonical_source_must_match(self):
        """Record identity should agree with its path and primary-source identity."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_yaml(root, "papers/2601.00001.yaml", canonical_paper())
            audit = valid_audit()
            audit["source"]["url"] = "https://arxiv.org/pdf/2601.99999v1.pdf"
            write_yaml(root, "audits/papers/wrong-name.yaml", audit)

            result = validate_audits.validate_audits(root)

        codes = {finding.code for finding in result.findings}
        self.assertIn("filename-id-mismatch", codes)
        self.assertIn("source-id-mismatch", codes)
        self.assertEqual(result.coverage.verified, 0)
        self.assertEqual(result.coverage.complete_decisions, 0)

    def test_duplicate_and_unknown_audit_ids_are_errors(self):
        """Orphan records and repeated logical IDs should always fail."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_yaml(root, "papers/2601.00001.yaml", canonical_paper())
            write_yaml(root, "audits/papers/2601.00001.yaml", valid_audit())
            write_yaml(root, "audits/papers/duplicate.yaml", valid_audit())
            write_yaml(root, "audits/papers/ghost.yaml", valid_audit("ghost"))

            result = validate_audits.validate_audits(root)

        codes = {finding.code for finding in result.findings}
        self.assertIn("duplicate-audit-id", codes)
        self.assertIn("unknown-paper-id", codes)

    def test_missing_or_empty_evidence_is_rejected(self):
        """Every scope, taxonomy, and content judgment needs written evidence."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_yaml(root, "papers/2601.00001.yaml", canonical_paper())
            audit = valid_audit()
            audit["scope"]["evidence"] = ""
            del audit["scope"]["locator"]
            audit["taxonomy"]["category"]["rationale"] = "  "
            audit["content_checks"]["links"]["evidence"] = ""
            write_yaml(root, "audits/papers/2601.00001.yaml", audit)

            result = validate_audits.validate_audits(root)

        fields = {finding.field for finding in result.findings}
        self.assertIn("scope.evidence", fields)
        self.assertIn("scope.locator", fields)
        self.assertIn("taxonomy.category.rationale", fields)
        self.assertIn("content_checks.links.evidence", fields)
        self.assertEqual(result.coverage.verified, 0)
        self.assertEqual(result.coverage.complete_decisions, 0)

    def test_verified_taxonomy_must_exactly_match_canonical_yaml(self):
        """A verified ledger may not silently drift from canonical metadata."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_yaml(root, "papers/2601.00001.yaml", canonical_paper())
            audit = valid_audit()
            audit["taxonomy"]["category"]["value"] = "analysis"
            audit["taxonomy"]["mechanism_tags"]["values"] = ["parallel-loop"]
            write_yaml(root, "audits/papers/2601.00001.yaml", audit)

            result = validate_audits.validate_audits(root)

        drift_fields = {
            finding.field
            for finding in result.findings
            if finding.code == "taxonomy-drift"
        }
        self.assertEqual(
            drift_fields,
            {"taxonomy.category.value", "taxonomy.mechanism_tags.values"},
        )
        self.assertEqual(result.coverage.verified, 0)
        self.assertEqual(result.coverage.complete_decisions, 0)

    def test_invalid_canonical_paper_cannot_complete_a_verified_decision(self):
        """Record validity must include the corresponding canonical source."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = canonical_paper()
            paper["category"] = 42
            write_yaml(root, "papers/2601.00001.yaml", paper)
            write_yaml(root, "audits/papers/2601.00001.yaml", valid_audit())

            result = validate_audits.validate_audits(root)

        self.assertFalse(result.valid)
        self.assertEqual(result.coverage.covered_papers, 1)
        self.assertEqual(result.coverage.verified, 0)
        self.assertEqual(result.coverage.complete_decisions, 0)

    def test_generic_source_url_normalizes_query_order_and_encoding(self):
        """Equivalent generic URLs should match despite query order and encoding."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper_id = "vendor-paper"
            paper = canonical_paper(paper_id)
            paper["links"] = {
                "paper": (
                    "https://papers.example.org/view/?b=2&a=hello%20world#source"
                )
            }
            audit = valid_audit(paper_id)
            audit["source"]["url"] = (
                "https://papers.example.org/view?a=hello+world&b=2"
            )
            write_yaml(root, f"papers/{paper_id}.yaml", paper)
            write_yaml(root, f"audits/papers/{paper_id}.yaml", audit)

            result = validate_audits.validate_audits(
                root, require_complete=True
            )

        self.assertEqual(result.findings, ())
        self.assertEqual(result.coverage.verified, 1)
        self.assertEqual(result.coverage.complete_decisions, 1)

    def test_invalid_status_confidence_date_and_url_are_rejected(self):
        """Scalar enums and source fields should follow the published schema."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_yaml(root, "papers/2601.00001.yaml", canonical_paper())
            audit = valid_audit()
            audit["status"] = "done"
            audit["confidence"] = "certain"
            audit["source"]["verified_on"] = "2026-02-30"
            audit["source"]["url"] = "file:///tmp/paper.pdf"
            write_yaml(root, "audits/papers/2601.00001.yaml", audit)

            result = validate_audits.validate_audits(root)

        codes = {finding.code for finding in result.findings}
        self.assertIn("invalid-enum", codes)
        self.assertIn("invalid-date", codes)
        self.assertIn("invalid-url", codes)

    def test_verified_content_confidence_scope_and_questions_are_strict(self):
        """Verified means resolved content, in-scope evidence, and medium confidence."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_yaml(root, "papers/2601.00001.yaml", canonical_paper())
            audit = valid_audit()
            audit["confidence"] = "low"
            audit["scope"]["verdict"] = "uncertain"
            audit["content_checks"]["description"]["status"] = "issue"
            audit["unresolved_questions"] = ["Is the main claim source-backed?"]
            write_yaml(root, "audits/papers/2601.00001.yaml", audit)

            result = validate_audits.validate_audits(root)

        self.assertEqual(
            {
                "verified-confidence",
                "verified-content",
                "verified-scope",
                "verified-unresolved",
            },
            {finding.code for finding in result.findings},
        )

    def test_shape_unknown_fields_and_duplicate_lists_are_rejected(self):
        """Strict mappings and unique string lists should expose schema mistakes."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_yaml(root, "papers/2601.00001.yaml", canonical_paper())
            audit = valid_audit()
            audit["unexpected"] = True
            audit["taxonomy"]["domain_tags"]["values"] = [
                "reasoning",
                "reasoning",
            ]
            audit["unresolved_questions"] = "none"
            write_yaml(root, "audits/papers/2601.00001.yaml", audit)
            write_yaml(root, "audits/papers/not-a-mapping.yaml", ["invalid"])
            write_raw(
                root,
                "audits/papers/malformed.yaml",
                "paper_id: [unterminated\n",
            )

            result = validate_audits.validate_audits(root)

        codes = {finding.code for finding in result.findings}
        self.assertIn("unknown-field", codes)
        self.assertIn("duplicate-list-item", codes)
        self.assertIn("invalid-field-type", codes)
        self.assertIn("top-level-type", codes)
        self.assertIn("yaml-parse", codes)

    def test_duplicate_yaml_keys_are_rejected_in_papers_and_audits(self):
        """Duplicate mapping keys must not be silently overwritten at any depth."""
        cases = (
            (
                "papers/2601.00001.yaml",
                "title: First\ntitle: Second\n",
            ),
            (
                "audits/papers/2601.00001.yaml",
                "paper_id: 2601.00001\nstatus: verified\nstatus: remove\n",
            ),
        )
        for relative_path, raw_yaml in cases:
            with self.subTest(relative_path=relative_path):
                with TemporaryDirectory() as tmpdir:
                    root = Path(tmpdir)
                    if relative_path.startswith("audits/"):
                        write_yaml(
                            root,
                            "papers/2601.00001.yaml",
                            canonical_paper(),
                        )
                    write_raw(root, relative_path, raw_yaml)

                    result = validate_audits.validate_audits(root)

                self.assertIn(
                    "duplicate-yaml-key",
                    {finding.code for finding in result.findings},
                )

    def test_cli_json_is_stable_and_exit_status_tracks_errors(self):
        """JSON output should be repeatable and errors should return status one."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_yaml(root, "papers/2601.00001.yaml", canonical_paper())
            write_yaml(root, "audits/papers/2601.00001.yaml", valid_audit())
            outputs = []
            exit_codes = []
            for _ in range(2):
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream):
                    exit_codes.append(
                        validate_audits.main(
                            ["--root", str(root), "--format", "json"]
                        )
                    )
                outputs.append(stream.getvalue())

            error_stream = io.StringIO()
            with contextlib.redirect_stdout(error_stream):
                error_exit = validate_audits.main(
                    [
                        "--root",
                        str(root),
                        "--format",
                        "json",
                        "--require-complete",
                    ]
                )

        self.assertEqual(exit_codes, [0, 0])
        self.assertEqual(outputs[0], outputs[1])
        self.assertTrue(json.loads(outputs[0])["valid"])
        self.assertEqual(error_exit, 0)
        self.assertTrue(json.loads(error_stream.getvalue())["valid"])

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_yaml(root, "papers/2601.00001.yaml", canonical_paper())
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                exit_code = validate_audits.main(
                    [
                        "--root",
                        str(root),
                        "--format",
                        "json",
                        "--require-complete",
                    ]
                )

        self.assertEqual(exit_code, 1)
        self.assertFalse(json.loads(stream.getvalue())["valid"])

    def test_templates_are_skipped_in_both_source_directories(self):
        """Template-prefixed YAML files must not count as sources or records."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_yaml(root, "papers/2601.00001.yaml", canonical_paper())
            write_yaml(root, "papers/_template-invalid.yaml", {"bad": True})
            write_yaml(root, "audits/papers/2601.00001.yaml", valid_audit())
            write_yaml(root, "audits/papers/_template-invalid.yaml", {"bad": True})

            result = validate_audits.validate_audits(root, require_complete=True)

        self.assertEqual(result.findings, ())
        self.assertEqual(result.coverage.canonical_papers, 1)
        self.assertEqual(result.coverage.audit_records, 1)


if __name__ == "__main__":
    unittest.main()
