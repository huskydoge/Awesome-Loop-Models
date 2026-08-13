"""Contract tests for the read-only canonical paper catalog auditor."""

from __future__ import annotations

import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from scripts import audit_catalog


def valid_paper(arxiv_id: str = "2601.00001") -> dict:
    """Return a minimal valid raw canonical paper record."""
    return {
        "title": "A Looped Model",
        "authors": ["Ada Example"],
        "year": 2026,
        "published_date": "2026-01-02",
        "venue": "arXiv",
        "category": "designs",
        "mechanism_tags": ["flat-loop"],
        "domain_tags": ["reasoning"],
        "focus_tags": ["architecture"],
        "desc": "Introduces a shared block that is reused within one forward pass.",
        "links": {"arxiv": f"https://arxiv.org/abs/{arxiv_id}"},
    }


def write_paper(root: Path, filename: str, paper: object) -> Path:
    """Write one YAML paper fixture below ``root`` and return its path."""
    path = root / "papers" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(paper, sort_keys=False), encoding="utf-8")
    return path


class CatalogAuditTests(unittest.TestCase):
    """Exercise raw YAML, schema, identity, tag, and prose findings."""

    def test_valid_catalog_has_no_findings_and_skips_templates(self):
        """A valid paper should pass while template-prefixed YAML stays out of scope."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_paper(root, "2601.00001.yaml", valid_paper())
            write_paper(root, "_template-invalid.yaml", {"unexpected": True})

            findings = audit_catalog.audit_catalog(root)

        self.assertEqual(findings, [])

    def test_adjacent_fit_allows_an_empty_mechanism_list(self):
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper()
            paper["catalog_fit"] = "adjacent"
            paper["mechanism_tags"] = []
            write_paper(root, "2601.00001.yaml", paper)

            findings = audit_catalog.audit_catalog(root)

        self.assertEqual(findings, [])

    def test_unknown_catalog_fit_is_rejected(self):
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper()
            paper["catalog_fit"] = "borderline"
            write_paper(root, "2601.00001.yaml", paper)

            findings = audit_catalog.audit_catalog(root)

        self.assertIn(
            ("invalid-catalog-fit", "catalog_fit"),
            {(item.code, item.field) for item in findings},
        )

    def test_yaml_and_top_level_failures_are_reported_without_hiding_raw_data(self):
        """Malformed YAML and non-mapping documents should produce stable errors."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            malformed = root / "papers" / "a.yaml"
            malformed.parent.mkdir(parents=True)
            malformed.write_text("title: [unterminated\n", encoding="utf-8")
            write_paper(root, "b.yaml", ["not", "a", "mapping"])

            findings = audit_catalog.audit_catalog(root)

        self.assertEqual(
            [(item.code, item.source, item.field) for item in findings],
            [
                ("yaml-parse", "papers/a.yaml", "$"),
                ("top-level-type", "papers/b.yaml", "$"),
            ],
        )

    def test_duplicate_yaml_keys_are_rejected_at_top_level_and_in_links(self):
        """Raw duplicate mapping keys should error instead of being silently overwritten."""
        cases = (
            ("title: First\ntitle: Second\n", "title"),
            (
                "links:\n"
                "  arxiv: https://arxiv.org/abs/2601.00001\n"
                "  arxiv: https://arxiv.org/abs/2601.00002\n",
                "arxiv",
            ),
        )
        for raw_yaml, duplicate_key in cases:
            with self.subTest(duplicate_key=duplicate_key):
                with TemporaryDirectory() as tmpdir:
                    root = Path(tmpdir)
                    path = root / "papers" / "duplicate.yaml"
                    path.parent.mkdir(parents=True)
                    path.write_text(raw_yaml, encoding="utf-8")

                    findings = audit_catalog.audit_catalog(root)

                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0].code, "duplicate-yaml-key")
                self.assertEqual(findings[0].field, "$")
                self.assertIn(repr(duplicate_key), findings[0].message)

    def test_required_fields_types_unknown_fields_and_dates_are_checked(self):
        """The auditor should inspect raw required fields before build normalization."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper()
            del paper["authors"]
            paper["title"] = 42
            paper["year"] = 2025
            paper["published_date"] = "2026-02-30"
            paper["mystery"] = "hidden by normalization"
            write_paper(root, "2601.00001.yaml", paper)

            findings = audit_catalog.audit_catalog(root)

        by_code = {(item.code, item.field): item for item in findings}
        self.assertIn(("missing-field", "authors"), by_code)
        self.assertIn(("invalid-field-type", "title"), by_code)
        self.assertIn(("invalid-date", "published_date"), by_code)
        self.assertIn(("unknown-field", "mystery"), by_code)
        self.assertNotIn(("year-date-mismatch", "year"), by_code)

    def test_year_date_mismatch_and_optional_dates_are_warnings_or_errors(self):
        """A valid but different publication year warns; malformed optional dates error."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper()
            paper["year"] = 2027
            paper["added_date"] = "2026/01/03"
            write_paper(root, "2601.00001.yaml", paper)

            findings = audit_catalog.audit_catalog(root)

        self.assertIn(
            ("warning", "year-date-mismatch", "year"),
            {(item.severity, item.code, item.field) for item in findings},
        )
        self.assertIn(
            ("error", "invalid-date", "added_date"),
            {(item.severity, item.code, item.field) for item in findings},
        )

    def test_links_require_mapping_http_urls_and_a_primary_paper_link(self):
        """Link structure, scheme, and canonical-paper availability are errors."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper()
            paper["links"] = {
                "github": "git://example.com/project",
                "project": 123,
            }
            write_paper(root, "loop-paper.yaml", paper)

            findings = audit_catalog.audit_catalog(root)

        keys = {(item.code, item.field) for item in findings}
        self.assertIn(("invalid-url", "links.github"), keys)
        self.assertIn(("invalid-link-type", "links.project"), keys)
        self.assertIn(("missing-primary-link", "links"), keys)

    def test_malformed_url_is_reported_instead_of_crashing(self):
        """A URL parser ValueError should become a normal invalid-url finding."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper()
            paper["links"]["project"] = "https://[::1"
            write_paper(root, "2601.00001.yaml", paper)

            findings = audit_catalog.audit_catalog(root)

        self.assertIn(
            ("invalid-url", "links.project"),
            {(item.code, item.field) for item in findings},
        )

    def test_arxiv_filename_and_link_identifiers_must_match(self):
        """An arXiv-backed record should use the same ID in its filename and URL."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper("2601.99999")
            write_paper(root, "2601.00001.yaml", paper)

            findings = audit_catalog.audit_catalog(root)

        mismatch = [item for item in findings if item.code == "arxiv-id-mismatch"]
        self.assertEqual(len(mismatch), 1)
        self.assertEqual(mismatch[0].field, "links.arxiv")
        self.assertIn("2601.00001", mismatch[0].message)
        self.assertIn("2601.99999", mismatch[0].message)

    def test_duplicate_normalized_title_and_primary_source_name_first_conflict(self):
        """Duplicate findings should point to the deterministic first conflicting source."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first = valid_paper("2601.00001")
            second = valid_paper("2601.00002")
            second["title"] = "  A   LOOPED model!  "
            second["links"]["arxiv"] = "https://arxiv.org/pdf/2601.00001v2.pdf"
            write_paper(root, "2601.00001.yaml", first)
            write_paper(root, "2601.00002.yaml", second)

            findings = audit_catalog.audit_catalog(root)

        duplicate_codes = {
            item.code: item for item in findings if item.code.startswith("duplicate-")
        }
        self.assertEqual(
            set(duplicate_codes),
            {"duplicate-primary-source", "duplicate-title"},
        )
        for finding in duplicate_codes.values():
            self.assertEqual(finding.source, "papers/2601.00002.yaml")
            self.assertIn("papers/2601.00001.yaml", finding.message)

    def test_all_primary_links_are_indexed_for_duplicate_sources(self):
        """A shared OpenReview identity should collide despite distinct arXiv IDs."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first = valid_paper("2601.00001")
            first["title"] = "First paper"
            first["links"]["paper"] = "https://openreview.net/forum?id=shared-id"
            second = valid_paper("2601.00002")
            second["title"] = "Second paper"
            second["links"]["openreview"] = (
                "https://openreview.net/forum?id=shared-id"
            )
            write_paper(root, "2601.00001.yaml", first)
            write_paper(root, "2601.00002.yaml", second)

            findings = audit_catalog.audit_catalog(root)

        duplicates = [
            item for item in findings if item.code == "duplicate-primary-source"
        ]
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0].source, "papers/2601.00002.yaml")
        self.assertEqual(duplicates[0].field, "links.openreview")
        self.assertIn("papers/2601.00001.yaml", duplicates[0].message)
        self.assertIn("links.paper", duplicates[0].message)

    def test_same_entry_primary_links_with_one_identity_do_not_self_conflict(self):
        """Equivalent arXiv links in two fields should be indexed once per paper."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper("2601.00001")
            paper["links"]["paper"] = "https://arxiv.org/pdf/2601.00001v2.pdf"
            write_paper(root, "2601.00001.yaml", paper)

            findings = audit_catalog.audit_catalog(root)

        self.assertNotIn(
            "duplicate-primary-source",
            {item.code for item in findings},
        )

    def test_tag_shape_duplicates_allowlists_and_cross_axis_collisions(self):
        """Raw tag arrays should retain shape and respect controlled vocabularies."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper()
            paper["mechanism_tags"] = ["flat-loop", "Flat Loop", ""]
            paper["focus_tags"] = "architecture"
            paper["domain_tags"] = ["reasoning", "architecture"]
            paper["tags"] = ["reasoning"]
            write_paper(root, "2601.00001.yaml", paper)

            findings = audit_catalog.audit_catalog(root)

        keys = {(item.code, item.field) for item in findings}
        self.assertIn(("duplicate-tag", "mechanism_tags[1]"), keys)
        self.assertIn(("invalid-mechanism-tag", "mechanism_tags[1]"), keys)
        self.assertIn(("empty-tag", "mechanism_tags[2]"), keys)
        self.assertIn(("invalid-tag-list", "focus_tags"), keys)
        self.assertIn(("cross-axis-tag-collision", "domain_tags[1]"), keys)
        self.assertIn(("cross-axis-tag-collision", "tags[0]"), keys)

    def test_required_tag_lists_cannot_be_empty_but_optional_tags_can(self):
        """Every required tag axis should contain a value while aliases may be empty."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper()
            paper["mechanism_tags"] = []
            paper["domain_tags"] = []
            paper["focus_tags"] = []
            paper["tags"] = []
            write_paper(root, "2601.00001.yaml", paper)

            findings = audit_catalog.audit_catalog(root)

        empty_fields = {
            item.field for item in findings if item.code == "empty-field"
        }
        self.assertEqual(
            empty_fields,
            {"mechanism_tags", "domain_tags", "focus_tags"},
        )

    def test_valid_optional_metadata_types_have_no_findings(self):
        """Every allowed optional field should accept its canonical raw type."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper()
            paper.update(
                {
                    "added_date": "2026-01-03",
                    "citation_source_best": "semantic_scholar",
                    "citation_sources": {"semantic_scholar": 0},
                    "citations": 0,
                    "foundation": False,
                    "github_stars": 3,
                    "metrics_updated": "2026-01-04",
                    "must_read": True,
                    "star_source_best": "github_api",
                    "star_sources": {"github_api": 3},
                    "tags": [],
                }
            )
            write_paper(root, "2601.00001.yaml", paper)

            findings = audit_catalog.audit_catalog(root)

        self.assertEqual(findings, [])

    def test_invalid_optional_metadata_types_report_precise_field_paths(self):
        """Optional scalars, counters, and source mappings should retain raw types."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper()
            paper.update(
                {
                    "foundation": "false",
                    "must_read": 1,
                    "citations": True,
                    "github_stars": -1,
                    "citation_source_best": "",
                    "star_source_best": 7,
                    "citation_sources": {
                        "": 0,
                        "semantic_scholar": True,
                        "openalex": -1,
                    },
                    "star_sources": [],
                }
            )
            write_paper(root, "2601.00001.yaml", paper)

            findings = audit_catalog.audit_catalog(root)

        keys = {(item.code, item.field) for item in findings}
        for field in (
            "foundation",
            "must_read",
            "citations",
            "github_stars",
            "citation_source_best",
            "star_source_best",
            "star_sources",
        ):
            with self.subTest(field=field):
                self.assertIn(("invalid-field-type", field), keys)
        self.assertIn(("invalid-map-key", "citation_sources['']"), keys)
        self.assertIn(
            ("invalid-map-value", "citation_sources.semantic_scholar"), keys
        )
        self.assertIn(("invalid-map-value", "citation_sources.openalex"), keys)

    def test_description_soft_limits_are_warnings(self):
        """Long or multi-sentence descriptions should warn without becoming errors."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper()
            paper["desc"] = "First claim. " + ("A" * (audit_catalog.DESC_LENGTH_LIMIT + 1))
            write_paper(root, "2601.00001.yaml", paper)

            findings = audit_catalog.audit_catalog(root)

        warnings = {(item.severity, item.code) for item in findings}
        self.assertIn(("warning", "desc-too-long"), warnings)
        self.assertIn(("warning", "desc-multiple-sentences"), warnings)


class CatalogAuditCliTests(unittest.TestCase):
    """Lock down deterministic sorting, serialization, and exit behavior."""

    def test_json_output_is_exact_and_errors_exit_one(self):
        """JSON mode should be stable and return one when any error exists."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper()
            paper["year"] = 2027
            paper["category"] = "legacy"
            write_paper(root, "2601.00001.yaml", paper)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = audit_catalog.main(
                    ["--root", str(root), "--format", "json"]
                )

        expected = {
            "counts": {"error": 1, "warning": 1},
            "findings": [
                {
                    "severity": "error",
                    "code": "invalid-category",
                    "source": "papers/2601.00001.yaml",
                    "field": "category",
                    "message": (
                        "Expected one of analysis, applications, designs; got 'legacy'."
                    ),
                },
                {
                    "severity": "warning",
                    "code": "year-date-mismatch",
                    "source": "papers/2601.00001.yaml",
                    "field": "year",
                    "message": (
                        "year is 2027 but published_date starts with 2026."
                    ),
                },
            ],
        }
        self.assertEqual(exit_code, 1)
        self.assertEqual(
            stdout.getvalue(),
            json.dumps(expected, indent=2, sort_keys=True) + "\n",
        )

    def test_human_output_contains_all_fields_and_warning_only_exits_zero(self):
        """Human mode should show the full finding record and allow warning-only runs."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper = valid_paper()
            paper["year"] = 2027
            write_paper(root, "2601.00001.yaml", paper)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = audit_catalog.main(
                    ["--root", str(root), "--format", "human"]
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            stdout.getvalue(),
            "Catalog audit: 0 error(s), 1 warning(s)\n"
            "WARNING year-date-mismatch papers/2601.00001.yaml "
            "year: year is 2027 but published_date starts with 2026.\n",
        )


if __name__ == "__main__":
    unittest.main()
