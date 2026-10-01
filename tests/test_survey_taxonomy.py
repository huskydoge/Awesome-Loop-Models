import unittest
from pathlib import Path

import yaml

from scripts import build

REPO_ROOT = Path(__file__).resolve().parents[1]


class SurveyTaxonomyFieldTests(unittest.TestCase):
    def test_valid_fields_are_normalized(self):
        result = build.normalize_survey_fields(
            {
                "survey_section": ["design/topology", "scaling/test-time"],
                "loop_topology": "prelude-core-coda",
                "sharing": "full",
                "depth_control": "sampled-train",
                "claims": ["test-time-scaling"],
                "comparison": [],
                "survey_core": True,
            },
            "x.yaml",
        )
        self.assertEqual(result["survey_section"], ["design/topology", "scaling/test-time"])
        self.assertEqual(result["comparison"], [])
        self.assertTrue(result["survey_core"])

    def test_missing_fields_are_omitted(self):
        self.assertEqual(build.normalize_survey_fields({}, "x.yaml"), {})

    def test_invalid_values_are_rejected(self):
        for data in (
            {"survey_section": ["design/unknown"]},
            {"survey_section": []},
            {"loop_topology": "flat"},
            {"sharing": "tied"},
            {"depth_control": "dynamic"},
            {"claims": ["speed"]},
            {"comparison": ["iso-time"]},
            {"survey_core": "yes"},
        ):
            with self.subTest(data=data), self.assertRaises(ValueError):
                build.normalize_survey_fields(data, "x.yaml")

    def test_vocabularies_are_consistent(self):
        self.assertEqual(len(build.VALID_SURVEY_SECTIONS), len(set(build.VALID_SURVEY_SECTIONS)))

    def test_browser_entries_keep_survey_fields(self):
        entry = {"id": "x", "entry_type": "paper", "survey_section": ["interpretability"], "loop_topology": "whole-stack",
                 "sharing": "full", "depth_control": "fixed", "claims": [], "comparison": [], "survey_core": False}
        browser_entry = build.serialize_browser_entry(entry)
        for field in build.SURVEY_FIELDS:
            self.assertIn(field, browser_entry)

    def test_catalog_papers_use_valid_survey_fields(self):
        for path in sorted((REPO_ROOT / "papers").glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            build.normalize_survey_fields(data, path.name)


if __name__ == "__main__":
    unittest.main()
