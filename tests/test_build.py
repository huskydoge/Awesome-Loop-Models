import hashlib
import json
import re
import subprocess
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zoneinfo import ZoneInfo

import yaml

from scripts import add_arxiv_yaml, build


REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_META_PATH = REPO_ROOT / "repo_meta.json"
REPO_META_JS_PATH = REPO_ROOT / "assets" / "repo-meta.js"
DAILY_WATCH_COUNTDOWN_JS_PATH = REPO_ROOT / "assets" / "daily-watch-countdown.js"
ISSUE_TEMPLATE_CONFIG_PATH = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml"
ISSUE_TEMPLATE_CONFIG_TEMPLATE_PATH = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "config.template.yml"
FIX_ERROR_TEMPLATE_PATH = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "fix_error.yml"
PR_TEMPLATE_PATH = REPO_ROOT / ".github" / "pull_request_template.md"
INDEX_HTML_PATH = REPO_ROOT / "index.html"
READING_DESK_JS_PATH = REPO_ROOT / "assets" / "reading-desk.js"
READING_DESK_CSS_PATH = REPO_ROOT / "assets" / "reading-desk.css"
SUBMIT_PAGE_PATH = REPO_ROOT / "submit.html"
CONTRIBUTING_PATH = REPO_ROOT / "CONTRIBUTING.md"
README_HEADER_PATH = REPO_ROOT / "scripts" / "README_HEADER.md"
ADD_ARXIV_YAML_PATH = REPO_ROOT / "scripts" / "add_arxiv_yaml.py"
README_FOOTER_PATH = REPO_ROOT / "scripts" / "README_FOOTER.md"
TAXONOMY_PATH = REPO_ROOT / "TAXONOMY.md"
TAGS_PATH = REPO_ROOT / "TAGS.md"
PAPER_TEMPLATE_PATH = REPO_ROOT / "papers" / "_template.yaml.example"
BLOG_TEMPLATE_PATH = REPO_ROOT / "blogs" / "_template.yaml.example"
BRIEFINGS_DIR = REPO_ROOT / "briefings"
FAVICON_PATH = REPO_ROOT / "assets" / "favicon.png"


def survey_fields(**overrides) -> dict:
    """Return a complete, valid set of paper survey fields with optional overrides."""
    fields = {
        "survey_section": ["architecture/topology", "scaling/test-time"],
        "loop_topology": "prelude-core-coda",
        "sharing": "full",
        "depth_control": "sampled-train",
        "claims": ["test-time-scaling"],
        "comparison": ["iso-param"],
    }
    fields.update(overrides)
    return fields


SURVEY_YAML = (
    "survey_section:\n"
    "  - architecture/topology\n"
    "  - scaling/test-time\n"
    "loop_topology: prelude-core-coda\n"
    "sharing: full\n"
    "depth_control: sampled-train\n"
    "claims:\n"
    "  - test-time-scaling\n"
    "comparison: []\n"
)


class BuildTaxonomyTests(unittest.TestCase):
    def test_peer_review_requires_a_boolean_and_publication_source(self):
        """A venue name or truthy string cannot stand in for verified evidence."""
        valid = {
            "venue": "ICML", "peer_reviewed": True,
            "venue_source": "https://proceedings.mlr.press/v267/schone25a.html",
        }
        build.validate_publication_metadata(valid, "paper.yaml")
        build.validate_publication_metadata({"venue": "arXiv"}, "paper.yaml")
        for overrides in (
            {"peer_reviewed": "true"}, {"venue": "arXiv"},
            {"venue_source": ""}, {"venue_source": "javascript:alert(1)"},
            {"venue_source": "https://user:password@example.org/paper"},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                build.validate_publication_metadata({**valid, **overrides}, "paper.yaml")

    def test_colm_workshop_uses_colm_venue_class(self):
        """A COLM workshop must not fall back to the arXiv badge class."""
        self.assertEqual(
            build.normalize_venue_class("COLM 2025 Workshop", "paper"),
            "venue-colm",
        )

    def test_unknown_paper_venue_uses_other_class(self):
        """An unknown non-arXiv venue should render with the neutral badge."""
        self.assertEqual(
            build.normalize_venue_class("Example Workshop", "paper"),
            "venue-other",
        )

    def test_arxiv_venue_keeps_arxiv_class(self):
        """The canonical arXiv venue should keep its dedicated badge class."""
        self.assertEqual(
            build.normalize_venue_class("arXiv", "paper"),
            "venue-arxiv",
        )

    def test_retired_fields_are_rejected_for_papers(self):
        for field in (*build.RETIRED_FIELDS, "family_tags"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, f"{field} no longer exist"):
                    build.normalize_paper_taxonomy_fields({field: "anything"}, "paper.yaml")

    def test_retired_field_vocabulary_matches_the_survey_migration(self):
        self.assertEqual(
            set(build.RETIRED_FIELDS),
            {"category", "category_path", "subcategory", "foundation", "mechanism_tags", "focus_tags", "domain_tags", "tags"},
        )
        for removed in (
            "VALID_CATEGORIES", "VALID_MECHANISM_TAGS", "VALID_FOCUS_TAGS", "normalize_mechanism_tags",
            "normalize_focus_tags", "merge_mechanism_tags", "split_focus_and_mechanism_tags",
            "split_domain_and_mechanism_tags", "guess_capability_category", "guess_efficiency_category",
        ):
            self.assertFalse(hasattr(build, removed), removed)

    def test_reject_retired_fields_lists_every_retired_field_present(self):
        with self.assertRaises(ValueError) as ctx:
            build.reject_retired_fields({"category": "designs", "tags": ["x"], "survey_section": ["x"]}, "e.yaml")
        message = str(ctx.exception)
        self.assertIn("e.yaml: category, tags no longer exist", message)
        build.reject_retired_fields({"survey_section": ["architecture/topology"]}, "e.yaml")

    def test_adjacent_catalog_fit_is_valid_and_strict_is_the_default(self):
        adjacent = build.normalize_paper_taxonomy_fields({"catalog_fit": "adjacent"}, "paper.yaml")
        strict = build.normalize_paper_taxonomy_fields({}, "paper.yaml")
        self.assertEqual(adjacent, {"catalog_fit": "adjacent"})
        self.assertEqual(strict, {"catalog_fit": "strict"})
        self.assertEqual(
            build.normalize_paper_taxonomy_fields({"catalog_fit": " Adjacent "}, "paper.yaml"),
            {"catalog_fit": "adjacent"},
        )

    def test_unknown_catalog_fit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid catalog_fit"):
            build.normalize_paper_taxonomy_fields({"catalog_fit": "borderline"}, "paper.yaml")

    def test_required_paper_survey_fields_are_enforced(self):
        complete = survey_fields()
        self.assertEqual(
            build.normalize_survey_fields(complete, "paper.yaml", build.REQUIRED_PAPER_SURVEY_FIELDS),
            complete,
        )
        for field in build.REQUIRED_PAPER_SURVEY_FIELDS:
            for broken in ({k: v for k, v in complete.items() if k != field}, {**complete, field: None}):
                with self.subTest(field=field, broken=broken):
                    with self.assertRaisesRegex(ValueError, f"missing required {field}"):
                        build.normalize_survey_fields(broken, "paper.yaml", build.REQUIRED_PAPER_SURVEY_FIELDS)

    def test_required_scalar_axis_cannot_be_blank(self):
        for field in ("loop_topology", "sharing", "depth_control"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, f"missing required {field}"):
                    build.normalize_survey_fields(
                        survey_fields(**{field: ""}), "paper.yaml", build.REQUIRED_PAPER_SURVEY_FIELDS
                    )

    def test_survey_list_fields_are_deduplicated_and_keep_primary_order(self):
        result = build.normalize_survey_fields(
            survey_fields(
                survey_section=["scaling/test-time", "architecture/topology", "scaling/test-time"],
                claims="stability",
                comparison=["iso-flop", "iso-param", "iso-flop"],
            ),
            "paper.yaml",
        )
        self.assertEqual(result["survey_section"], ["scaling/test-time", "architecture/topology"])
        self.assertEqual(result["claims"], ["stability"])
        self.assertEqual(result["comparison"], ["iso-flop", "iso-param"])
        self.assertEqual(build.primary_section(result), "scaling/test-time")
        self.assertIsNone(build.primary_section({}))
        self.assertIsNone(build.primary_section({"survey_section": []}))

    def test_section_label_uses_survey_number_and_title(self):
        self.assertEqual(build.section_label("architecture/topology"), "§4.1 Loop topology")
        self.assertEqual(build.section_label("open-problems/diffusion"), "§10.1 Unification with diffusion models")
        with self.assertRaises(KeyError):
            build.section_label("design/topology")

    def test_count_field_values_counts_scalars_and_lists(self):
        entries = [
            {"survey_section": ["architecture/topology", "scaling/test-time"], "sharing": "full"},
            {"survey_section": ["scaling/test-time"], "sharing": "full"},
            {"sharing": ""},
            {},
        ]
        self.assertEqual(
            build.count_field_values(entries, "survey_section"),
            {"architecture/topology": 1, "scaling/test-time": 2},
        )
        self.assertEqual(build.count_field_values(entries, "sharing"), {"full": 2})

    def test_render_survey_taxonomy_shape(self):
        taxonomy = build.render_survey_taxonomy()
        self.assertEqual(set(taxonomy), {"parts", "chapters", "sections", "axes"})
        self.assertEqual([part["id"] for part in taxonomy["parts"]], [p for p, _ in build.SURVEY_PARTS])
        self.assertEqual(
            [chapter["number"] for chapter in taxonomy["chapters"]],
            ["2", "3", "4", "5", "6", "7", "8", "9", "10"],
        )
        part_ids = {part["id"] for part in taxonomy["parts"]}
        chapter_numbers = {chapter["number"] for chapter in taxonomy["chapters"]}
        for chapter in taxonomy["chapters"]:
            self.assertEqual(set(chapter), {"number", "part", "title"})
            self.assertIn(chapter["part"], part_ids)
        self.assertEqual([section["id"] for section in taxonomy["sections"]], list(build.VALID_SURVEY_SECTIONS))
        for section in taxonomy["sections"]:
            self.assertEqual(set(section), {"id", "number", "chapter", "title"})
            self.assertIn(section["chapter"], chapter_numbers)
            self.assertTrue(section["number"].startswith(section["chapter"] + "."))
        self.assertIn(
            {"id": "architecture/topology", "number": "4.1", "chapter": "4", "title": "Loop topology"},
            taxonomy["sections"],
        )
        self.assertEqual(
            list(taxonomy["axes"]),
            ["loop_topology", "sharing", "depth_control", "claims", "comparison"],
        )
        self.assertEqual(taxonomy["axes"]["sharing"], {"label": "Sharing", "values": list(build.VALID_SHARING_SCHEMES)})
        self.assertEqual(taxonomy["axes"]["claims"]["values"], list(build.VALID_CLAIMS))
        self.assertEqual(taxonomy["axes"]["comparison"]["values"], ["iso-param", "iso-flop", "iso-depth", "unclear"])
        json.dumps(taxonomy)

    def test_optional_date_fields_accept_python_date_objects(self):
        self.assertEqual(
            build.normalize_optional_date_string("2026-04-20", "added_date", "paper.yaml"),
            "2026-04-20",
        )
        import datetime as _dt
        self.assertEqual(
            build.normalize_optional_date_string(_dt.date(2026, 4, 20), "added_date", "paper.yaml"),
            "2026-04-20",
        )

    def test_invalid_optional_date_fields_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "expected YYYY-MM-DD"):
            build.normalize_optional_date_string("2026/04/20", "added_date", "paper.yaml")

    def test_impossible_optional_date_fields_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "expected YYYY-MM-DD"):
            build.normalize_optional_date_string("2026-02-31", "added_date", "paper.yaml")


class DailyBriefingBuildTests(unittest.TestCase):
    def test_load_briefings_reads_year_month_daily_markdown_with_frontmatter(self):
        with TemporaryDirectory() as tmpdir:
            briefings_dir = Path(tmpdir) / "briefings"
            briefing_path = briefings_dir / "2026" / "04" / "2026-04-28.md"
            briefing_path.parent.mkdir(parents=True)
            briefing_path.write_text(
                "---\n"
                "title: Daily Loop-Model Briefing — 2026-04-28\n"
                "date: 2026-04-28\n"
                "status: watchlist\n"
                "run_id: internal_cron_id_that_should_not_be_exported\n"
                "summary: One strong loop-model candidate is ready for readers.\n"
                "highlights:\n"
                "  - Reader-facing takeaway about memory tokens.\n"
                "  - Watchlist keeps near-misses separate.\n"
                "candidates:\n"
                "  - id: '2604.21999'\n"
                "    title: Universal Transformers Need Memory\n"
                "    verdict: strong candidate\n"
                "    url: https://arxiv.org/abs/2604.21999\n"
                "---\n\n"
                "# Daily Loop-Model Briefing — 2026-04-28\n\n"
                "Reader notes live here.\n",
                encoding="utf-8",
            )

            with patch.object(build, "BRIEFINGS_DIR", briefings_dir):
                briefings = build.load_briefings()

        self.assertEqual(len(briefings), 1)
        briefing = briefings[0]
        self.assertEqual(briefing["date"], "2026-04-28")
        self.assertEqual(briefing["title"], "Daily Loop-Model Briefing — 2026-04-28")
        self.assertEqual(briefing["status"], "watchlist")
        self.assertEqual(briefing["source_path"], "briefings/2026/04/2026-04-28.md")
        self.assertIn("Reader notes live here.", briefing["content"])
        self.assertEqual(briefing["highlights"][0], "Reader-facing takeaway about memory tokens.")
        self.assertEqual(briefing["candidates"][0]["id"], "2604.21999")
        self.assertNotIn("run_id", briefing)

    def test_load_briefings_keeps_every_briefing_content_for_internal_consumers(self):
        with TemporaryDirectory() as tmpdir:
            briefings_dir = Path(tmpdir) / "briefings"
            for briefing_date, body in (
                ("2026-04-28", "Latest reader notes."),
                ("2026-04-27", "Earlier reader notes."),
            ):
                briefing_path = (
                    briefings_dir
                    / briefing_date[:4]
                    / briefing_date[5:7]
                    / f"{briefing_date}.md"
                )
                briefing_path.parent.mkdir(parents=True, exist_ok=True)
                briefing_path.write_text(
                    "---\n"
                    f"date: {briefing_date}\n"
                    f"title: Briefing {briefing_date}\n"
                    "---\n\n"
                    f"{body}\n",
                    encoding="utf-8",
                )

            with patch.object(build, "BRIEFINGS_DIR", briefings_dir):
                briefings = build.load_briefings()

        self.assertEqual([briefing["date"] for briefing in briefings], ["2026-04-28", "2026-04-27"])
        self.assertEqual([briefing["content"] for briefing in briefings], ["Latest reader notes.", "Earlier reader notes."])

    def test_build_json_splits_papers_into_bounded_versioned_chunks(self):
        with TemporaryDirectory() as tmpdir:
            json_out = Path(tmpdir) / "papers.json"
            stale = Path(tmpdir) / "catalog" / "papers-009.json"
            stale.parent.mkdir()
            stale.write_text('{"papers":[]}', encoding="utf-8")
            papers = [{"id": f"2604.{index:05d}", "title": f"Paper {index}"} for index in range(5)]
            with patch.object(build, "JSON_OUT", json_out), patch.object(build, "PAPER_CHUNK_SIZE", 2):
                build.build_json(papers, [], [])
            payload = json.loads(json_out.read_text(encoding="utf-8"))
            chunk_files = sorted(path.name for path in (Path(tmpdir) / "catalog").iterdir())
            raw_chunks = [
                (Path(tmpdir) / row["path"]).read_text(encoding="utf-8") for row in payload["paper_chunks"]
            ]

        self.assertEqual(
            [(row["path"], row["count"]) for row in payload["paper_chunks"]],
            [("catalog/papers-000.json", 2), ("catalog/papers-001.json", 2), ("catalog/papers-002.json", 1)],
        )
        self.assertEqual(chunk_files, ["papers-000.json", "papers-001.json", "papers-002.json"])
        self.assertEqual(
            [paper["id"] for raw in raw_chunks for paper in json.loads(raw)["papers"]],
            [paper["id"] for paper in papers],
        )
        for row, raw in zip(payload["paper_chunks"], raw_chunks):
            self.assertEqual(row["version"], hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12])

    def test_index_fetches_manifest_then_every_listed_chunk(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('return fetch("papers.json")', html)
        self.assertIn("Promise.all(chunks.map(fetchPaperChunk))", html)
        self.assertIn("const PAPER_CHUNK_PATH_PATTERN = /^catalog\\/papers-\\d{3}\\.json$/;", html)
        self.assertIn("papers.length !== chunk.count", html)
        self.assertIn("loadCatalog()\n  .then(function(data) { buildDOM(data); })", html)

    def test_serialize_browser_entry_drops_redundant_copies(self):
        entry = {
            "id": "2604.21999",
            "entry_type": "paper",
            "title": "A paper",
            "authors": "A. Author, B. Author",
            "authors_list": ["A. Author", "B. Author"],
            "links": {
                "arxiv": "https://arxiv.org/abs/2604.21999",
                "alphaxiv": "https://www.alphaxiv.org/abs/2604.21999",
                "github": "https://github.com/example/repo",
            },
            "community_comments": [{"label": "Review", "url": "https://example.com/review"}],
            "comments": [{"label": "Review", "url": "https://example.com/review"}],
        }

        browser_entry = build.serialize_browser_entry(entry)

        self.assertNotIn("entry_type", browser_entry)
        self.assertNotIn("authors", browser_entry)
        self.assertNotIn("comments", browser_entry)
        self.assertEqual(browser_entry["authors_list"], ["A. Author", "B. Author"])
        self.assertEqual(browser_entry["community_comments"], entry["community_comments"])
        self.assertEqual(
            browser_entry["links"],
            {"arxiv": "https://arxiv.org/abs/2604.21999", "github": "https://github.com/example/repo"},
        )
        self.assertIn("alphaxiv", entry["links"])
        self.assertEqual(build.serialize_browser_entry({"entry_type": "blog"}), {"entry_type": "blog"})

    def test_serialize_browser_entry_keeps_survey_fields_and_drops_retired_fields(self):
        entry = {
            "id": "2604.21999",
            "entry_type": "paper",
            "title": "A paper",
            **survey_fields(),
            "survey_core": False,
            "category": "designs",
            "category_path": ["x"],
            "subcategory": "x",
            "foundation": True,
            "mechanism_tags": ["flat-loop"],
            "focus_tags": ["architecture"],
            "domain_tags": ["reasoning"],
            "tags": ["LoopLM"],
            "family_tags": ["ut"],
        }
        browser_entry = build.serialize_browser_entry(entry)
        for field in build.SURVEY_FIELDS:
            self.assertEqual(browser_entry[field], entry[field])
        for field in (*build.RETIRED_FIELDS, "family_tags"):
            self.assertNotIn(field, browser_entry)

    def test_compact_browser_links_keeps_alphaxiv_it_cannot_rebuild_exactly(self):
        arxiv = "https://arxiv.org/abs/2604.21999"
        cases = [
            {"arxiv": arxiv, "alphaxiv": "https://www.alphaxiv.org/abs/2604.00001"},
            {"arxiv": arxiv, "github": "https://github.com/x/y", "alphaxiv": "https://www.alphaxiv.org/abs/2604.21999"},
            {"alphaxiv": "https://www.alphaxiv.org/abs/2604.21999"},
            {"arxiv": "https://www.alphaxiv.org/abs/2604.21999", "alphaxiv": "https://www.alphaxiv.org/abs/2604.21999"},
        ]
        for links in cases:
            with self.subTest(links=links):
                self.assertEqual(build.compact_browser_links(links), links)

    def test_index_restores_links_dropped_from_browser_payload(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("function restoreDerivedLinks(links) {", html)
        self.assertIn("paper.links = restoreDerivedLinks(paper.links);", html)
        self.assertIn("arxiv\\.org\\/(?:abs|pdf)\\/(\\d{4}\\.\\d{4,5})(?:v\\d+)?", html)
        self.assertEqual(
            build.BROWSER_ARXIV_LINK_RE.pattern,
            r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?",
        )

    def test_build_json_trims_briefings_for_browser_without_changing_catalog_entries(self):
        with TemporaryDirectory() as tmpdir:
            json_out = Path(tmpdir) / "papers.json"
            papers = [
                {
                    "id": "2604.21999",
                    "entry_type": "paper",
                    "title": "A paper",
                    "authors": "A. Author",
                    "authors_list": ["A. Author"],
                    "venue": "ICML",
                    "venueClass": "venue-icml",
                    "peer_reviewed": True,
                    "venue_source": "https://proceedings.mlr.press/v267/schone25a.html",
                    "year": 2026,
                    "published_date": "2026-04-28",
                    "added_date": "2026-04-28",
                    "desc": "A reader-facing summary.",
                    "links": {"arxiv": "https://arxiv.org/abs/2604.21999"},
                    "catalog_fit": "adjacent",
                    "survey_section": ["architecture/topology", "scaling/test-time"],
                    "loop_topology": "prelude-core-coda",
                    "sharing": "full",
                    "depth_control": "sampled-train",
                    "claims": ["test-time-scaling"],
                    "comparison": [],
                    "survey_core": True,
                    "must_read": True,
                    "citations": 12,
                    "github_stars": 34,
                    "community_comments": [{"label": "Review", "url": "https://example.com/review"}],
                    "comments": [{"label": "Review", "url": "https://example.com/review"}],
                    "source_file": "2604.21999.yaml",
                    "source_path": "papers/2604.21999.yaml",
                    "citation_source_best": "semantic_scholar",
                    "citation_sources": {"semantic_scholar": 12},
                    "star_source_best": "github",
                    "star_sources": {"github": 34},
                    "metrics_updated": "2026-04-28T00:00:00Z",
                }
            ]
            blogs = [
                {
                    "id": "blog-1",
                    "entry_type": "blog",
                    "title": "A blog",
                    "authors": "B. Author",
                    "authors_list": ["B. Author"],
                    "published_date": "2026-04-27",
                    "desc": "A blog summary.",
                    "links": {"blog": "https://example.com/blog"},
                    "survey_section": ["understanding/why"],
                    "source_file": "blog-1.yaml",
                    "source_path": "blogs/blog-1.yaml",
                    "citation_sources": {"internal": 1},
                    "metrics_updated": "2026-04-28T00:00:00Z",
                }
            ]
            papers_before = json.loads(json.dumps(papers))
            blogs_before = json.loads(json.dumps(blogs))
            briefings = [
                {
                    "date": "2026-04-27",
                    "title": "Yesterday",
                    "status": "ok",
                    "summary": "Earlier summary.",
                    "highlights": ["Earlier highlight."],
                    "candidates": [],
                    "content": "Earlier full Markdown body.",
                    "source_path": "briefings/2026/04/2026-04-27.md",
                },
                {
                    "date": "2026-04-28",
                    "title": "Today",
                    "status": "watchlist",
                    "summary": "Latest summary.",
                    "highlights": ["Latest highlight."],
                    "candidates": [
                        {
                            "id": "2604.21999",
                            "title": "A paper",
                            "verdict": "strong candidate",
                            "url": "https://arxiv.org/abs/2604.21999",
                            "internal": "sentinel",
                        }
                    ],
                    "content": "Latest full Markdown body.",
                    "source_path": "briefings/2026/04/2026-04-28.md",
                },
            ]
            with patch.object(build, "JSON_OUT", json_out):
                build.build_json(papers, blogs, briefings)
            raw_payload = json_out.read_text(encoding="utf-8")
            payload = json.loads(raw_payload)
            briefing_page_raw = (json_out.parent / "briefing-latest.json").read_text(encoding="utf-8")
            chunk_papers = [
                paper
                for row in payload["paper_chunks"]
                for paper in json.loads((json_out.parent / row["path"]).read_text(encoding="utf-8"))["papers"]
            ]

        self.assertNotIn("papers", payload)
        browser_fields = (
            "id", "entry_type", "title", "authors_list", "venue", "venueClass",
            "peer_reviewed", "venue_source",
            "year", "published_date", "added_date", "desc", "links", "catalog_fit",
            "survey_section", "loop_topology", "sharing", "depth_control", "claims", "comparison",
            "survey_core", "must_read", "citations", "github_stars", "community_comments",
        )
        expected_paper = {
            field: papers_before[0][field]
            for field in browser_fields
            if field in papers_before[0] and field != "entry_type"
        }
        self.assertEqual(chunk_papers, [expected_paper])
        self.assertEqual(
            payload["blogs"],
            [{field: blogs_before[0][field] for field in browser_fields if field in blogs_before[0]}],
        )
        self.assertEqual(papers, papers_before)
        self.assertEqual(blogs, blogs_before)
        for entry in [*chunk_papers, *payload["blogs"]]:
            for field in (
                "source_file", "source_path", "citation_source_best", "citation_sources",
                "star_source_best", "star_sources", "metrics_updated",
            ):
                self.assertNotIn(field, entry)
        self.assertEqual(raw_payload, json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        self.assertEqual(payload["meta"]["briefing_total"], 2)
        self.assertEqual(payload["meta"]["latest_briefing_date"], "2026-04-28")
        self.assertEqual(payload["meta"]["briefing_section_title"], "Daily Briefing")
        self.assertEqual(payload["meta"]["taxonomy_note"], build.TAXONOMY_NOTE)
        self.assertIn("topic map", payload["meta"]["taxonomy_note"])
        self.assertNotIn("survey", payload["meta"]["taxonomy_note"].lower())
        self.assertEqual(payload["survey_taxonomy"], build.render_survey_taxonomy())
        self.assertEqual(
            set(payload),
            {"meta", "survey_taxonomy", "paper_chunks", "blogs", "briefings"},
        )
        for retired in build.RETIRED_FIELDS:
            self.assertNotIn(f'"{retired}"', raw_payload)
        self.assertEqual(build.CATALOG_TIME_ZONE.key, "America/New_York")
        self.assertEqual(
            payload["meta"]["generated_local_date"],
            datetime.fromisoformat(payload["meta"]["generated"])
            .astimezone(ZoneInfo("America/New_York"))
            .date()
            .isoformat(),
        )
        self.assertEqual(
            payload["briefings"],
            [
                {
                    "date": "2026-04-28",
                    "title": "Today",
                    "status": "watchlist",
                    "summary": "Latest summary.",
                    "highlights": ["Latest highlight."],
                    "candidates": [
                        {
                            "id": "2604.21999",
                            "title": "A paper",
                            "verdict": "strong candidate",
                            "url": "https://arxiv.org/abs/2604.21999",
                        }
                    ],
                    "source_path": "briefings/2026/04/2026-04-28.md",
                }
            ],
        )
        self.assertNotIn("content", payload["briefings"][0])
        self.assertNotIn("internal", payload["briefings"][0]["candidates"][0])

        # The newest briefing's full body lives only in briefing-latest.json.
        briefing_page = json.loads(briefing_page_raw)
        self.assertEqual(list(briefing_page), list(build.BRIEFING_PAGE_FIELDS))
        self.assertEqual(briefing_page, {
            "date": "2026-04-28",
            "title": "Today",
            "status": "watchlist",
            "summary": "Latest summary.",
            "highlights": ["Latest highlight."],
            "candidates": [{
                "id": "2604.21999",
                "title": "A paper",
                "verdict": "strong candidate",
                "url": "https://arxiv.org/abs/2604.21999",
            }],
            "source_path": "briefings/2026/04/2026-04-28.md",
            "body_markdown": "Latest full Markdown body.",
        })
        self.assertEqual(briefing_page_raw, json.dumps(briefing_page, ensure_ascii=False, indent=2) + "\n")
        self.assertEqual(
            payload["meta"]["latest_briefing_version"],
            hashlib.sha256(briefing_page_raw.encode("utf-8")).hexdigest()[:12],
        )
        self.assertNotIn("Latest full Markdown body.", raw_payload)

    def test_latest_briefing_page_is_rewritten_only_when_its_content_changes(self):
        briefing = {
            "date": "2026-04-28", "title": "Today", "status": "added", "summary": "Summary.",
            "highlights": [], "candidates": [], "content": "## Added\n\nBody.",
            "source_path": "briefings/2026/04/2026-04-28.md",
        }
        with TemporaryDirectory() as tmpdir:
            json_out = Path(tmpdir) / "papers.json"
            page_path = Path(tmpdir) / "briefing-latest.json"
            with patch.object(build, "JSON_OUT", json_out):
                first_version = build.write_latest_briefing([briefing])
                first_text = page_path.read_text(encoding="utf-8")
                with patch.object(Path, "write_text") as write_text:
                    second_version = build.write_latest_briefing([briefing])
                write_text.assert_not_called()
                changed_version = build.write_latest_briefing([{**briefing, "content": "## Added\n\nNew body."}])
                changed_text = page_path.read_text(encoding="utf-8")

        self.assertEqual(first_version, second_version)
        self.assertNotEqual(first_version, changed_version)
        self.assertTrue(first_text.endswith("}\n"))
        self.assertIn('"body_markdown": "## Added\\n\\nNew body."', changed_text)

    def test_latest_briefing_page_without_briefings_keeps_every_key_empty(self):
        page = build.render_latest_briefing_page([])
        self.assertEqual(list(page), list(build.BRIEFING_PAGE_FIELDS))
        self.assertEqual(page, {
            "date": None, "title": None, "status": None, "summary": "", "highlights": [],
            "candidates": [], "source_path": None, "body_markdown": "",
        })

    def test_repo_latest_briefing_page_matches_the_newest_briefing_file(self):
        briefings = build.load_briefings()
        page = json.loads((REPO_ROOT / "briefing-latest.json").read_text(encoding="utf-8"))
        newest = max(briefings, key=lambda item: item["date"])
        self.assertEqual(page["date"], newest["date"])
        self.assertEqual(page["source_path"], newest["source_path"])
        source = (REPO_ROOT / newest["source_path"]).read_text(encoding="utf-8")
        self.assertTrue(source.rstrip().endswith(page["body_markdown"]))
        self.assertFalse(page["body_markdown"].startswith("---"))

    def test_serialize_browser_briefings_copies_nested_ui_fields(self):
        briefings = [
            {
                "date": "2026-04-28",
                "highlights": ["Original highlight."],
                "candidates": [
                    {
                        "id": "2604.21999",
                        "title": "Original title",
                        "verdict": "strong candidate",
                        "url": "https://arxiv.org/abs/2604.21999",
                        "internal": "sentinel",
                    }
                ],
            }
        ]

        browser_briefings = build.serialize_browser_briefings(briefings)

        self.assertIsNot(browser_briefings[0]["highlights"], briefings[0]["highlights"])
        self.assertIsNot(browser_briefings[0]["candidates"], briefings[0]["candidates"])
        self.assertIsNot(browser_briefings[0]["candidates"][0], briefings[0]["candidates"][0])
        self.assertNotIn("internal", browser_briefings[0]["candidates"][0])

        browser_briefings[0]["highlights"].append("Browser-only highlight.")
        browser_briefings[0]["candidates"][0]["title"] = "Browser-only title"
        self.assertEqual(briefings[0]["highlights"], ["Original highlight."])
        self.assertEqual(briefings[0]["candidates"][0]["title"], "Original title")

    def test_repo_briefings_use_year_month_daily_paths(self):
        paths = sorted(path for path in BRIEFINGS_DIR.glob("*/*/*.md") if not path.name.startswith("_"))
        self.assertIn(BRIEFINGS_DIR / "2026" / "04" / "2026-04-28.md", paths)
        for path in paths:
            with self.subTest(path=path):
                self.assertRegex(path.name, r"^\d{4}-\d{2}-\d{2}\.md$")
                self.assertEqual(path.parent.name, path.stem[5:7])
                self.assertEqual(path.parent.parent.name, path.stem[:4])


class TagFilterUiTests(unittest.TestCase):
    @staticmethod
    def run_stats_series_helpers(expression: str):
        """Evaluate the pure paper-statistics helpers from index.html in Node."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        helper_start = html.index("function parseIsoDate(value) {")
        helper_end = html.index("function createStatsSvgElement(", helper_start)
        tick_start = html.index("function selectTimelineTickIndices(", helper_end)
        tick_end = html.index("function renderReleasePulseChart(", tick_start)
        helpers = html[helper_start:helper_end] + html[tick_start:tick_end]
        script = f"""
{helpers}
const result = {expression};
process.stdout.write(JSON.stringify(result));
"""
        output = subprocess.check_output(["node", "-e", script], text=True)
        return json.loads(output)

    @staticmethod
    def run_top_level_tab_block(initial_hash: str, test_body: str):
        """Evaluate the production tab, survey-taxonomy and filter-routing code in Node.

        The real survey vocabulary from ``build.render_survey_taxonomy()`` is loaded
        before ``test_body`` runs; rendering and stats entry points are stubbed.
        """
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")

        def between(start_marker: str, end_marker: str, include_end: bool = False) -> str:
            start = html.index(start_marker)
            end = html.index(end_marker, start)
            return html[start:end + (len(end_marker) if include_end else 0)]

        production_block = "\n".join((
            between("function escapeHtml(str) {", "function getPaperVenueLabel("),
            between("const CATALOG_ADJACENT_NOTE = ", "\n", include_end=True),
            between("const AXIS_CHIP_PREFIXES = {", "/** Mark core references"),
            between("let CURRENT_SORT = 'date';", "let CURRENT_VIEW = 'list';", include_end=True),
            between("function normalizeTopLevelTab(tab) {", "initResearchPrompt();"),
            between("function setSurveyTaxonomy(taxonomy) {", "function setFacetFilterOpen(isOpen) {"),
            between("function toggleFacetFilter(group, value) {", "function updateFacetFilterUI() {"),
            between("function normalizeDateInputValue(raw) {", "function getFilterSidebarActiveCount() {"),
            between("function rerenderCurrentResults() {", "function setToggleButtonState("),
            between("function buildPrimaryChapterCounts(papers) {", "function syncSurveyNavCounts("),
            between("function syncSearchQueryToUrl(query) {", "function initPublicationDateFilter() {"),
            between("function shouldHandleFacetLinkClick(event) {", "function initFacetLinkInteractions() {"),
        ))
        taxonomy = json.dumps(build.render_survey_taxonomy())
        script = f"""
let browserHash = {json.dumps(initial_hash)};
let focusedTabId = null;
const hashWrites = [];
const renderStatsCalls = [];
const scrollRequests = [];
const activatedNavTargets = [];
const animationFrameCallbacks = [];
const windowListeners = {{}};
const replaceStateCalls = [];
const pushStateCalls = [];
const searchInput = {{
  value: '',
  placeholder: 'Search papers, authors, keywords…',
  attributes: {{}},
  listeners: {{}},
  setAttribute: function(name, value) {{
    this.attributes[name] = String(value);
    if (name === 'placeholder') this.placeholder = String(value);
  }},
  addEventListener: function(name, listener) {{
    if (!this.listeners[name]) this.listeners[name] = [];
    this.listeners[name].push(listener);
  }},
  focus: function() {{
    document.activeElement = this;
  }}
}};
function makeStaticElement(hidden) {{
  return {{
    hidden: Boolean(hidden),
    textContent: '',
    innerHTML: '',
    attributes: {{}},
    listeners: {{}},
    setAttribute: function(name, value) {{ this.attributes[name] = String(value); }},
    addEventListener: function(name, listener) {{
      if (!this.listeners[name]) this.listeners[name] = [];
      this.listeners[name].push(listener);
    }}
  }};
}}
const publicationDateStart = makeStaticElement(false);
publicationDateStart.value = '';
const publicationDateEnd = makeStaticElement(false);
publicationDateEnd.value = '';
const sectionFilter = makeStaticElement(false);
sectionFilter.value = '';
const facetFilterGroups = makeStaticElement(false);
const searchCalls = [];
let facetUiUpdates = 0;
let quickFilterUiUpdates = 0;

function makeTab(id, selected, tabIndex) {{
  return {{
    id: id,
    tabIndex: tabIndex,
    attributes: {{ 'aria-selected': selected ? 'true' : 'false' }},
    listeners: {{}},
    classList: {{
      active: selected,
      toggle: function(name, enabled) {{
        if (name === 'active') this.active = Boolean(enabled);
      }}
    }},
    setAttribute: function(name, value) {{ this.attributes[name] = value; }},
    addEventListener: function(name, listener) {{
      if (!this.listeners[name]) this.listeners[name] = [];
      this.listeners[name].push(listener);
    }},
    focus: function() {{ focusedTabId = this.id; }}
  }};
}}

const tabs = [
  makeTab('papers-tab', true, 0),
  makeTab('briefing-tab', false, -1),
  makeTab('stats-tab', false, -1),
  makeTab('blogs-tab', false, -1)
];
const [papersTab, briefingTab, statsTab, blogsTab] = tabs;
const papersPanel = makeStaticElement(false);
const statsPanel = makeStaticElement(true);
const briefingPanel = makeStaticElement(true);
const briefingLoads = [];
const catalogHeading = makeStaticElement(false);
const bodyClasses = {{}};
const elements = {{
  'papers-tab': papersTab,
  'briefing-tab': briefingTab,
  'stats-tab': statsTab,
  'blogs-tab': blogsTab,
  'papers-panel': papersPanel,
  'stats-panel': statsPanel,
  'briefing-panel': briefingPanel,
  'catalog-heading': catalogHeading,
  'search': searchInput,
  'publication-date-start': publicationDateStart,
  'publication-date-end': publicationDateEnd,
  'section-filter': sectionFilter,
  'facet-filter-groups': facetFilterGroups
}};
const document = {{
  activeElement: null,
  body: {{
    classList: {{
      toggle: function(name, enabled) {{ bodyClasses[name] = Boolean(enabled); }}
    }}
  }},
  querySelectorAll: function(selector) {{
    return selector === '.top-level-tab[role="tab"]' ? tabs : [];
  }},
  getElementById: function(id) {{ return elements[id] || null; }}
}};
function recordUrl(calls, url) {{
  const nextUrl = new URL(String(url), window.location.href);
  calls.push({{ search: nextUrl.search, hash: nextUrl.hash }});
  window.location.href = nextUrl.href;
  window.location.search = nextUrl.search;
  browserHash = nextUrl.hash;
}}
const window = {{
  location: {{
    href: 'https://example.test/index.html' + {json.dumps(initial_hash)},
    search: ''
  }},
  history: {{
    state: null,
    replaceState: function(state, title, url) {{ recordUrl(replaceStateCalls, url); }},
    pushState: function(state, title, url) {{ recordUrl(pushStateCalls, url); }}
  }},
  addEventListener: function(name, listener) {{
    if (!windowListeners[name]) windowListeners[name] = [];
    windowListeners[name].push(listener);
  }},
  requestAnimationFrame: function(callback) {{ animationFrameCallbacks.push(callback); }}
}};
Object.defineProperty(window.location, 'hash', {{
  get: function() {{ return browserHash; }},
  set: function(value) {{
    hashWrites.push(value);
    browserHash = value;
  }}
}});
function setBrowserHash(value) {{ browserHash = value; }}
function dispatchWindowEvent(name) {{
  (windowListeners[name] || []).forEach(function(listener) {{ listener(); }});
}}
function flushAnimationFrames() {{
  while (animationFrameCallbacks.length) animationFrameCallbacks.shift()();
}}
function renderStatsPanel() {{
  renderStatsCalls.push({{ ready: CATALOG_DATA_READY, error: CATALOG_DATA_ERROR }});
}}
function loadBriefingPage() {{ briefingLoads.push(ACTIVE_TOP_LEVEL_TAB); }}
function scrollToSection(sectionId) {{ scrollRequests.push(sectionId); }}
function activateSurveyNavLink(targetId) {{ activatedNavTargets.push(targetId); }}
/** Keep this harness independent of detail-pane and card rendering. */
function syncReadingDeskPanel() {{}}
function renderCard(paper) {{ return '[card ' + paper.id + ']'; }}
/** Preserve view transitions without rendering the catalog in this harness. */
function setView(view) {{ CURRENT_VIEW = view; }}
function updateFacetFilterUI() {{ facetUiUpdates += 1; }}
function updateQuickFilterButtons() {{ quickFilterUiUpdates += 1; }}
function doSearch(query) {{ searchCalls.push(query); }}

{production_block}
setSurveyTaxonomy({taxonomy});
{test_body}
"""
        output = subprocess.check_output(["node", "-e", script], text=True)
        return json.loads(output)

    def test_date_sort_is_default_active_sort(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("let CURRENT_SORT = 'date';", html)
        self.assertIn('<button class="sort-btn" data-sort="default" onclick="setSort(\'default\')">Curated</button>', html)
        self.assertIn('<button class="sort-btn active" data-sort="date" onclick="setSort(\'date\')">&#128197; Date</button>', html)
        self.assertNotIn('<button class="sort-btn active" data-sort="default" onclick="setSort(\'default\')">Curated</button>', html)
        self.assertNotIn('>Default</button>', html)
        self.assertNotIn('>Year</button>', html)

    def test_publication_date_filter_controls_use_date_range_inputs(self):
        """Date range inputs must retain their native type and accessible labels."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("Publication date:", html)
        self.assertIn('<input type="date" id="publication-date-start" class="date-input" placeholder="Start" aria-label="Publication start date" />', html)
        self.assertIn('<input type="date" id="publication-date-end" class="date-input" placeholder="End" aria-label="Publication end date" />', html)
        self.assertIn('<button type="button" id="publication-date-clear" class="date-clear-btn">Clear</button>', html)
        self.assertNotIn("Filter year:", html)
        self.assertNotIn("year-start", html)
        self.assertNotIn("year-end", html)

    def test_publication_date_filter_uses_published_date_range_logic(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("function normalizeDateInputValue(raw) {", html)
        self.assertIn("function getPublicationDateFilter() {", html)
        self.assertIn("function getPaperPublicationDateValue(paper) {", html)
        self.assertIn("function matchPublicationDate(paper, publicationDateFilter) {", html)
        self.assertIn("function initPublicationDateFilter() {", html)
        self.assertIn("paper.published_date", html)
        self.assertIn("matchPublicationDate(paper, publicationDateFilter)", html)
        self.assertNotIn("function getYearFilter() {", html)
        self.assertNotIn("function matchYear(paper, yearFilter) {", html)

    def test_frontend_drops_retired_taxonomy_identifiers(self):
        """The browser, submit page and reading desk no longer know categories or free-form tags."""
        sources = {
            "index.html": INDEX_HTML_PATH.read_text(encoding="utf-8"),
            "submit.html": SUBMIT_PAGE_PATH.read_text(encoding="utf-8"),
            "reading-desk.js": READING_DESK_JS_PATH.read_text(encoding="utf-8"),
        }
        retired = (
            "mechanism_tags", "focus_tags", "domain_tags", "family_tags", "category_path", "subcategory",
            "foundation", "TAG_FILTER_LOOKUP", "ACTIVE_TAG_FILTERS", "URL_TAG_FILTER_KEYS",
            "ROUTE_OWNED_TAG_FILTER_KEYS", "TagDrilldown", "tag-filter", "_tagKeySet", "paper-tag",
            "category-filter", "setCategoryFilter", "ACTIVE_CATEGORY_FILTER", "CATEGORIES",
            "searchParams.getAll('tag')", "mechanism::", "focus::", "domain::",
        )
        for name, source in sources.items():
            for identifier in retired:
                with self.subTest(file=name, identifier=identifier):
                    self.assertNotIn(identifier, source)

    def test_index_uses_survey_section_and_design_axis_url_params(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "const FACET_GROUPS = ['loop_topology', 'sharing', 'depth_control', 'claims', 'comparison'];",
            html,
        )
        params_start = html.index("function buildFilterSearchParams(sectionFilter, facetFilters, query) {")
        params_source = html[params_start:html.index("function cloneFacetFilters() {", params_start)]
        self.assertIn("params.set('q', query);", params_source)
        self.assertIn("params.set('section', sectionFilter);", params_source)
        self.assertIn("params.append(group, value);", params_source)
        read_start = html.index("function readFiltersFromUrl() {")
        read_source = html[read_start:html.index("function syncFiltersToUrl(mode) {", read_start)]
        self.assertIn("params.get('section')", read_source)
        self.assertIn("params.getAll(group)", read_source)
        self.assertIn("params.get('q')", read_source)
        self.assertIn('id="section-filter"', html)
        self.assertIn('id="facet-filter-toggle"', html)
        self.assertIn('id="facet-filter-panel"', html)
        self.assertIn('id="facet-filter-groups"', html)
        self.assertIn('id="facet-filter-summary"', html)
        self.assertIn("setSurveyTaxonomy(data.survey_taxonomy);", html)

    def test_facet_url_state_is_validated_against_the_survey_vocabulary(self):
        result = self.run_top_level_tab_block("#papers", """
function read(search) {
  window.location.search = search;
  const state = readFiltersFromUrl();
  const facets = {};
  Object.keys(state.facets).sort().forEach(function(group) { facets[group] = Array.from(state.facets[group]); });
  return { section: state.section, facets: facets, query: state.query };
}
process.stdout.write(JSON.stringify({
  full: read('?section=architecture%2Ftopology&loop_topology=partial&loop_topology=flat&claims=stability&claims=expressivity&q=Norm'),
  chapter: read('?section=4&sharing=full&sharing=tied'),
  unknownSection: read('?section=design%2Ftopology&depth_control=adaptive-halting'),
  retiredParams: read('?tag=mechanism%3A%3Aflat-loop&category=designs&mechanism_tags=flat-loop'),
  empty: read('')
}));
""")
        self.assertEqual(
            result,
            {
                "full": {
                    "section": "architecture/topology",
                    "facets": {"claims": ["stability", "expressivity"], "loop_topology": ["partial"]},
                    "query": "Norm",
                },
                "chapter": {"section": "4", "facets": {"sharing": ["full"]}, "query": ""},
                "unknownSection": {"section": "", "facets": {"depth_control": ["adaptive-halting"]}, "query": ""},
                "retiredParams": {"section": "", "facets": {}, "query": ""},
                "empty": {"section": "", "facets": {}, "query": ""},
            },
        )

    def test_facet_links_are_cumulative_and_serialized_in_vocabulary_order(self):
        result = self.run_top_level_tab_block("#papers", """
window.location.search = '?q=norm';
ACTIVE_SECTION_FILTER = '4';
ACTIVE_FACET_FILTERS = { claims: new Set(['stability']), sharing: new Set(['full']) };
const result = {
  addClaim: getFacetDrilldownHref('claims', 'param-efficiency'),
  replaceSection: getFacetDrilldownHref('section', 'scaling/test-time'),
  liveState: { section: ACTIVE_SECTION_FILTER, claims: Array.from(ACTIVE_FACET_FILTERS.claims) },
  statsAxisRow: getFacetOnlyHref('depth_control', 'convergence'),
  statsSectionRow: getFacetOnlyHref('section', 'architecture/topology')
};
ACTIVE_TOP_LEVEL_TAB = 'blogs';
result.blogsSection = getFacetDrilldownHref('section', 'understanding/why');
process.stdout.write(JSON.stringify(result));
""")
        self.assertEqual(
            result,
            {
                "addClaim": "?q=norm&section=4&sharing=full&claims=param-efficiency&claims=stability#papers",
                "replaceSection": "?q=norm&section=scaling%2Ftest-time&sharing=full&claims=stability#papers",
                "liveState": {"section": "4", "claims": ["stability"]},
                "statsAxisRow": "?depth_control=convergence#papers",
                "statsSectionRow": "?section=architecture%2Ftopology#papers",
                "blogsSection": "?q=norm&section=understanding%2Fwhy&sharing=full&claims=stability#blogs",
            },
        )

    def test_facet_link_navigation_pushes_history_and_back_restores_filters(self):
        result = self.run_top_level_tab_block("#papers", """
CATALOG_DATA_READY = true;
function link(href, reset) {
  return { getAttribute: function() { return href; }, dataset: reset ? { facetReset: 'true' } : {} };
}
navigateToFacetLink(link(getFacetDrilldownHref('sharing', 'full')));
navigateToFacetLink(link(getFacetDrilldownHref('claims', 'stability')));
const entered = {
  facets: { sharing: Array.from(ACTIVE_FACET_FILTERS.sharing), claims: Array.from(ACTIVE_FACET_FILTERS.claims) },
  pushes: pushStateCalls.slice()
};
window.location.search = '?sharing=full';
dispatchWindowEvent('popstate');
const back = { groups: Object.keys(ACTIVE_FACET_FILTERS), searches: searchCalls.slice() };

setBrowserHash('#stats');
dispatchWindowEvent('hashchange');
ACCEPTED_ONLY = true;
HAS_CODE_ONLY = true;
publicationDateStart.value = '2025-01-01';
CURRENT_VIEW = 'table';
navigateToFacetLink(link(getFacetOnlyHref('section', '4'), true));
process.stdout.write(JSON.stringify({
  entered: entered,
  back: back,
  reset: {
    active: ACTIVE_TOP_LEVEL_TAB,
    section: ACTIVE_SECTION_FILTER,
    groups: Object.keys(ACTIVE_FACET_FILTERS),
    accepted: ACCEPTED_ONLY,
    hasCode: HAS_CODE_ONLY,
    startDate: publicationDateStart.value,
    view: CURRENT_VIEW,
    sectionSelect: sectionFilter.value,
    lastPush: pushStateCalls.at(-1)
  }
}));
""")
        self.assertEqual(
            result["entered"],
            {
                "facets": {"sharing": ["full"], "claims": ["stability"]},
                "pushes": [
                    {"search": "?sharing=full", "hash": "#papers"},
                    {"search": "?sharing=full&claims=stability", "hash": "#papers"},
                ],
            },
        )
        self.assertEqual(result["back"], {"groups": ["sharing"], "searches": ["", "", ""]})
        self.assertEqual(
            result["reset"],
            {
                "active": "papers",
                "section": "4",
                "groups": [],
                "accepted": False,
                "hasCode": False,
                "startDate": "",
                "view": "list",
                "sectionSelect": "4",
                "lastPush": {"search": "?section=4", "hash": "#papers"},
            },
        )

    def test_panel_filter_edits_replace_history_and_keep_query(self):
        result = self.run_top_level_tab_block("#papers", """
CATALOG_DATA_READY = true;
window.location.href = 'https://example.test/index.html?q=LayerNorm#papers';
window.location.search = '?q=LayerNorm';
toggleFacetFilter('loop_topology', 'partial');
toggleFacetFilter('claims', 'stability');
toggleFacetFilter('claims', 'not-a-claim');
toggleFacetFilter('tags', 'flat-loop');
setSectionFilter('architecture/topology');
setSectionFilter('design/topology');
setSectionFilter('9');
toggleFacetFilter('loop_topology', 'partial');
process.stdout.write(JSON.stringify({
  replaces: replaceStateCalls,
  pushes: pushStateCalls.length,
  section: ACTIVE_SECTION_FILTER,
  groups: Object.keys(ACTIVE_FACET_FILTERS),
  searches: searchCalls
}));
""")
        self.assertEqual(
            result["replaces"],
            [
                {"search": "?q=LayerNorm&loop_topology=partial", "hash": "#papers"},
                {"search": "?q=LayerNorm&loop_topology=partial&claims=stability", "hash": "#papers"},
                {"search": "?q=LayerNorm&section=architecture%2Ftopology&loop_topology=partial&claims=stability", "hash": "#papers"},
                {"search": "?q=LayerNorm&loop_topology=partial&claims=stability", "hash": "#papers"},
                {"search": "?q=LayerNorm&section=9&loop_topology=partial&claims=stability", "hash": "#papers"},
                {"search": "?q=LayerNorm&section=9&claims=stability", "hash": "#papers"},
            ],
        )
        self.assertEqual(result["pushes"], 0)
        self.assertEqual(result["section"], "9")
        self.assertEqual(result["groups"], ["claims"])
        self.assertEqual(len(result["searches"]), 6)

    def test_prepared_records_index_sections_chapters_and_axes(self):
        result = self.run_top_level_tab_block("#papers", """
const paper = preparePaperRecord({
  id: 'p1', title: 'Looped', authors_list: ['A. Author'],
  survey_section: ['architecture/topology', 'design/topology', 'scaling/test-time', 'architecture/topology'],
  loop_topology: 'prelude-core-coda', sharing: 'unspecified', depth_control: 'bogus',
  claims: ['stability', 'speed', 'stability'], comparison: [], survey_core: true,
  links: { arxiv: 'https://arxiv.org/abs/2604.21999' }
});
const blog = preparePaperRecord({
  id: 'b1', entry_type: 'blog', title: 'Post', survey_section: ['understanding/why'], sharing: 'full'
});
const unplaced = preparePaperRecord({ id: 'p2', title: 'Unplaced', survey_section: ['design/topology'] });
process.stdout.write(JSON.stringify({
  sections: paper._sections,
  chapters: Array.from(paper._chapterSet).sort(),
  primary: [paper._primarySection, paper._primaryChapter, paper._sectionLabel],
  axes: paper._axisEntries,
  visibleAxes: getVisibleAxisEntries(paper).map(function(entry) { return entry.group + '=' + entry.value; }),
  links: Object.keys(paper.links),
  search: ['§4.1 loop topology', 'prelude-core-coda', 'core reference'].map(function(text) { return paper._searchText.includes(text); }),
  blog: { type: blog.entry_type, axes: blog._axisEntries, primary: blog._primarySection },
  unplaced: { sections: unplaced._sections, primary: unplaced._primarySection, label: unplaced._sectionLabel }
}));
""")
        self.assertEqual(result["sections"], ["architecture/topology", "scaling/test-time"])
        self.assertEqual(result["chapters"], ["4", "6"])
        self.assertEqual(result["primary"], ["architecture/topology", "4", "§4.1 Loop topology"])
        self.assertEqual(
            result["axes"],
            [
                {"group": "loop_topology", "value": "prelude-core-coda"},
                {"group": "sharing", "value": "unspecified"},
                {"group": "claims", "value": "stability"},
            ],
        )
        self.assertEqual(result["visibleAxes"], ["loop_topology=prelude-core-coda", "claims=stability"])
        self.assertEqual(result["links"], ["arxiv", "alphaxiv"])
        self.assertEqual(result["search"], [True, True, True])
        self.assertEqual(result["blog"], {"type": "blog", "axes": [], "primary": "understanding/why"})
        self.assertEqual(result["unplaced"], {"sections": [], "primary": "", "label": ""})

    def test_section_and_axis_filters_match_any_placement_and_combine_axes(self):
        result = self.run_top_level_tab_block("#papers", """
ALL_PAPERS = [
  { id: 'a', survey_section: ['architecture/topology'], loop_topology: 'partial', sharing: 'full', claims: ['stability'] },
  { id: 'b', survey_section: ['scaling/test-time', 'architecture/depth-control'], loop_topology: 'whole-stack', sharing: 'full', claims: ['test-time-scaling'] },
  { id: 'c', survey_section: ['understanding/why'], loop_topology: 'partial', sharing: 'partial-adapter', claims: [] }
].map(preparePaperRecord);
ALL_BLOGS = [
  { id: 'blog', entry_type: 'blog', survey_section: ['architecture/hybrid'] }
].map(preparePaperRecord);
const noDates = { active: false };
function ids(section, facets, tab) {
  ACTIVE_TOP_LEVEL_TAB = tab || 'papers';
  ACTIVE_SECTION_FILTER = section;
  ACTIVE_FACET_FILTERS = {};
  Object.keys(facets).forEach(function(group) { ACTIVE_FACET_FILTERS[group] = new Set(facets[group]); });
  return getFilteredPapers('', noDates).map(function(paper) { return paper.id; });
}
process.stdout.write(JSON.stringify({
  chapter4: ids('4', {}),
  secondarySection: ids('architecture/depth-control', {}),
  orWithinAxis: ids('', { loop_topology: ['partial', 'whole-stack'] }),
  andAcrossAxes: ids('', { loop_topology: ['partial'], sharing: ['full'] }),
  sectionAndAxis: ids('4', { sharing: ['full'], claims: ['test-time-scaling'] }),
  blogsIgnoreAxes: ids('4', { sharing: ['full'] }, 'blogs'),
  blogsOtherChapter: ids('8', {}, 'blogs'),
  sectionLabels: [
    (ACTIVE_SECTION_FILTER = '4', getSectionFilterLabel()),
    (ACTIVE_SECTION_FILTER = 'architecture/depth-control', getSectionFilterLabel())
  ]
}));
""")
        self.assertEqual(
            result,
            {
                "chapter4": ["a", "b"],
                "secondarySection": ["b"],
                "orWithinAxis": ["a", "b", "c"],
                "andAcrossAxes": ["a"],
                "sectionAndAxis": ["b"],
                "blogsIgnoreAxes": ["blog"],
                "blogsOtherChapter": [],
                "sectionLabels": ["§4 Architecture and Design", "§4.5 Controlling recurrence depth"],
            },
        )

    def test_facet_filter_groups_count_papers_in_vocabulary_order(self):
        result = self.run_top_level_tab_block("#papers", """
const papers = [
  { survey_section: ['architecture/topology'], loop_topology: 'partial', sharing: 'full', claims: ['stability', 'expressivity'] },
  { survey_section: ['architecture/topology'], loop_topology: 'whole-stack', sharing: 'full', claims: ['stability'] },
  { survey_section: ['architecture/topology'], loop_topology: 'partial', sharing: 'full', claims: [] }
].map(preparePaperRecord);
process.stdout.write(JSON.stringify(buildFacetFilterGroups(papers)));
""")
        self.assertEqual(
            result,
            [
                {
                    "id": "loop_topology",
                    "title": "Loop topology",
                    "values": [{"value": "whole-stack", "count": 1}, {"value": "partial", "count": 2}],
                },
                {"id": "sharing", "title": "Sharing", "values": [{"value": "full", "count": 3}]},
                {
                    "id": "claims",
                    "title": "Claims",
                    "values": [{"value": "expressivity", "count": 1}, {"value": "stability", "count": 2}],
                },
            ],
        )

    def test_active_facet_summary_and_filter_chips_are_escaped_toggle_controls(self):
        result = self.run_top_level_tab_block("#papers", """
ACTIVE_FACET_FILTERS = { claims: new Set(['stability', 'expressivity']), sharing: new Set(['full']) };
FACET_FILTER_GROUPS = [{ id: 'sharing', title: 'Sharing <b>', values: [{ value: 'full', count: 3 }, { value: 'partial-adapter', count: 1 }] }];
renderFacetFilterGroups();
process.stdout.write(JSON.stringify({ summary: renderActiveFacetFiltersHtml(), chips: facetFilterGroups.innerHTML }));
""")
        summary = result["summary"]
        self.assertEqual(summary.count("facet-filter-active-item"), 3)
        self.assertLess(summary.index('data-remove-facet-value="full"'), summary.index('data-remove-facet-value="expressivity"'))
        self.assertLess(summary.index('data-remove-facet-value="expressivity"'), summary.index('data-remove-facet-value="stability"'))
        self.assertIn('aria-label="Remove Claims filter: stability"', summary)
        self.assertIn('aria-label="Remove Sharing filter: full"', summary)
        self.assertIn('<span class="paper-chip-prefix">Claim</span>', summary)
        chips = result["chips"]
        self.assertIn("Sharing &lt;b&gt;", chips)
        self.assertNotIn("<b>", chips)
        self.assertIn('data-facet-value="full" aria-pressed="true"', chips)
        self.assertIn('data-facet-value="partial-adapter" aria-pressed="false"', chips)
        self.assertIn('<span class="facet-filter-chip-count">3</span>', chips)
        self.assertNotIn("disabled", chips)

    def test_section_badges_and_axis_chips_are_filter_links(self):
        result = self.run_top_level_tab_block("#papers", """
ACTIVE_SECTION_FILTER = '4';
ACTIVE_FACET_FILTERS = { sharing: new Set(['full']) };
process.stdout.write(JSON.stringify({
  primary: renderSectionBadgeHtml('architecture/topology', true, false),
  secondary: renderSectionBadgeHtml('scaling/test-time', false, true),
  unknown: renderSectionBadgeHtml('design/topology', true, false),
  axis: renderAxisChipHtml({ group: 'sharing', value: 'full' }),
  axisInactive: renderAxisChipHtml({ group: 'claims', value: 'stability' }, true)
}));
""")
        self.assertIn('class="paper-section-badge is-primary is-active"', result["primary"])
        self.assertIn('href="?section=architecture%2Ftopology&amp;sharing=full#papers"', result["primary"])
        self.assertIn('<span class="paper-section-title">Loop topology</span>', result["primary"])
        self.assertIn('title="Primary section: §4.1 Loop topology"', result["primary"])
        self.assertIn('class="paper-section-badge is-secondary"', result["secondary"])
        self.assertIn('aria-label="Also discussed in: §6.2 Test-time scaling"', result["secondary"])
        self.assertNotIn("paper-section-title", result["secondary"])
        self.assertEqual(result["unknown"], "")
        self.assertIn('class="paper-chip paper-chip-axis is-active"', result["axis"])
        self.assertIn('data-facet-group="sharing" data-facet-value="full"', result["axis"])
        self.assertIn('<span class="paper-chip-prefix">Sharing</span>full</a>', result["axis"])
        self.assertIn('href="?section=4&amp;sharing=full&amp;claims=stability#papers"', result["axisInactive"])
        self.assertNotIn("paper-chip-prefix", result["axisInactive"])

    def test_survey_list_groups_papers_by_part_chapter_and_primary_section(self):
        result = self.run_top_level_tab_block("#papers", """
const papers = [
  { id: 'late', survey_section: ['open-problems/diffusion'] },
  { id: 'topo2', survey_section: ['architecture/topology'] },
  { id: 'depth', survey_section: ['architecture/depth-control', 'architecture/topology'] },
  { id: 'topo1', survey_section: ['architecture/topology'] },
  { id: 'nowhere', survey_section: [] }
].map(preparePaperRecord);
process.stdout.write(JSON.stringify({ html: renderSurveyListHtml(papers, ''), counts: buildPrimaryChapterCounts(papers) }));
""")
        html = result["html"]
        order = [
            '<section class="survey-part" id="part-building">',
            '<span class="survey-part-label">Part III</span><h3 class="survey-part-title">Building, Training and Deploying</h3>',
            '<section class="survey-chapter" id="chapter-4" data-chapter="4">',
            '<span class="survey-count" aria-label="3 papers">3</span>',
            '<section class="survey-section" id="section-4-1" data-section-id="architecture/topology">',
            "[card topo2]",
            "[card topo1]",
            '<section class="survey-section" id="section-4-5" data-section-id="architecture/depth-control">',
            "[card depth]",
            '<section class="survey-part" id="part-open-problems">',
            '<section class="survey-chapter" id="chapter-10" data-chapter="10">',
            "[card late]",
            '<section class="survey-part" id="part-unplaced">',
            "[card nowhere]",
        ]
        positions = [html.index(marker) for marker in order]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(html.count("[card depth]"), 1)
        self.assertNotIn('id="part-foundations"', html)
        self.assertNotIn('id="chapter-5"', html)
        self.assertEqual(result["counts"], {"4": 3, "10": 1})

    def test_section_filter_options_are_grouped_by_chapter_with_counts(self):
        result = self.run_top_level_tab_block("#papers", """
ALL_PAPERS = [
  { survey_section: ['architecture/topology', 'scaling/test-time'] },
  { survey_section: ['architecture/topology'] }
].map(preparePaperRecord);
ALL_BLOGS = [{ entry_type: 'blog', survey_section: ['understanding/why'] }].map(preparePaperRecord);
ACTIVE_SECTION_FILTER = 'architecture/topology';
renderSectionFilter();
const papers = { html: sectionFilter.innerHTML, value: sectionFilter.value };
ACTIVE_TOP_LEVEL_TAB = 'blogs';
ACTIVE_SECTION_FILTER = '';
renderSectionFilter();
process.stdout.write(JSON.stringify({ papers: papers, blogs: sectionFilter.innerHTML }));
""")
        html = result["papers"]["html"]
        self.assertTrue(html.startswith('<option value="">All sections</option>'))
        self.assertEqual(html.count("<optgroup"), 9)
        self.assertIn('<optgroup label="§4 Architecture and Design"><option value="4">All of §4 · 2</option>', html)
        self.assertIn('<option value="architecture/topology">§4.1 Loop topology · 2</option>', html)
        self.assertIn('<option value="scaling/test-time">§6.2 Test-time scaling · 1</option>', html)
        self.assertIn('<option value="2">All of §2 · 0</option>', html)
        self.assertEqual(result["papers"]["value"], "architecture/topology")
        self.assertIn('<option value="understanding/why">§8.1 Why looped models work · 1</option>', result["blogs"])
        self.assertIn('<option value="architecture/topology">§4.1 Loop topology · 0</option>', result["blogs"])

    def test_reading_desk_survey_placement_lists_sections_and_specified_axes(self):
        desk = READING_DESK_JS_PATH.read_text(encoding="utf-8")
        start = desk.index("function renderReadingDeskSurveyHtml(paper) {")
        helper = desk[start:desk.index("/** Reuse catalog renderers", start)]
        result = self.run_top_level_tab_block("#papers", helper + """
const paper = preparePaperRecord({
  id: 'p', survey_section: ['architecture/topology', 'scaling/test-time'],
  loop_topology: 'partial', sharing: 'unspecified', depth_control: 'fixed', claims: ['stability'], comparison: []
});
const blog = preparePaperRecord({ id: 'b', entry_type: 'blog', survey_section: ['understanding/why'], sharing: 'full' });
const unplaced = preparePaperRecord({ id: 'u', entry_type: 'blog', survey_section: [] });
process.stdout.write(JSON.stringify({
  paper: renderReadingDeskSurveyHtml(paper),
  blog: renderReadingDeskSurveyHtml(blog),
  unplaced: renderReadingDeskSurveyHtml(unplaced)
}));
""")
        paper = result["paper"]
        self.assertLess(paper.index("§4.1"), paper.index("§6.2"))
        self.assertIn("is-primary", paper[:paper.index("§6.2")])
        for label in ("Loop topology", "Sharing", "Depth control", "Claims", "Looped-vs-untied comparison"):
            self.assertIn(f"<dt>{label}</dt>", paper)
        self.assertIn("<dt>Sharing</dt><dd><span class=\"desk-axis-unspecified\">unspecified</span></dd>", paper)
        self.assertIn("<dt>Looped-vs-untied comparison</dt><dd><span class=\"desk-axis-unspecified\">none recorded</span></dd>", paper)
        self.assertIn('data-facet-group="claims" data-facet-value="stability"', paper)
        self.assertNotIn('data-facet-group="sharing"', paper)
        self.assertIn("§8.1", result["blog"])
        self.assertNotIn("desk-axis-list", result["blog"])
        self.assertEqual(result["unplaced"], "<p>Not yet placed in a section.</p>")

    def test_stats_distribution_rows_link_to_filters_or_survey_anchors(self):
        """Stats rows are safe DOM nodes; axis rows reset filters and chapter rows open anchors."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        renderer_start = html.index("function renderStatsDistribution(")
        renderer = html[renderer_start:html.index("/** Label taxonomy sections by number", renderer_start)]
        self.assertNotIn("innerHTML", renderer)
        result = self.run_top_level_tab_block("#stats", """
class FakeElement {
  constructor(tagName) {
    this.tagName = tagName.toUpperCase();
    this.attributes = {};
    this.children = [];
    this.style = {};
    this.className = '';
    this.textContent = '';
  }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  appendChild(child) { this.children.push(child); return child; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
}
document.createElement = function(tagName) { return new FakeElement(tagName); };
""" + renderer + """
const data = { rows: [{ key: 'partial', label: 'partial', count: 2, percentage: 50 }] };
const plain = new FakeElement('div');
const axis = new FakeElement('div');
const chapter = new FakeElement('div');
const empty = new FakeElement('div');
renderStatsDistribution(plain, data);
renderStatsDistribution(axis, data, { facetGroup: 'loop_topology' });
renderStatsDistribution(chapter, { rows: [{ key: '4', label: '§4 Architecture and Design', count: 3, percentage: 30 }] }, {
  anchorFor: function(row) { return getChapterDomId(row.key); }
});
renderStatsDistribution(empty, { rows: [] });
function firstRow(container) {
  const item = container.children[0].children[0];
  return item.children[0] && item.children[0].tagName === 'A' ? item.children[0] : item;
}
process.stdout.write(JSON.stringify({
  roles: [plain.children[0].attributes.role, plain.children[0].children[0].attributes.role],
  plain: { tag: firstRow(plain).tagName, aria: firstRow(plain).attributes['aria-label'] },
  axis: firstRow(axis).attributes,
  axisTag: firstRow(axis).tagName,
  chapter: firstRow(chapter).attributes,
  empty: empty.children[0].textContent
}));
""")
        self.assertEqual(result["roles"], ["list", "listitem"])
        self.assertEqual(result["plain"], {"tag": "DIV", "aria": "partial: 2 papers, 50 percent"})
        self.assertEqual(result["axisTag"], "A")
        self.assertEqual(
            result["axis"],
            {
                "href": "?loop_topology=partial#papers",
                "data-facet-group": "loop_topology",
                "data-facet-value": "partial",
                "data-facet-reset": "true",
                "aria-label": "View 2 papers with Loop topology: partial",
            },
        )
        self.assertEqual(
            result["chapter"],
            {
                "href": "?#chapter-4",
                "data-survey-anchor": "chapter-4",
                "aria-label": "Browse 3 papers in §4 Architecture and Design",
            },
        )
        self.assertEqual(result["empty"], "No classification data is available.")

    def test_filter_link_click_interception_only_handles_unmodified_left_clicks(self):
        """Modified and non-left clicks retain the native anchor behavior."""
        result = self.run_top_level_tab_block("#papers", """
const base = { button: 0, defaultPrevented: false, metaKey: false, ctrlKey: false, shiftKey: false, altKey: false };
process.stdout.write(JSON.stringify({
  left: shouldHandleFacetLinkClick(base),
  prevented: shouldHandleFacetLinkClick({ ...base, defaultPrevented: true }),
  middle: shouldHandleFacetLinkClick({ ...base, button: 1 }),
  meta: shouldHandleFacetLinkClick({ ...base, metaKey: true }),
  ctrl: shouldHandleFacetLinkClick({ ...base, ctrlKey: true }),
  shift: shouldHandleFacetLinkClick({ ...base, shiftKey: true }),
  alt: shouldHandleFacetLinkClick({ ...base, altKey: true }),
  missing: shouldHandleFacetLinkClick(null)
}));
""")
        self.assertEqual(
            result,
            {
                "left": True, "prevented": False, "middle": False, "meta": False,
                "ctrl": False, "shift": False, "alt": False, "missing": False,
            },
        )
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        start = html.index("function initFacetLinkInteractions() {")
        source = html[start:html.index("function initTableInteractions() {", start)]
        self.assertIn("shouldHandleFacetLinkClick(event)", source)
        self.assertIn("a[data-survey-anchor]", source)
        self.assertIn("navigateToUnfilteredSurveyAnchor(anchorLink.dataset.surveyAnchor);", source)
        self.assertIn("a[data-facet-group][href]", source)
        self.assertIn("navigateToFacetLink(link);", source)
        self.assertIn("if (FACET_LINK_INTERACTIONS_BOUND) return;", source)

    def test_catalog_load_restores_url_filters_after_indexing_the_survey(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        build_start = html.index("function buildDOM(data) {")
        source = html[build_start:html.index("// ── Search", build_start)]
        order = (
            "setSurveyTaxonomy(data.survey_taxonomy);",
            "ALL_PAPERS = (data.papers || []).map(preparePaperRecord);",
            "ALL_BLOGS = (data.blogs || []).map(preparePaperRecord);",
            "FACET_FILTER_GROUPS = buildFacetFilterGroups(ALL_PAPERS);",
            "renderSurveyNav();",
            "renderSectionFilter();",
            "restoreFiltersFromUrl();",
            "restoreTopLevelTabAfterCatalogLoad();",
            "restoreSurveyHashPosition(window.location.hash);",
        )
        positions = [source.index(marker) for marker in order]
        self.assertEqual(positions, sorted(positions))
        init_start = html.index("function initTopLevelTabInteractions() {")
        init_source = html[init_start:html.index("function restoreTopLevelTabAfterCatalogLoad() {", init_start)]
        popstate = init_source[init_source.index("window.addEventListener('popstate'"):]
        self.assertIn("restoreFiltersFromUrl();", popstate)
        hashchange = init_source[init_source.index("window.addEventListener('hashchange'"):init_source.index("window.addEventListener('popstate'")]
        self.assertIn("restoreSurveyHashPosition(window.location.hash);", hashchange)
        self.assertNotIn("restoreFiltersFromUrl", hashchange)

    def test_search_query_sync_uses_replace_state_and_preserves_filter_params(self):
        """Free search updates q in place without losing section, axis params or the hash."""
        result = self.run_top_level_tab_block("#papers", """
window.location.href = 'https://example.test/index.html?section=4&sharing=full#papers';
window.location.search = '?section=4&sharing=full';
syncSearchQueryToUrl('Layer Norm');
syncSearchQueryToUrl('');
process.stdout.write(JSON.stringify({ calls: replaceStateCalls }));
""")
        self.assertEqual(
            result,
            {
                "calls": [
                    {"search": "?section=4&sharing=full&q=Layer+Norm", "hash": "#papers"},
                    {"search": "?section=4&sharing=full", "hash": "#papers"},
                ]
            },
        )

        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        helper_start = html.index("function syncSearchQueryToUrl(query) {")
        helper_end = html.index("function initSearch() {", helper_start)
        helper_source = html[helper_start:helper_end]
        self.assertIn("new URL(window.location.href)", helper_source)
        self.assertIn("nextUrl.searchParams.set('q'", helper_source)
        self.assertIn("nextUrl.searchParams.delete('q')", helper_source)
        self.assertIn("window.history.replaceState", helper_source)
        self.assertNotIn("pushState", helper_source)

    def test_search_input_syncs_q_immediately_and_debounces_captured_query(self):
        """Navigation sees the latest q while rendering still uses the input event value."""
        result = self.run_top_level_tab_block("#papers", """
window.location.href = 'https://example.test/index.html?claims=stability#papers';
window.location.search = '?claims=stability';
initSearch();
searchInput.value = 'first query';
const eventTarget = { value: 'first query' };
searchInput.listeners.input[0]({ target: eventTarget });
const immediateCalls = replaceStateCalls.slice();
eventTarget.value = 'overwritten';
setTimeout(function() {
  process.stdout.write(JSON.stringify({
    immediateCalls: immediateCalls,
    finalCalls: replaceStateCalls,
    searchCalls: searchCalls
  }));
}, 180);
""")
        expected_call = {"search": "?claims=stability&q=first+query", "hash": "#papers"}
        self.assertEqual(
            result,
            {
                "immediateCalls": [expected_call],
                "finalCalls": [expected_call],
                "searchCalls": ["first query"],
            },
        )

        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        search_start = html.index("function initSearch() {")
        search_end = html.index("function initPublicationDateFilter() {", search_start)
        search_source = html[search_start:search_end]
        capture_index = search_source.index("const query = e.target.value;")
        sync_index = search_source.index("syncSearchQueryToUrl(query);")
        debounce_index = search_source.index("debounce = setTimeout", sync_index)
        self.assertLess(capture_index, sync_index)
        self.assertLess(sync_index, debounce_index)
        self.assertIn("doSearch(query);", search_source[debounce_index:])
        self.assertNotIn("syncSearchQueryToUrl", search_source[debounce_index:])

    def test_pending_search_render_cannot_override_history_restored_query(self):
        """A stale input timer must not replace results restored by Back or Forward."""
        result = self.run_top_level_tab_block("#papers", """
CATALOG_DATA_READY = true;
window.location.href = 'https://example.test/index.html#papers';
initSearch();
searchInput.value = 'query A';
searchInput.listeners.input[0]({ target: searchInput });
window.location.href = 'https://example.test/index.html?q=query+B#papers';
window.location.search = '?q=query+B';
dispatchWindowEvent('popstate');
setTimeout(function() {
  process.stdout.write(JSON.stringify({
    input: searchInput.value,
    searchCalls: searchCalls
  }));
}, 180);
""")
        self.assertEqual(result, {"input": "query B", "searchCalls": ["query B"]})

        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        search_start = html.index("function initSearch() {")
        search_end = html.index("function initPublicationDateFilter() {", search_start)
        timer_source = html[html.index("debounce = setTimeout", search_start):search_end]
        self.assertIn("searchEl.value !== query", timer_source)
        self.assertIn("new URLSearchParams(window.location.search).get('q')", timer_source)

    def test_paper_titles_select_details_and_keep_primary_source_links(self):
        """Reading-desk titles select a resource while sources remain native links."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        desk = READING_DESK_JS_PATH.read_text(encoding="utf-8")
        render_start = html.index("function renderCard(paper, query) {")
        render_end = html.index("// ── State & Taxonomy", render_start)
        card = html[render_start:render_end]
        self.assertIn("function getPrimaryPaperUrl(paper)", html)
        self.assertIn("paper.links.blog", html)
        self.assertIn("paper.links.arxiv", html)
        self.assertIn("paper.links.paper", html)
        self.assertIn('class="desk-paper-select"', card)
        self.assertIn('aria-controls="paper-detail" aria-pressed="false"', card)
        self.assertIn('class="desk-open-paper"', desk)
        self.assertIn("getPrimaryPaperUrl(paper)", desk)
        self.assertIn("escapeHtml(primaryUrl)", desk)

    def test_survey_core_badge_replaces_the_foundation_badge(self):
        """Survey-core status is the only anchor badge; no classification disclosure remains."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("survey-core-badge", html)
        self.assertIn("paper.survey_core === true", html)
        self.assertIn('title="A core reference for loop models">Core</span>', html)
        self.assertNotIn("Looped Models Survey", html)
        self.assertNotIn("Survey core", html)
        self.assertNotIn("foundation", html)
        self.assertNotIn("category-disclaimer", html)
        self.assertNotIn("desk-scope", html)
        self.assertNotIn("About the classification", html)

    def test_adjacent_work_is_labeled_across_catalog_and_stats_views(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("catalog-fit-badge", html)
        self.assertIn("paper.catalog_fit === 'adjacent'", html)
        self.assertIn("Adjacent work", html)
        self.assertIn("outside the strict single-forward loop-model scope", html)
        self.assertIn('id="stats-total-papers-note"', html)

    def test_must_read_status_is_rendered_in_cards_details_and_table_titles(self):
        """The reading desk uses a text status while table titles retain their star."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        desk = READING_DESK_JS_PATH.read_text(encoding="utf-8")
        render_start = html.index("function renderCard(paper, query) {")
        render_end = html.index("// ── State & Taxonomy", render_start)
        marker = '(paper.must_read ? \'<span class="desk-must-read">Must read</span>\' : \'\')'
        self.assertIn(marker, html[render_start:render_end])
        self.assertIn(marker, desk)
        self.assertIn("must-read-marker", html)
        self.assertIn("paper.must_read", html)
        self.assertIn("🌟", html)
        self.assertIn("mustReadMarkerHtml + '<span>' + highlightQuery(paper.title, query) + '</span>' + surveyCoreBadgeHtml + catalogFitBadgeHtml", html)

    def test_filter_sidebar_hooks_exist_and_top_panel_resizer_is_removed(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('id="filter-sidebar-toggle"', html)
        self.assertIn('aria-controls="filter-sidebar-panel"', html)
        self.assertIn('id="filter-sidebar-panel"', html)
        self.assertIn('class="controls-bar filter-sidebar-controls"', html)
        self.assertIn('class="facet-filter-shell filter-sidebar-facet-shell"', html)
        sidebar_start = html.index('id="filter-sidebar-panel"')
        sidebar = html[sidebar_start:html.index("</aside>", sidebar_start)]
        self.assertIn('<select id="section-filter" onchange="setSectionFilter(this.value)">', sidebar)
        self.assertIn('id="facet-filter-groups"', sidebar)
        self.assertIn("function setFilterSidebarOpen(isOpen) {", html)
        self.assertIn("function updateFilterSidebarSummary() {", html)
        self.assertIn("document.body.classList.toggle('filter-sidebar-open', isOpen);", html)
        self.assertIn(".filter-sidebar[hidden]", html)
        self.assertIn("body.filter-sidebar-open .header-sub", html)
        self.assertNotIn("body.filter-sidebar-open h1", html)
        self.assertIn("body.filter-sidebar-open .filter-sidebar-toggle-row", html)
        self.assertIn("body.filter-sidebar-open > header {\n        padding: 12px;", html)
        self.assertIn(".filter-sidebar-controls {\n        grid-template-columns: 1fr;\n        gap: 10px;\n        overflow-x: visible;", html)
        self.assertIn(".filter-sidebar-controls .date-input {\n        flex: 1 1 128px;\n        width: auto;\n        min-width: 0;", html)
        chip_css = html[html.index(".facet-filter-chip {\n"):]
        self.assertIn("max-width: 100%;", chip_css[:chip_css.index("}")])
        init_start = html.index("function initFilterSidebarControls() {")
        init_end = html.index("function rerenderCurrentResults() {", init_start)
        init_source = html[init_start:init_end]
        self.assertIn("setFilterSidebarOpen(false);", init_source)
        self.assertNotIn("setFilterSidebarOpen(true);", init_source)
        self.assertNotIn(".filter-sidebar-backdrop", html)
        self.assertNotIn('id="filter-sidebar-backdrop"', html)
        self.assertNotIn("getElementById('filter-sidebar-backdrop')", html)
        self.assertNotIn("body.filter-sidebar-open .filter-sidebar-backdrop", html)
        self.assertNotIn('id="top-panel-resizer"', html)
        self.assertNotIn("function initTopPanelResizer() {", html)
        self.assertNotIn("top-panel-collapsed", html)

    def test_survey_nav_counts_are_synced_after_filtering(self):
        """Chapter navigation counts follow the filtered papers by primary chapter."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        sync_start = html.index("function syncSurveyNavCounts(filteredPapers) {")
        sync = html[sync_start:html.index("function renderAllGrids(q) {", sync_start)]
        self.assertIn("ACTIVE_TOP_LEVEL_TAB === 'blogs' ? {} : buildPrimaryChapterCounts(filteredPapers)", sync)
        self.assertIn(".survey-nav-link[data-chapter]", sync)
        self.assertIn("link.classList.toggle('is-empty', count === 0);", sync)
        renderer_start = html.index("function renderAllGrids(q) {")
        renderer = html[renderer_start:html.index("// ── Daily briefing page", renderer_start)]
        self.assertIn("syncSurveyNavCounts(filteredPapers);", renderer)
        nav_start = html.index("function renderSurveyNav() {")
        nav = html[nav_start:html.index("function activateSurveyNavLink(", nav_start)]
        self.assertIn("SURVEY.chapters.map", nav)
        self.assertIn("getChapterDomId(chapter.number)", nav)
        self.assertIn('<span class="survey-nav-count">0</span>', nav)
        self.assertNotIn("nodeKey", html)

    def test_blogs_section_support_exists_in_frontend(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("let ALL_BLOGS = [];", html)
        self.assertIn("function createBlogSection()", html)
        self.assertNotIn("createBlogTreeNode", html)
        self.assertIn("BLOG_SECTION_META", html)
        self.assertIn("section-blogs", html)
        self.assertIn("blogs-grid", html)

    def test_catalog_section_builders_create_empty_grid_shells(self):
        """Create one empty paper list and a separate lazy-rendered Blogs section."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        build_start = html.index("function buildDOM(data) {")
        build_end = html.index("// ── Search", build_start)
        list_builder = html[build_start:build_end]
        blog_start = html.index("function createBlogSection()")
        blog_end = html.index("function renderSurveyNav()", blog_start)
        blog_builder = html[blog_start:blog_end]
        renderer_start = html.index("function renderAllGrids(q) {")
        renderer_end = html.index("// ── Daily briefing page", renderer_start)
        renderer = html[renderer_start:renderer_end]

        self.assertIn("+ '<div class=\"survey-list\" id=\"papers-grid\"></div>';", list_builder)
        self.assertIn('<div class="paper-row-header" aria-hidden="true">', list_builder)
        self.assertNotIn("createCategorySection", html)
        self.assertIn("grid.id = 'blogs-grid';", blog_builder)
        for builder in (list_builder, blog_builder):
            self.assertNotIn("grid.innerHTML", builder)
            self.assertNotIn("renderCard(", builder)

        self.assertIn(
            "grid.innerHTML = isBlogs || !isList ? '' : renderSurveyListHtml(filteredPapers, query);",
            renderer,
        )
        self.assertIn(
            "blogsGrid.innerHTML = isBlogs ? filteredPapers.map(function(blog) { return renderCard(blog, query); }).join('') : '';",
            renderer,
        )
        self.assertEqual(html.count("grid.innerHTML ="), 1)
        self.assertEqual(html.count("blogsGrid.innerHTML ="), 1)

    def test_table_rows_are_rendered_only_for_table_view_and_cleared_in_list_view(self):
        """Preserve lazy table rendering when view modes change."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        renderer_start = html.index("function renderAllGrids(q) {")
        renderer_end = html.index("// ── Daily briefing page", renderer_start)
        renderer = html[renderer_start:renderer_end]

        self.assertIn(
            "if (CURRENT_VIEW === 'table') {\n    renderTableView(query, filteredPapers);\n  } else {",
            renderer,
        )
        self.assertIn("if (tableBody && tableBody.children.length) tableBody.textContent = '';", renderer)
        self.assertEqual(renderer.count("renderTableView(query, filteredPapers);"), 1)

    def test_briefing_tab_replaces_the_sidebar_notice(self):
        """The daily briefing is a top-level page; the sidebar keeps only the paper-watch countdown."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        for retired in (
            "daily-briefing-notice", "daily-briefing-summary", "daily-briefing-today-count", "daily-briefing-body",
            "updateDailyBriefingNotice", "hideStaleDailyBriefingNotice", "daily-briefing-paper",
        ):
            self.assertNotIn(retired, html)
        self.assertIn('<div class="daily-status-row">', html)

        # The Briefing tab sits right after Papers and controls its own panel.
        tabs_start = html.index('<div class="top-level-tabs" role="tablist"')
        tabs = html[tabs_start:html.index("</div>\n", tabs_start)]
        tab_ids = re.findall(r'id="(\w+)-tab" role="tab"', tabs)
        self.assertEqual(tab_ids, ["papers", "briefing", "stats", "blogs"])
        self.assertIn(
            '<button type="button" class="top-level-tab" id="briefing-tab" role="tab" aria-controls="briefing-panel" '
            'aria-selected="false" tabindex="-1"><span class="briefing-tab-label">Briefing</span>',
            tabs,
        )
        self.assertIn('<span class="briefing-tab-badge" id="briefing-tab-badge" hidden>', tabs)
        self.assertIn('<span class="briefing-tab-separator" aria-hidden="true">·</span>', tabs)
        self.assertIn('<span class="sr-only"> papers added today</span>', tabs)
        self.assertIn(
            '<section class="top-level-panel briefing-panel" id="briefing-panel" role="tabpanel" '
            'aria-labelledby="briefing-tab" tabindex="0" hidden>',
            html,
        )
        self.assertIn('<article class="briefing-page" id="briefing-page" aria-busy="false">', html)
        self.assertLess(html.index('id="stats-panel"'), html.index('id="briefing-panel"'))
        self.assertLess(html.index('id="briefing-panel"'), html.index("</main>"))

        # Today's New-York date drives the badge, rechecked every minute.
        self.assertIn("function getCurrentDailyWatchDateString()", html)
        self.assertIn("window.DAILY_WATCH_COUNTDOWN.getDailyWatchParts(new Date())", html)
        helper_start = html.index("function getCurrentDailyWatchDateString() {")
        helper = html[helper_start:html.index("function formatTableText(value)", helper_start)]
        self.assertIn("typeof window.DAILY_WATCH_COUNTDOWN.getDailyWatchParts !== 'function'", helper)
        self.assertIn("return '';", helper)
        page_start = html.index("// ── Daily briefing page")
        page_js = html[page_start:html.index("function createBlogSection() {", page_start)]
        self.assertIn("const currentDate = getCurrentDailyWatchDateString();", page_js)
        self.assertIn("briefing.date === currentDate", page_js)
        self.assertIn("candidate.verdict === 'added'", page_js)
        self.assertIn("badge.hidden = !isToday;", page_js)
        self.assertEqual(html.count("setInterval(updateBriefingTabBadge, 60_000);"), 1)

        build_dom_start = html.index("function buildDOM(data) {")
        build_dom = html[build_dom_start:html.index("// ── Search", build_dom_start)]
        self.assertIn(
            "LATEST_BRIEFING_SUMMARY = Array.isArray(data.briefings) && data.briefings[0] ? data.briefings[0] : null;",
            build_dom,
        )
        self.assertIn("data.meta.latest_briefing_version", build_dom)
        self.assertIn("updateBriefingTabBadge();", build_dom)

        # The page body is fetched lazily from briefing-latest.json with a cache-busting version.
        self.assertIn("const BRIEFING_PAGE_URL = 'briefing-latest.json';", page_js)
        self.assertIn("BRIEFING_PAGE_URL + (version ? '?v=' + encodeURIComponent(version) : '')", page_js)
        self.assertIn("BRIEFING_PAGE_STATE === 'loading' || BRIEFING_PAGE_STATE === 'ready'", page_js)
        self.assertIn("The latest briefing could not be loaded.", page_js)
        self.assertIn("'https://github.com/huskydoge/Awesome-Loop-Models/blob/main/'", page_js)
        self.assertIn("renderBriefingMarkdown(briefing.body_markdown, { dropLeadingTitle: true })", page_js)
        self.assertNotIn("innerHTML = briefing.body_markdown", page_js)

        # Like Stats, the Briefing page hides the catalog toolbar and the detail column.
        self.assertIn("body.stats-mode .catalog-toolbar-shell, body.briefing-mode .catalog-toolbar-shell {\n      display: none;", html)
        desk_js = READING_DESK_JS_PATH.read_text(encoding="utf-8")
        self.assertIn("&& !document.body.classList.contains('briefing-mode')", desk_js)

        watch_start = html.index('<section class="desk-watch"')
        status_start = html.index('<div class="daily-status-row">', watch_start)
        countdown_markup = html.index('<div class="daily-watch-countdown"', status_start)
        watch_end = html.index('</section>', countdown_markup)
        sidebar_end = html.index('</aside>', watch_start)
        self.assertIn('aria-label="Catalog watch"', html[watch_start:status_start])
        self.assertNotIn('desk-watch-title', html)
        self.assertNotIn('<details', html[watch_start:watch_end])
        self.assertLess(status_start, countdown_markup)
        self.assertLess(watch_end, sidebar_end)

        status_css_start = html.index("\n    .daily-status-row {\n") + 1
        status_css_end = html.index("}", status_css_start)
        status_css = html[status_css_start:status_css_end]
        for declaration in (
            "display: flex;",
            "align-items: flex-start;",
            "flex-wrap: wrap;",
            "justify-content: center;",
            "width: 100%;",
        ):
            self.assertIn(declaration, status_css)

    def test_briefing_tab_routes_and_hides_the_catalog_tools(self):
        """#briefing selects the Briefing page, hides Papers and Stats, and loads its body once."""
        result = self.run_top_level_tab_block("#briefing", """
const initial = {
  active: ACTIVE_TOP_LEVEL_TAB,
  briefingMode: bodyClasses['briefing-mode'],
  statsMode: bodyClasses['stats-mode'],
  panels: { papers: papersPanel.hidden, briefing: briefingPanel.hidden, stats: statsPanel.hidden },
  selected: tabs.map(tab => tab.attributes['aria-selected']),
  loads: briefingLoads.length,
  searches: searchCalls.length
};
CATALOG_DATA_READY = true;
tabs[0].listeners.click[0]();
dispatchWindowEvent('hashchange');
const papers = { active: ACTIVE_TOP_LEVEL_TAB, briefingMode: bodyClasses['briefing-mode'], panels: [papersPanel.hidden, briefingPanel.hidden], searches: searchCalls.length };
tabs[1].listeners.click[0]();
dispatchWindowEvent('hashchange');
process.stdout.write(JSON.stringify({
  initial, papers,
  back: { active: ACTIVE_TOP_LEVEL_TAB, hash: window.location.hash, loads: briefingLoads.length, searches: searchCalls.length },
  normalized: ['briefing', 'nope'].map(normalizeTopLevelTab)
}));
""")
        self.assertEqual(result["initial"], {
            "active": "briefing",
            "briefingMode": True,
            "statsMode": False,
            "panels": {"papers": True, "briefing": False, "stats": True},
            "selected": ["false", "true", "false", "false"],
            "loads": 1,
            "searches": 0,
        })
        self.assertEqual(result["papers"], {"active": "papers", "briefingMode": False, "panels": [False, True], "searches": 1})
        # Each activation asks for the page; loadBriefingPage itself fetches only once (see the node check).
        self.assertEqual(result["back"], {"active": "briefing", "hash": "#briefing", "loads": 3, "searches": 1})
        self.assertEqual(result["normalized"], ["briefing", "papers"])

    def test_daily_status_row_reflows_without_detached_positioning(self):
        """Daily status remains in flow and becomes compact on phones."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertNotIn("position: absolute;\n      top: 58px;", html)
        self.assertNotIn('id="daily-watch-countdown-value" aria-live=', html)
        self.assertIn('id="daily-watch-countdown-value">Calculating…</div>', html)
        self.assertIn('<span class="daily-watch-clock" aria-hidden="true"></span>', html)
        self.assertIn('<div class="daily-watch-countdown-copy">', html)
        self.assertIn('<div class="daily-watch-countdown-label">Next paper watch</div>', html)
        self.assertNotIn('"briefing countdown"', html)
        self.assertIn(".papers-only-tools > .daily-status-row { order: 2; }", html)
        self.assertIn(".papers-only-tools > .search-wrap { order: 3; }", html)
        self.assertIn("@keyframes daily-watch-clock-spin", html)
        self.assertIn("animation: daily-watch-clock-spin 60s steps(60, end) infinite;", html)
        self.assertIn(".daily-watch-clock::after { animation: none; }", html)
        self.assertNotIn(".daily-briefing-notice", html)
        meta_start = html.index(".daily-watch-countdown-meta {\n")
        meta_end = html.index("}", meta_start)
        self.assertIn("display: none;", html[meta_start:meta_end])

    def test_papers_list_is_grouped_by_survey_part_chapter_and_section(self):
        """The list view follows the survey outline; the old category shelves are gone."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertNotIn("function createCategorySection", html)
        self.assertIn("function renderSurveyListHtml(papers, query) {", html)
        self.assertIn("function renderSurveySectionHtml(section, papers, query) {", html)
        self.assertIn('id="section-filter" onchange="setSectionFilter(this.value)"', html)

    def test_quick_filter_controls_and_table_view_markup_exist(self):
        """Expose the supported quick filters alongside both catalog views."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        for snippet in (
            "Peer-reviewed",
            "w/ code",
            "w/ comments",
            "List view",
            "Table view",
            "table-view-shell",
            "papers-table-body",
        ):
            self.assertIn(snippet, html)
        self.assertIn(
            '<button type="button" class="sort-btn" id="newly-arrived-only-toggle" '
            'aria-pressed="false" onclick="toggleNewlyArrivedOnly()">Newly Arrived</button>',
            html,
        )

        header_start = html.index('<table class="papers-table" aria-label="Table view of loop-model resources">')
        header_end = html.index("</thead>", header_start)
        header_snippet = html[header_start:header_end]
        expected_markers = (
            '<th scope="col">Title</th>',
            'class="sort-btn table-sort-btn" data-sort="date" onclick="setSort(\'date\')">Date</button>',
            '<th scope="col">Venue</th>',
            '<th scope="col">Links</th>',
            '<th scope="col">Section</th>',
            '<th scope="col">Design axes</th>',
            'class="sort-btn table-sort-btn" data-sort="citations" onclick="setSort(\'citations\')">Citations</button>',
            'class="sort-btn table-sort-btn" data-sort="stars" onclick="setSort(\'stars\')">Stars</button>',
        )
        header_positions = [header_snippet.index(marker) for marker in expected_markers]
        self.assertEqual(header_positions, sorted(header_positions))
        for marker in expected_markers:
            self.assertIn(marker, header_snippet)
        self.assertIn('class="table-sort-direction-btn" data-sort="date"', header_snippet)
        self.assertIn('onclick="toggleSortDirection(\'date\')"', header_snippet)
        self.assertIn('class="table-sort-direction-btn" data-sort="citations"', header_snippet)
        self.assertIn('onclick="toggleSortDirection(\'citations\')"', header_snippet)
        self.assertIn('class="table-sort-direction-btn" data-sort="stars"', header_snippet)
        self.assertIn('onclick="toggleSortDirection(\'stars\')"', header_snippet)
        self.assertIn('aria-label="Toggle Date sort direction"', header_snippet)
        self.assertIn('aria-label="Toggle Citations sort direction"', header_snippet)
        self.assertIn('aria-label="Toggle Stars sort direction"', header_snippet)
        self.assertEqual(header_snippet.count('<th scope="col">'), 8)
        self.assertNotIn('<th scope="col">Year</th>', header_snippet)
        self.assertNotIn("Category / Subcategory", header_snippet)
        self.assertNotIn("Focus", header_snippet)
        self.assertNotIn("Domains", header_snippet)
        self.assertNotIn("Added", header_snippet)

    def test_top_level_papers_stats_and_blogs_tab_shell_exists(self):
        """All three navigation choices expose their tab and panel relationships."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        for snippet in (
            '<button type="button" class="top-level-tab active" id="papers-tab" role="tab" aria-controls="papers-panel" aria-selected="true" tabindex="0"',
            '<button type="button" class="top-level-tab" id="stats-tab" role="tab" aria-controls="stats-panel" aria-selected="false" tabindex="-1"',
            '<button type="button" class="top-level-tab" id="blogs-tab" role="tab" aria-controls="papers-panel" aria-selected="false" tabindex="-1"',
            '<div class="top-level-panel" id="papers-panel" role="tabpanel" aria-labelledby="papers-tab" tabindex="0"',
            '<section class="top-level-panel stats-panel" id="stats-panel" role="tabpanel" aria-labelledby="stats-tab" tabindex="0" hidden>',
        ):
            self.assertIn(snippet, html)

        for snippet in (
            'role="tablist"',
            "let ACTIVE_TOP_LEVEL_TAB = 'papers';",
            "function setTopLevelTab(tab, options) {",
            "function applyTopLevelTab() {",
            "List view",
            "Table view",
        ):
            self.assertIn(snippet, html)

    def test_top_level_tabs_and_tools_use_the_three_column_reading_desk(self):
        """The rail owns navigation while search and details occupy separate columns."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        style = READING_DESK_CSS_PATH.read_text(encoding="utf-8")
        sidebar_start = html.index('<aside class="sidebar"')
        sidebar_end = html.index('</aside>', sidebar_start)
        sidebar = html[sidebar_start:sidebar_end]
        main_start = html.index('<main id="main">')
        main_end = html.index("</main>", main_start)
        main = html[main_start:main_end]
        tools_start = main.index('<div class="catalog-toolbar-shell">')
        tools_end = main.index('id="papers-panel"', tools_start)
        tools = main[tools_start:tools_end]
        detail_start = html.index('<dialog class="paper-detail"', main_end)

        self.assertLess(sidebar_end, main_start)
        self.assertLess(main_end, detail_start)
        self.assertIn('<div class="site-brand">', sidebar)
        self.assertIn('<svg class="site-brand-mark"', sidebar)
        self.assertNotIn('A field guide to recurrent depth', sidebar)
        self.assertNotIn('id="sidebar-nav"', sidebar)
        self.assertIn('id="section-filter"', tools)
        self.assertNotIn('id="mobile-directory"', html)
        self.assertIn('<div class="top-level-tabs" role="tablist"', sidebar)
        self.assertIn('<div class="header-actions">', sidebar)
        self.assertIn('aria-orientation="vertical"', sidebar)
        brand_index = sidebar.index('<div class="site-brand">')
        tabs_index = sidebar.index('<div class="top-level-tabs" role="tablist"')
        actions_index = sidebar.index('<div class="header-actions">')
        self.assertLess(brand_index, tabs_index)
        self.assertLess(tabs_index, actions_index)
        self.assertNotIn("top-level-tabs", main)
        for marker in (
            'id="briefing-tab"',
            'id="daily-watch-countdown"',
            'id="research-prompt-launch"',
            'href="submit.html"',
            'id="desk-theme-toggle"',
            'class="desk-theme-moon"',
            'class="desk-theme-sun"',
        ):
            self.assertIn(marker, sidebar)
        for marker in (
            'class="search-wrap"',
            'id="filter-sidebar-toggle"',
            'id="filter-sidebar-panel"',
            'id="desk-sort"',
            'id="desk-view"',
        ):
            self.assertIn(marker, tools)
        for element_id in (
            "papers-tab",
            "stats-tab",
            "briefing-tab",
            "briefing-panel",
            "header-github-link",
            "daily-watch-countdown",
        ):
            self.assertEqual(html.count(f'id="{element_id}"'), 1)

        apply_start = html.index("function applyTopLevelTab() {")
        apply_end = html.index("function setTopLevelTab(tab, options) {", apply_start)
        apply_helper = html[apply_start:apply_end]
        self.assertIn("document.body.classList.toggle('stats-mode', isStats);", apply_helper)
        self.assertIn("document.body.classList.toggle('briefing-mode', isBriefing);", apply_helper)
        self.assertIn("papersPanel.hidden = isStats || isBriefing;", apply_helper)
        self.assertIn("if (briefingPanel) briefingPanel.hidden = !isBriefing;", apply_helper)
        self.assertNotIn("daily-briefing-notice", sidebar)
        self.assertIn("syncReadingDeskPanel();", apply_helper)

        self.assertRegex(style, r"grid-template-columns:\s*var\(--desk-rail\)\s+minmax\([^;]+\)\s+1px\s+minmax\([^;]+\);")
        self.assertIn(".reading-desk.stats-mode .layout", style)
        self.assertIn(".reading-desk.briefing-mode .layout", style)
        self.assertIn(".stats-mode .survey-nav, .briefing-mode .survey-nav, .blogs-mode .survey-nav { display: none; }", style)
        self.assertIn(".reading-desk .layout.table-view-active", style)
        self.assertIn("grid-template-columns: var(--desk-rail) minmax(0, 1fr);", style)
        self.assertIn(".reading-desk .catalog-toolbar-shell { position: sticky;", style)
        mobile_start = style.index("@media (max-width: 768px)")
        mobile_css = style[mobile_start:]
        self.assertIn(".reading-desk .top-level-tabs { flex-direction: row;", mobile_css)
        self.assertIn(".reading-desk .header-actions { display: flex;", mobile_css)
        self.assertIn(".desk-watch { margin: 0; grid-row: 4; grid-column: 1 / -1;", mobile_css)
        self.assertIn(".reading-desk .paper-detail { width: calc(100vw - 24px);", mobile_css)

    def test_editorial_masthead_is_compact_on_desktop_without_shrinking_mobile_targets(self):
        """Desktop chrome should be shorter while mobile keeps its existing tap targets."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        editorial_start = html.index("    /* ── Personal-site-aligned editorial system ── */")
        editorial_end = html.index("  </style>", editorial_start)
        editorial_css = html[editorial_start:editorial_end]
        mobile_start = editorial_css.index("    @media (max-width: 768px)")
        desktop_css = editorial_css[:mobile_start]
        mobile_css = editorial_css[mobile_start:]

        self.assertIn(
            "body > header,\n    body:not(.stats-mode):not(.briefing-mode) > header,\n"
            "    body.stats-mode > header,\n    body.briefing-mode > header {",
            desktop_css,
        )
        self.assertIn("padding: 0 24px;", desktop_css)
        self.assertIn("min-height: 52px;", desktop_css)
        self.assertIn("width: 28px;", desktop_css)
        self.assertIn("height: 28px;", desktop_css)
        self.assertIn("min-height: 32px;", desktop_css)
        self.assertIn("min-height: 58px;", mobile_css)
        self.assertIn("min-height: 44px;", mobile_css)

    def test_editorial_form_controls_inherit_the_site_typeface(self):
        """Native controls should not fall back to Arial or monospace beside serif content."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "button,\n    input,\n    select,\n    textarea {\n      font: inherit;\n    }",
            html,
        )

    def test_small_filter_rows_scroll_instead_of_stacking(self):
        """Narrow tag routes should preserve paper space without clipping controls."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        editorial_start = html.index("    /* ── Personal-site-aligned editorial system ── */")
        editorial_css = html[editorial_start:html.index("  </style>", editorial_start)]
        self.assertIn("@media (max-width: 900px)", editorial_css)
        self.assertIn(".filter-sidebar-controls .sort-bar,", editorial_css)
        self.assertIn("flex-wrap: nowrap;", editorial_css)
        self.assertIn("overflow-x: auto;", editorial_css)
        self.assertIn("scrollbar-width: none;", editorial_css)
        self.assertIn(".filter-sidebar-controls .date-input {\n        flex: 0 0 132px;", editorial_css)

    def test_top_level_tabs_restore_hash_and_support_keyboard_navigation(self):
        """Top-level tabs must preserve survey anchors and expose full tab keyboard UX."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")

        hash_start = html.index("function getTopLevelTabFromHash(hash) {")
        hash_end = html.index("function applyTopLevelTab() {", hash_start)
        hash_helper = html[hash_start:hash_end]
        self.assertIn("hash === '#stats'", hash_helper)
        self.assertIn("hash === '#briefing'", hash_helper)
        self.assertIn("hash === '#blogs'", hash_helper)
        self.assertIn("hash === '#section-blogs'", hash_helper)

        keyboard_start = html.index("function handleTopLevelTabKeydown(event) {")
        init_start = html.index("function initTopLevelTabInteractions() {", keyboard_start)
        init_end = html.index("function restoreTopLevelTabAfterCatalogLoad() {", init_start)
        init_helper = html[init_start:init_end]
        self.assertIn("addEventListener('click'", init_helper)
        self.assertIn("addEventListener('keydown', handleTopLevelTabKeydown)", init_helper)
        self.assertIn("window.addEventListener('hashchange'", init_helper)
        self.assertIn(
            "setTopLevelTab(getTopLevelTabFromHash(window.location.hash), { updateHash: false })",
            init_helper,
        )
        self.assertIn("restoreSurveyHashPosition(window.location.hash)", init_helper)
        self.assertIn("restoreFiltersFromUrl()", init_helper)

        restore_start = html.index("function restoreTopLevelTabAfterCatalogLoad() {")
        restore_end = html.index("initTopLevelTabInteractions();", restore_start)
        restore_helper = html[restore_start:restore_end]
        self.assertIn("window.location.hash || !HAS_USER_SELECTED_TOP_LEVEL_TAB", restore_helper)
        self.assertIn("getTopLevelTabFromHash(window.location.hash)", restore_helper)
        self.assertIn("ACTIVE_TOP_LEVEL_TAB", restore_helper)
        self.assertIn("setTopLevelTab(requestedTab, { updateHash: false })", restore_helper)

        build_start = html.index("function buildDOM(data) {")
        build_end = html.index("// ── Search", build_start)
        build_helper = html[build_start:build_end]
        data_ready_index = build_helper.index("CATALOG_DATA_READY = true;")
        sections_created_index = build_helper.index('id="papers-grid"')
        restore_index = build_helper.index("restoreTopLevelTabAfterCatalogLoad();")
        survey_restore_index = build_helper.index("restoreSurveyHashPosition(window.location.hash);")
        self.assertLess(data_ready_index, restore_index)
        self.assertLess(sections_created_index, survey_restore_index)
        self.assertLess(restore_index, survey_restore_index)

        bootstrap_start = html.index("initTopLevelTabInteractions();", restore_end)
        bootstrap_end = html.index("initResearchPrompt();", bootstrap_start)
        bootstrap_helper = html[bootstrap_start:bootstrap_end]
        self.assertIn(
            "initTopLevelTabInteractions();\nsetTopLevelTab(getTopLevelTabFromHash(window.location.hash), { updateHash: false });",
            bootstrap_helper,
        )

        setter_start = html.index("function setTopLevelTab(tab, options) {")
        setter_end = html.index("function handleTopLevelTabKeydown(event) {", setter_start)
        setter_helper = html[setter_start:setter_end]
        self.assertIn("window.location.hash !== nextHash", setter_helper)
        self.assertIn("window.location.hash = nextHash", setter_helper)

    def test_top_level_hash_mapping_behavior(self):
        """Blogs has its own route while survey anchors stay on Papers."""
        result = self.run_top_level_tab_block("", """
const hashes = ['#stats', '#papers', '#briefing', '#blogs', '#section-blogs', '', '#part-building', '#chapter-4', '#section-4-5'];
const result = hashes.map(function(hash) {
  return { hash: hash, tab: getTopLevelTabFromHash(hash) };
});
process.stdout.write(JSON.stringify(result));
""")
        self.assertEqual(
            result,
            [
                {"hash": "#stats", "tab": "stats"},
                {"hash": "#papers", "tab": "papers"},
                {"hash": "#briefing", "tab": "briefing"},
                {"hash": "#blogs", "tab": "blogs"},
                {"hash": "#section-blogs", "tab": "blogs"},
                {"hash": "", "tab": "papers"},
                {"hash": "#part-building", "tab": "papers"},
                {"hash": "#chapter-4", "tab": "papers"},
                {"hash": "#section-4-5", "tab": "papers"},
            ],
        )

    def test_blogs_navigation_rerenders_and_legacy_route_does_not_scroll(self):
        """Blogs owns the shared content panel and legacy links never scroll Papers."""
        result = self.run_top_level_tab_block("#papers", """
CATALOG_DATA_READY = true;
ACTIVE_SECTION_FILTER = 'architecture/topology';
searchInput.value = 'depth';
window.location.search = '?q=depth';
blogsTab.listeners.click[0]();
dispatchWindowEvent('hashchange');
const entered = {
  active: ACTIVE_TOP_LEVEL_TAB,
  hash: window.location.hash,
  selected: tabs.map(tab => tab.attributes['aria-selected']),
  tabStops: tabs.map(tab => tab.tabIndex),
  labelledBy: papersPanel.attributes['aria-labelledby'],
  heading: catalogHeading.textContent,
  searchLabel: searchInput.attributes['aria-label'],
  placeholder: searchInput.placeholder,
  panels: [papersPanel.hidden, statsPanel.hidden, briefingPanel.hidden],
  searches: searchCalls.slice()
};
setBrowserHash('#section-blogs');
dispatchWindowEvent('hashchange');
flushAnimationFrames();
process.stdout.write(JSON.stringify({
  entered,
  legacy: { active: ACTIVE_TOP_LEVEL_TAB, section: ACTIVE_SECTION_FILTER, scrolls: scrollRequests }
}));
""")
        self.assertEqual(result["entered"], {
            "active": "blogs",
            "hash": "#blogs",
            "selected": ["false", "false", "false", "true"],
            "tabStops": [-1, -1, -1, 0],
            "labelledBy": "blogs-tab",
            "heading": "Blogs",
            "searchLabel": "Search blogs",
            "placeholder": "Search blogs, authors, keywords…",
            "panels": [False, True, True],
            "searches": ["depth"],
        })
        self.assertEqual(result["legacy"], {
            "active": "blogs", "section": "architecture/topology", "scrolls": [],
        })

    def test_top_level_keyboard_navigation_behavior(self):
        """Arrow/Home/End activate and focus tabs while Enter/Space retain native click."""
        result = self.run_top_level_tab_block("", """
function runKey(tabIndex, key) {
  setBrowserHash('#' + tabs[tabIndex].id.replace('-tab', ''));
  dispatchWindowEvent('hashchange');
  focusedTabId = null;
  hashWrites.length = 0;
  let prevented = false;
  tabs[tabIndex].listeners.keydown[0]({
    key: key,
    currentTarget: tabs[tabIndex],
    preventDefault: function() { prevented = true; }
  });
  return {
    key: key,
    from: tabs[tabIndex].id,
    prevented: prevented,
    focused: focusedTabId,
    active: ACTIVE_TOP_LEVEL_TAB,
    hash: window.location.hash,
    hashWrites: hashWrites.slice()
  };
}
const result = [
  runKey(0, 'ArrowRight'),
  runKey(1, 'ArrowRight'),
  runKey(2, 'ArrowRight'),
  runKey(3, 'ArrowRight'),
  runKey(0, 'ArrowLeft'),
  runKey(1, 'ArrowLeft'),
  runKey(2, 'ArrowLeft'),
  runKey(3, 'ArrowLeft'),
  runKey(2, 'Home'),
  runKey(0, 'End'),
  runKey(0, 'Enter'),
  runKey(0, ' ')
];
process.stdout.write(JSON.stringify(result));
""")
        expected = []
        for key, source, target in (
            ("ArrowRight", "papers-tab", "briefing"),
            ("ArrowRight", "briefing-tab", "stats"),
            ("ArrowRight", "stats-tab", "blogs"),
            ("ArrowRight", "blogs-tab", "papers"),
            ("ArrowLeft", "papers-tab", "blogs"),
            ("ArrowLeft", "briefing-tab", "papers"),
            ("ArrowLeft", "stats-tab", "briefing"),
            ("ArrowLeft", "blogs-tab", "stats"),
            ("Home", "stats-tab", "papers"),
            ("End", "papers-tab", "blogs"),
        ):
            expected.append(
                {
                    "key": key,
                    "from": source,
                    "prevented": True,
                    "focused": f"{target}-tab",
                    "active": target,
                    "hash": f"#{target}",
                    "hashWrites": [f"#{target}"],
                }
            )
        expected.extend(
            {
                "key": key,
                "from": "papers-tab",
                "prevented": False,
                "focused": None,
                "active": "papers",
                "hash": "#papers",
                "hashWrites": [],
            }
            for key in ("Enter", " ")
        )
        self.assertEqual(
            result,
            expected,
        )

    def test_initial_stats_hash_activates_loading_panel_before_catalog_data(self):
        """A direct Stats URL must reveal its panel and enter the loading path immediately."""
        result = self.run_top_level_tab_block("#stats", """
const result = {
  active: ACTIVE_TOP_LEVEL_TAB,
  statsMode: bodyClasses['stats-mode'],
  papersHidden: papersPanel.hidden,
  statsHidden: statsPanel.hidden,
  papersSelected: papersTab.attributes['aria-selected'],
  statsSelected: statsTab.attributes['aria-selected'],
  briefingHidden: briefingPanel.hidden,
  briefingMode: bodyClasses['briefing-mode'],
  briefingLoads: briefingLoads.length,
  renderCalls: renderStatsCalls,
  hashWrites: hashWrites,
  listeners: {
    papersClick: (papersTab.listeners.click || []).length,
    papersKeydown: (papersTab.listeners.keydown || []).length,
    statsClick: (statsTab.listeners.click || []).length,
    statsKeydown: (statsTab.listeners.keydown || []).length,
    briefingClick: (briefingTab.listeners.click || []).length,
    briefingKeydown: (briefingTab.listeners.keydown || []).length,
    hashchange: (windowListeners.hashchange || []).length
  }
};
process.stdout.write(JSON.stringify(result));
""")
        self.assertEqual(result["active"], "stats")
        self.assertTrue(result["statsMode"])
        self.assertTrue(result["papersHidden"])
        self.assertFalse(result["statsHidden"])
        self.assertEqual(result["papersSelected"], "false")
        self.assertEqual(result["statsSelected"], "true")
        self.assertTrue(result["briefingHidden"])
        self.assertFalse(result["briefingMode"])
        self.assertEqual(result["briefingLoads"], 0)
        self.assertEqual(result["renderCalls"], [{"ready": False, "error": False}])
        self.assertEqual(result["hashWrites"], [])
        self.assertEqual(
            result["listeners"],
            {
                "papersClick": 1,
                "papersKeydown": 1,
                "statsClick": 1,
                "statsKeydown": 1,
                "briefingClick": 1,
                "briefingKeydown": 1,
                "hashchange": 1,
            },
        )

    def test_top_level_click_history_reconcile_and_survey_anchor_restore_behavior(self):
        """History restores survey anchors in the list view without touching filters or the hash."""
        result = self.run_top_level_tab_block("", """
statsTab.listeners.click[0]();
const firstClick = { active: ACTIVE_TOP_LEVEL_TAB, writes: hashWrites.slice() };
statsTab.listeners.click[0]();
const repeatedClick = { active: ACTIVE_TOP_LEVEL_TAB, writes: hashWrites.slice() };

hashWrites.length = 0;
setBrowserHash('#stats');
dispatchWindowEvent('hashchange');
const statsHistory = { active: ACTIVE_TOP_LEVEL_TAB, writes: hashWrites.slice() };

CATALOG_DATA_READY = true;
CURRENT_VIEW = 'table';
ACTIVE_SECTION_FILTER = 'architecture/topology';
setBrowserHash('#chapter-4');
dispatchWindowEvent('hashchange');
const anchorBeforeFrame = {
  active: ACTIVE_TOP_LEVEL_TAB,
  section: ACTIVE_SECTION_FILTER,
  view: CURRENT_VIEW,
  hash: window.location.hash,
  writes: hashWrites.slice(),
  queuedFrames: animationFrameCallbacks.length,
  scrolls: scrollRequests.slice()
};
flushAnimationFrames();
const anchorAfterFrame = { scrolls: scrollRequests.slice(), activated: activatedNavTargets.slice() };

scrollRequests.length = 0;
setBrowserHash('#chapter-4');
dispatchWindowEvent('hashchange');
setBrowserHash('#stats');
dispatchWindowEvent('hashchange');
flushAnimationFrames();
const staleAnchorFrame = {
  active: ACTIVE_TOP_LEVEL_TAB,
  hash: window.location.hash,
  scrolls: scrollRequests.slice()
};

setBrowserHash('#chapter-four');
dispatchWindowEvent('hashchange');
const invalidAnchor = { active: ACTIVE_TOP_LEVEL_TAB, queuedFrames: animationFrameCallbacks.length };

process.stdout.write(JSON.stringify({
  firstClick: firstClick,
  repeatedClick: repeatedClick,
  statsHistory: statsHistory,
  anchorBeforeFrame: anchorBeforeFrame,
  anchorAfterFrame: anchorAfterFrame,
  staleAnchorFrame: staleAnchorFrame,
  invalidAnchor: invalidAnchor
}));
""")
        self.assertEqual(result["firstClick"], {"active": "stats", "writes": ["#stats"]})
        self.assertEqual(result["repeatedClick"], {"active": "stats", "writes": ["#stats"]})
        self.assertEqual(result["statsHistory"], {"active": "stats", "writes": []})
        self.assertEqual(
            result["anchorBeforeFrame"],
            {
                "active": "papers",
                "section": "architecture/topology",
                "view": "list",
                "hash": "#chapter-4",
                "writes": [],
                "queuedFrames": 1,
                "scrolls": [],
            },
        )
        self.assertEqual(result["anchorAfterFrame"], {"scrolls": ["chapter-4"], "activated": ["chapter-4"]})
        self.assertEqual(result["staleAnchorFrame"], {"active": "stats", "hash": "#stats", "scrolls": []})
        self.assertEqual(result["invalidAnchor"], {"active": "papers", "queuedFrames": 0})

    def test_catalog_load_reconcile_preserves_empty_hash_user_choice_but_honors_hash(self):
        """Load completion preserves an unrepresented user choice unless a hash drives state."""
        result = self.run_top_level_tab_block("", """
statsTab.listeners.click[0]();
setBrowserHash('');
CATALOG_DATA_READY = true;
restoreTopLevelTabAfterCatalogLoad();
const emptyHashAfterClick = ACTIVE_TOP_LEVEL_TAB;

setBrowserHash('#papers');
restoreTopLevelTabAfterCatalogLoad();
const explicitPapers = ACTIVE_TOP_LEVEL_TAB;

setBrowserHash('#stats');
restoreTopLevelTabAfterCatalogLoad();
const explicitStats = ACTIVE_TOP_LEVEL_TAB;

setBrowserHash('#section-blogs');
restoreTopLevelTabAfterCatalogLoad();
const explicitBlogsAnchor = ACTIVE_TOP_LEVEL_TAB;

process.stdout.write(JSON.stringify({
  emptyHashAfterClick: emptyHashAfterClick,
  explicitPapers: explicitPapers,
  explicitStats: explicitStats,
  explicitBlogsAnchor: explicitBlogsAnchor
}));
""")
        self.assertEqual(
            result,
            {
                "emptyHashAfterClick": "stats",
                "explicitPapers": "papers",
                "explicitStats": "stats",
                "explicitBlogsAnchor": "blogs",
            },
        )

    def test_survey_anchor_navigation_leaves_stats_and_restores_repeated_hash(self):
        """Chapter navigation must reveal Papers and restore even when the hash is unchanged."""
        result = self.run_top_level_tab_block("#stats", """
CATALOG_DATA_READY = true;
navigateToSurveyAnchor('section-4-5');
const firstNavigation = {
  active: ACTIVE_TOP_LEVEL_TAB,
  hash: window.location.hash,
  writes: hashWrites.slice(),
  papersHidden: papersPanel.hidden,
  statsHidden: statsPanel.hidden,
  queuedFrames: animationFrameCallbacks.length
};
dispatchWindowEvent('hashchange');
flushAnimationFrames();
const firstScrolls = scrollRequests.slice();

hashWrites.length = 0;
scrollRequests.length = 0;
CURRENT_VIEW = 'table';
navigateToSurveyAnchor('section-4-5');
const repeatedNavigation = {
  active: ACTIVE_TOP_LEVEL_TAB,
  hash: window.location.hash,
  writes: hashWrites.slice(),
  view: CURRENT_VIEW,
  queuedFrames: animationFrameCallbacks.length
};
flushAnimationFrames();

process.stdout.write(JSON.stringify({
  firstNavigation: firstNavigation,
  firstScrolls: firstScrolls,
  repeatedNavigation: repeatedNavigation,
  repeatedScrolls: scrollRequests,
  activated: activatedNavTargets
}));
""")
        self.assertEqual(
            result["firstNavigation"],
            {
                "active": "papers",
                "hash": "#section-4-5",
                "writes": ["#section-4-5"],
                "papersHidden": False,
                "statsHidden": True,
                "queuedFrames": 0,
            },
        )
        self.assertEqual(result["firstScrolls"], ["section-4-5"])
        self.assertEqual(
            result["repeatedNavigation"],
            {"active": "papers", "hash": "#section-4-5", "writes": [], "view": "list", "queuedFrames": 1},
        )
        self.assertEqual(result["repeatedScrolls"], ["section-4-5"])
        self.assertEqual(result["activated"], ["section-4-5", "section-4-5"])

    def test_stats_chapter_links_open_the_unfiltered_list_at_the_anchor(self):
        """Stats chapter counts are unfiltered, so following one clears filters before scrolling."""
        result = self.run_top_level_tab_block("#stats", """
CATALOG_DATA_READY = true;
window.location.href = 'https://example.test/index.html?section=9&sharing=full&q=norm#stats';
window.location.search = '?section=9&sharing=full&q=norm';
ACTIVE_SECTION_FILTER = '9';
ACTIVE_FACET_FILTERS = { sharing: new Set(['full']) };
HAS_COMMENTS_ONLY = true;
publicationDateEnd.value = '2026-01-01';
navigateToUnfilteredSurveyAnchor('chapter-4');
const before = {
  pushes: pushStateCalls.slice(),
  active: ACTIVE_TOP_LEVEL_TAB,
  section: ACTIVE_SECTION_FILTER,
  groups: Object.keys(ACTIVE_FACET_FILTERS),
  query: searchInput.value,
  comments: HAS_COMMENTS_ONLY,
  endDate: publicationDateEnd.value,
  queuedFrames: animationFrameCallbacks.length
};
flushAnimationFrames();
process.stdout.write(JSON.stringify({ before: before, scrolls: scrollRequests }));
""")
        self.assertEqual(
            result,
            {
                "before": {
                    "pushes": [{"search": "", "hash": "#chapter-4"}],
                    "active": "papers",
                    "section": "",
                    "groups": [],
                    "query": "",
                    "comments": False,
                    "endDate": "",
                    "queuedFrames": 1,
                },
                "scrolls": ["chapter-4"],
            },
        )

    def test_stats_series_helpers_use_strict_utc_date_parsing(self):
        """Stats helpers must reject normalized-looking but impossible dates."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        parse_start = html.index("function parseIsoDate(value) {")
        parse_end = html.index("function formatIsoDateUtc(date) {", parse_start)
        parse_helper = html[parse_start:parse_end]
        format_start = parse_end
        format_end = html.index("function buildDailyPublicationSeries(papers) {", format_start)
        format_helper = html[format_start:format_end]

        self.assertIn("/^\\d{4}-\\d{2}-\\d{2}$/", parse_helper)
        self.assertIn("setUTCFullYear", parse_helper)
        self.assertIn("setUTCHours", parse_helper)
        self.assertIn("getUTCFullYear()", parse_helper)
        self.assertIn("getUTCMonth()", parse_helper)
        self.assertIn("getUTCDate()", parse_helper)
        self.assertNotIn("new Date(value)", parse_helper)
        self.assertIn("getUTCFullYear()", format_helper)
        self.assertIn("getUTCMonth()", format_helper)
        self.assertIn("getUTCDate()", format_helper)

    def test_daily_stats_series_uses_only_publication_dates_and_fills_utc_days(self):
        """Release cadence must use published dates without intake-date fallback."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        daily_start = html.index("function buildDailyPublicationSeries(papers) {")
        daily_end = html.index("function buildMonthlyPublicationSeries(papers) {", daily_start)
        daily_helper = html[daily_start:daily_end]

        self.assertIn("parseIsoDate(paper && paper.published_date)", daily_helper)
        self.assertNotIn("added_date", daily_helper)
        self.assertIn("setUTCDate", daily_helper)
        for field in ("key:", "label:", "count:", "cumulative:"):
            self.assertIn(field, daily_helper)

    def test_monthly_stats_series_uses_publication_dates_and_fills_utc_months(self):
        """Publication history must use monthly published-date buckets only."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        monthly_start = html.index("function buildMonthlyPublicationSeries(papers) {")
        monthly_end = html.index("function addTrailingAverage(series, windowSize) {", monthly_start)
        monthly_helper = html[monthly_start:monthly_end]

        self.assertIn("paper.published_date", monthly_helper)
        self.assertNotIn("added_date", monthly_helper)
        self.assertIn("setUTCMonth", monthly_helper)
        for field in ("key:", "label:", "count:", "cumulative:"):
            self.assertIn(field, monthly_helper)

    def test_release_helpers_exclude_intake_dates_and_define_range_contracts(self):
        """All pure Stats derivation must be release-only and range-aware."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        helpers_start = html.index("function buildDailyPublicationSeries(papers) {")
        helpers_end = html.index("function createStatsSvgElement(", helpers_start)
        helpers = html[helpers_start:helpers_end]

        for function_name in (
            "buildDailyPublicationSeries",
            "buildMonthlyPublicationSeries",
            "addTrailingAverage",
            "aggregateWeeklySeries",
            "slicePublicationRange",
            "buildReleasePulseFacts",
            "buildReleaseStatsSummary",
            "buildStatsDistribution",
            "buildRecentStatsDistribution",
        ):
            self.assertIn(f"function {function_name}(", helpers)
        self.assertNotIn("added_date", helpers)
        self.assertIn("range === '90d'", helpers)
        self.assertIn("range === 'all'", helpers)
        self.assertIn("windowSize = 14", helpers)
        self.assertIn("windowSize = 7", helpers)
        self.assertIn("source = daily.slice(-365)", helpers)
        self.assertIn("function extendDailySeriesThrough(", helpers)
        self.assertIn("function extendMonthlySeriesThrough(", helpers)
        self.assertIn("windowSize = 6", helpers)

    def test_stats_helpers_execute_date_series_and_summary_boundaries(self):
        """Execute strict dates, gap filling, release KPIs, and stable ordering."""
        result = self.run_stats_series_helpers("""(function() {
  const daily = buildDailyPublicationSeries([
    { published_date: '2026-07-01' },
    { published_date: '2026-07-03' },
    { published_date: '2026-07-03' },
    { added_date: '2026-07-02' },
    { published_date: '2026-02-29' }
  ]);
  const monthly = buildMonthlyPublicationSeries([
    { published_date: '2025-11-15' },
    { published_date: '2026-01-01' },
    { added_date: '2025-12-01' }
  ]);
  const lowYearMonthly = buildMonthlyPublicationSeries([
    { published_date: '0099-12-15' },
    { published_date: '0100-01-01' }
  ]);
  const summaryPapers = [
    { id: 'jan-b', title: 'Beta', published_date: '2026-01-02' },
    { id: 'jan-a', title: 'Alpha', published_date: '2026-01-01' },
    { id: 'jan-c', title: 'Gamma', published_date: '2026-01-03' },
    { id: 'mar-b', title: 'Beta', published_date: '2026-03-02' },
    { id: 'mar-a', title: 'Alpha', published_date: '2026-03-01' },
    { id: 'june', title: 'Older', published_date: '2026-06-03' },
    { id: 'latest-b', title: 'Beta', published_date: '2026-07-03' },
    { id: 'latest-a2', title: 'Alpha', published_date: '2026-07-03' },
    { id: 'latest-a1', title: 'Alpha', published_date: '2026-07-03' },
    { id: 'intake-only', title: 'Ignored', added_date: '2026-07-04' },
    { id: 'invalid', title: 'Invalid', published_date: '2026-02-29' }
  ];
  const summaryDaily = buildDailyPublicationSeries(summaryPapers);
  const summaryMonthly = buildMonthlyPublicationSeries(summaryPapers);
  const rangeDaily = Array.from({ length: 400 }, function(_, index) {
    var count = index === 35 ? 8 : (index === 36 ? 2 : (index === 310 ? 5 : (index === 311 ? 1 : 0)));
    return { key: 'd' + index, label: 'd' + index, count: count, cumulative: index };
  });
  const rangeMonthly = Array.from({ length: 12 }, function(_, index) {
    return { key: 'm' + index, label: 'm' + index, count: index === 0 ? 6 : 0, cumulative: index };
  });
  const ninetyDays = slicePublicationRange(rangeDaily, rangeMonthly, '90d');
  const oneYear = slicePublicationRange(rangeDaily, rangeMonthly, '1y');
  const allTime = slicePublicationRange(rangeDaily, rangeMonthly, 'all');
  return {
    dates: {
      invalidType: parseIsoDate(null),
      invalidFormat: parseIsoDate('2026/02/28'),
      impossible: parseIsoDate('2026-02-29'),
      yearZero: parseIsoDate('0000-01-01'),
      yearNinetyNine: formatIsoDateUtc(parseIsoDate('0099-12-31')),
      leapDay: formatIsoDateUtc(parseIsoDate('2024-02-29'))
    },
    daily: daily,
    monthly: monthly,
    lowYearMonthly: lowYearMonthly,
    averages: addTrailingAverage([
      { key: 'a', count: 2 },
      { key: 'b', count: 4 },
      { key: 'c', count: 0 }
    ], 14).map(function(bucket) { return bucket.average; }),
    normalizedAverages: addTrailingAverage([
      { key: 'a', count: Infinity },
      { key: 'b', count: -4 },
      { key: 'c', count: '3' },
      { key: 'd', count: NaN }
    ], 2).map(function(bucket) { return bucket.average; }),
    ranges: {
      ninetyDays: {
        range: ninetyDays.range,
        granularity: ninetyDays.granularity,
        windowSize: ninetyDays.windowSize,
        length: ninetyDays.series.length,
        firstKey: ninetyDays.series[0].key,
        lastKey: ninetyDays.series[ninetyDays.series.length - 1].key,
        firstAverages: ninetyDays.series.slice(0, 2).map(function(bucket) { return bucket.average; })
      },
      oneYear: {
        range: oneYear.range,
        granularity: oneYear.granularity,
        windowSize: oneYear.windowSize,
        length: oneYear.series.length,
        firstKey: oneYear.series[0].key,
        lastKey: oneYear.series[oneYear.series.length - 1].key,
        firstAverages: oneYear.series.slice(0, 2).map(function(bucket) { return bucket.average; })
      },
      allTime: {
        range: allTime.range,
        granularity: allTime.granularity,
        windowSize: allTime.windowSize,
        length: allTime.series.length,
        firstKey: allTime.series[0].key,
        lastKey: allTime.series[allTime.series.length - 1].key,
        firstAverages: allTime.series.slice(0, 2).map(function(bucket) { return bucket.average; })
      }
    },
    emptyRange: slicePublicationRange(null, null, 'unexpected'),
    emptySummary: buildReleaseStatsSummary(null, null),
    summary: buildReleaseStatsSummary(summaryPapers, summaryDaily),
    chapterDistribution: buildStatsDistribution([
      { _primaryChapter: '4' },
      { _primaryChapter: '8' },
      { _primaryChapter: '4' }
    ], '_primaryChapter', { '4': '§4 Architecture and Design', '8': '§8 Understanding Why Looped Models Work' }),
    claimDistribution: buildStatsDistribution([
      { claims: ['stability', 'stability', 'param-efficiency'] },
      { claims: ['stability'] },
      { claims: [] }
    ], 'claims'),
    recentDirections: buildRecentStatsDistribution([
      { published_date: '2026-07-03', survey_section: ['architecture/topology', 'scaling/test-time'] },
      { published_date: '2026-06-01', survey_section: ['architecture/topology'] },
      { published_date: '2026-03-01', survey_section: ['understanding/why'] }
    ], 'survey_section', 90, 1),
    emptyDistribution: buildStatsDistribution(null, 'loop_topology')
  };
})()""")

        self.assertEqual(
            result["dates"],
            {
                "invalidType": None,
                "invalidFormat": None,
                "impossible": None,
                "yearZero": None,
                "yearNinetyNine": "0099-12-31",
                "leapDay": "2024-02-29",
            },
        )
        self.assertEqual(
            result["daily"],
            [
                {"key": "2026-07-01", "label": "2026-07-01", "count": 1, "cumulative": 1},
                {"key": "2026-07-02", "label": "2026-07-02", "count": 0, "cumulative": 1},
                {"key": "2026-07-03", "label": "2026-07-03", "count": 2, "cumulative": 3},
            ],
        )
        self.assertEqual(
            result["monthly"],
            [
                {"key": "2025-11", "label": "2025-11", "count": 1, "cumulative": 1},
                {"key": "2025-12", "label": "2025-12", "count": 0, "cumulative": 1},
                {"key": "2026-01", "label": "2026-01", "count": 1, "cumulative": 2},
            ],
        )
        self.assertEqual(
            result["lowYearMonthly"],
            [
                {"key": "0099-12", "label": "0099-12", "count": 1, "cumulative": 1},
                {"key": "0100-01", "label": "0100-01", "count": 1, "cumulative": 2},
            ],
        )
        self.assertEqual(
            result["emptySummary"],
            {
                "totalPapers": 0,
                "releasesLast30Days": 0,
                "releasesPrevious30Days": 0,
                "releaseChangePercent": 0,
                "latestReleaseDate": None,
            },
        )
        self.assertEqual(result["averages"], [2, 3, 2])
        self.assertEqual(result["normalizedAverages"], [0, 0, 1.5, 1.5])
        self.assertEqual(
            result["ranges"],
            {
                "ninetyDays": {
                    "range": "90d",
                    "granularity": "day",
                    "windowSize": 14,
                    "length": 90,
                    "firstKey": "d310",
                    "lastKey": "d399",
                    "firstAverages": [5, 3],
                },
                "oneYear": {
                    "range": "1y",
                    "granularity": "day",
                    "windowSize": 7,
                    "length": 365,
                    "firstKey": "d35",
                    "lastKey": "d399",
                    "firstAverages": [8, 5],
                },
                "allTime": {
                    "range": "all",
                    "granularity": "month",
                    "windowSize": 6,
                    "length": 12,
                    "firstKey": "m0",
                    "lastKey": "m11",
                    "firstAverages": [6, 3],
                },
            },
        )
        self.assertEqual(
            result["emptyRange"],
            {"range": "1y", "granularity": "day", "windowSize": 7, "series": []},
        )
        self.assertEqual(result["summary"]["totalPapers"], 11)
        self.assertEqual(result["summary"]["releasesLast30Days"], 3)
        self.assertEqual(result["summary"]["releasesPrevious30Days"], 1)
        self.assertEqual(result["summary"]["releaseChangePercent"], 200)
        self.assertEqual(result["summary"]["latestReleaseDate"], "2026-07-03")
        self.assertEqual(
            result["chapterDistribution"],
            {
                "totalPapers": 3,
                "assignmentCount": 3,
                "rows": [
                    {"key": "4", "label": "§4 Architecture and Design", "count": 2, "percentage": 66.7},
                    {"key": "8", "label": "§8 Understanding Why Looped Models Work", "count": 1, "percentage": 33.3},
                ],
            },
        )
        self.assertEqual(
            result["claimDistribution"],
            {
                "totalPapers": 3,
                "assignmentCount": 3,
                "rows": [
                    {"key": "stability", "label": "Stability", "count": 2, "percentage": 66.7},
                    {"key": "param-efficiency", "label": "Param efficiency", "count": 1, "percentage": 33.3},
                ],
            },
        )
        self.assertEqual(
            result["emptyDistribution"],
            {"totalPapers": 0, "assignmentCount": 0, "rows": []},
        )
        self.assertEqual(
            result["recentDirections"],
            {
                "totalPapers": 2,
                "assignmentCount": 2,
                "rows": [
                    {"key": "architecture/topology", "label": "Architecture/topology", "count": 2, "percentage": 100},
                ],
            },
        )

    def test_stats_series_extend_through_today_and_keep_latest_release(self):
        """Live Stats pad empty days and months through today without moving the latest release."""
        result = self.run_stats_series_helpers("""(function() {
  const papers = [
    { published_date: '2026-11-22', survey_section: ['architecture/topology'] },
    { published_date: '2026-11-24', survey_section: ['training/post-training'] },
    { published_date: '2026-08-01', survey_section: ['understanding/why'] }
  ];
  const daily = extendDailySeriesThrough(buildDailyPublicationSeries(papers), '2026-11-26');
  const monthly = extendMonthlySeriesThrough(buildMonthlyPublicationSeries(papers), '2027-01-03');
  return {
    today: getStatsTodayKey(new Date(2026, 10, 26, 23, 59)),
    dailyTail: daily.slice(-3).map(function(bucket) { return [bucket.key, bucket.count, bucket.cumulative]; }),
    notShortened: extendDailySeriesThrough(buildDailyPublicationSeries(papers), '2026-11-01').slice(-1)[0].key,
    invalidEnd: extendDailySeriesThrough(buildDailyPublicationSeries(papers), 'soon').length,
    emptyDaily: extendDailySeriesThrough(null, '2026-11-26'),
    monthlyTail: monthly.slice(-3).map(function(bucket) { return [bucket.key, bucket.count, bucket.cumulative]; }),
    latest: buildReleaseStatsSummary(papers, daily).latestReleaseDate,
    oneYearLast: slicePublicationRange(daily, monthly, '1y').series.slice(-1)[0].key,
    recent: buildRecentStatsDistribution(papers, 'survey_section', 90, 5, '2026-11-26').totalPapers,
    recentAnchoredLater: buildRecentStatsDistribution(papers, 'survey_section', 3, 5, '2026-11-26').totalPapers
  };
})()""")
        self.assertEqual(result["today"], "2026-11-26")
        self.assertEqual(
            result["dailyTail"],
            [["2026-11-24", 1, 3], ["2026-11-25", 0, 3], ["2026-11-26", 0, 3]],
        )
        self.assertEqual(result["notShortened"], "2026-11-24")
        self.assertEqual(result["invalidEnd"], 116)
        self.assertEqual(result["emptyDaily"], [])
        self.assertEqual(
            result["monthlyTail"],
            [["2026-11", 2, 3], ["2026-12", 0, 3], ["2027-01", 0, 3]],
        )
        self.assertEqual(result["latest"], "2026-11-24")
        self.assertEqual(result["oneYearLast"], "2026-11-26")
        self.assertEqual(result["recent"], 2)
        self.assertEqual(result["recentAnchoredLater"], 1)

    def test_weekly_release_series_facts_and_axis_are_exact(self):
        """1Y uses gap-free weekly sums, headline facts, and clean integer axis steps."""
        result = self.run_stats_series_helpers("""(function() {
  const daily = Array.from({ length: 16 }, function(_, index) {
    return { key: 'd' + index, label: 'd' + index, count: index % 5 === 0 ? 2 : 0, cumulative: index };
  });
  const weeks = aggregateWeeklySeries(daily);
  const facts = buildReleasePulseFacts({ series: weeks });
  return {
    weeks: weeks.map(function(week) { return [week.key, week.endKey, week.count, week.cumulative]; }),
    facts: facts,
    emptyFacts: buildReleasePulseFacts(null),
    emptyWeeks: aggregateWeeklySeries(null)
  };
})()""")
        self.assertEqual(result["weeks"], [["d0", "d6", 4, 6], ["d7", "d13", 2, 13], ["d14", "d15", 2, 15]])
        self.assertEqual(result["facts"], {"total": 8, "peak": {"key": "d0", "count": 4}, "average": 8 / 3, "periods": 3})
        self.assertEqual(result["emptyFacts"], {"total": 0, "peak": None, "average": 0, "periods": 0})
        self.assertEqual(result["emptyWeeks"], [])

        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        axis_start = html.index("function niceStatsAxis(")
        axis_end = html.index("function selectTimelineTickIndices(", axis_start)
        script = html[axis_start:axis_end] + """
process.stdout.write(JSON.stringify([niceStatsAxis(17, 4), niceStatsAxis(45, 4), niceStatsAxis(0, 4), niceStatsAxis(3, 4)]));
"""
        axes = json.loads(subprocess.check_output(["node", "-e", script], text=True))
        self.assertEqual(axes, [{"max": 20, "step": 5}, {"max": 50, "step": 10}, {"max": 1, "step": 1}, {"max": 3, "step": 1}])

    def test_release_chart_exposes_hover_and_keyboard_readout(self):
        """Every plotted period is readable by pointer or keyboard without innerHTML."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        render_start = html.index("function renderReleasePulseChart(container, series, options) {")
        render_end = html.index("function renderStatsSparkline(", render_start)
        render_source = html[render_start:render_end]
        for marker in (
            "stats-chart-tooltip",
            "timeline-crosshair",
            "'pointermove'",
            "'keydown'",
            "ArrowLeft",
            "ArrowRight",
            "describeStatsPeriod(point.bucket, granularity)",
            "tabindex: 0",
        ):
            self.assertIn(marker, render_source)
        self.assertNotIn("innerHTML", render_source)
        stats_start = html.index('<section class="top-level-panel stats-panel"')
        stats_markup = html[stats_start:html.index("</section>", stats_start)]
        for marker in ('id="release-pulse-facts"', 'id="release-pulse-peak"', 'id="stats-latest-thirty-spark"'):
            self.assertIn(marker, stats_markup)

    def test_stats_panel_has_catalog_intelligence_dashboard(self):
        """Stats markup must expose the approved editorial Research Landscape."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        stats_start = html.index('<section class="top-level-panel stats-panel"')
        stats_end = html.index("</section>", stats_start)
        stats_markup = html[stats_start:stats_end]

        for marker in (
            "Research landscape",
            "Loop Models, mapped.",
            'id="stats-snapshot"',
            'class="stats-metric-rail"',
            'id="stats-total-papers"',
            'id="stats-latest-thirty"',
            'id="stats-recent-change"',
            'id="stats-recent-change-note"',
            'id="stats-latest-release"',
            'class="stats-dashboard-grid stats-dashboard-primary stats-landscape-primary"',
            'id="release-pulse-chart"',
            'id="release-pulse-summary"',
            'id="stats-chapter-distribution"',
            'id="stats-topology-distribution"',
            'id="stats-active-directions"',
            'data-stats-direction="section" aria-pressed="true"',
            'data-stats-direction="claims" aria-pressed="false"',
            'class="stats-dashboard-grid stats-dashboard-secondary stats-landscape-secondary"',
            'class="stats-range-control"',
            'data-stats-range="90d"',
            'data-stats-range="1y"',
            'data-stats-range="all"',
            'aria-pressed="true">1Y</button>',
            "Release trend",
            "Topic map",
            "Chapters",
            "Loop topology",
            "Active directions",
        ):
            self.assertIn(marker, stats_markup)
        self.assertIn('aria-live="polite"', stats_markup)
        self.assertNotIn('id="release-pulse-chart" tabindex=', stats_markup)
        self.assertNotIn("stats-panel-placeholder", stats_markup)
        for obsolete in (
            "Catalog Growth",
            "Collection telemetry",
            "added date",
            "intake",
            "stats-latest-seven",
            "stats-date-coverage",
            "stats-peak-day",
            "catalog-growth-chart",
            "publication-trend-chart",
            "stats-signal-card",
            "stats-hero-latest",
            "stats-peak-month",
            "Release dossiers",
            "Long arc",
            "long-arc-chart",
            "Annual volume",
            'id="annual-release-volume"',
            "stats-taxonomy-details",
            "stats-tag-explorer",
            "stats-tag-search",
            "stats-tag-results",
            "Latest publications",
            "latest-releases-list",
            "stats-category-distribution",
            "stats-mechanism-distribution",
            "Category mix",
            "Loop mechanisms",
            'data-stats-direction="focus"',
            'data-stats-direction="domain"',
        ):
            self.assertNotIn(obsolete, stats_markup)

    def test_stats_range_control_rerenders_only_the_selected_release_window(self):
        """Range changes must stay local to Stats and never pass full daily history."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        state_start = html.index("let ACTIVE_TOP_LEVEL_TAB = 'papers';")
        state_end = html.index("let CURRENT_VIEW = 'list';", state_start)
        state_source = html[state_start:state_end]
        bind_start = html.index("function initStatsRangeInteractions() {")
        bind_end = html.index("function renderStatsPanel() {", bind_start)
        bind_source = html[bind_start:bind_end]
        pulse_start = html.index("function renderReleasePulse(")
        pulse_end = html.index("function initStatsRangeInteractions() {", pulse_start)
        pulse_source = html[pulse_start:pulse_end]

        self.assertIn("let CURRENT_STATS_RANGE = '1y';", state_source)
        self.assertIn("let STATS_RANGE_LISTENERS_BOUND = false;", state_source)
        self.assertIn("if (STATS_RANGE_LISTENERS_BOUND) return;", bind_source)
        self.assertIn("STATS_RANGE_LISTENERS_BOUND = true;", bind_source)
        self.assertIn("CURRENT_STATS_RANGE = button.dataset.statsRange;", bind_source)
        self.assertIn("setAttribute('aria-pressed'", bind_source)
        self.assertIn("renderReleasePulse();", bind_source)
        self.assertNotIn("location.hash", bind_source)
        self.assertIn(
            "slicePublicationRange(STATS_DAILY_RELEASES, STATS_MONTHLY_RELEASES, CURRENT_STATS_RANGE)",
            pulse_source,
        )
        self.assertIn("rangeData.series", pulse_source)
        self.assertNotIn("renderReleasePulseChart(container, STATS_DAILY_RELEASES", pulse_source)

    def test_stats_release_chart_resize_observer_deduplicates_visible_widths(self):
        """Release chart resizing should rerender once per new visible integer width."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        observer_start = html.index("function initStatsReleaseChartResizeObserver() {")
        observer_end = html.index("/** Register the native range buttons", observer_start)
        observer_source = html[observer_start:observer_end]
        render_start = html.index("function renderStatsPanel() {")
        render_end = html.index("function escapeHtml(str) {", render_start)
        render_source = html[render_start:render_end]

        for marker in (
            "typeof ResizeObserver !== 'function'",
            "Math.round(container.getBoundingClientRect().width",
            "width === LAST_STATS_RELEASE_CHART_WIDTH",
            "!CATALOG_DATA_READY || !panel || panel.hidden",
            "renderReleasePulse();",
        ):
            self.assertIn(marker, observer_source)
        self.assertIn("initStatsReleaseChartResizeObserver();", render_source)
        self.assertGreater(
            render_source.index("initStatsReleaseChartResizeObserver();"),
            render_source.index("if (!CATALOG_DATA_READY)"),
        )

        script = f"""
let STATS_RELEASE_CHART_RESIZE_OBSERVER = null;
let LAST_STATS_RELEASE_CHART_WIDTH = 0;
let CATALOG_DATA_READY = true;
let renderCalls = 0;
let observerCalls = 0;
let resizeCallback = null;
const panel = {{ hidden: false }};
const container = {{
  clientWidth: 640,
  getBoundingClientRect() {{ return {{ width: 640 }}; }}
}};
const document = {{
  getElementById(id) {{
    if (id === 'release-pulse-chart') return container;
    if (id === 'stats-panel') return panel;
    return null;
  }}
}};
function renderReleasePulse() {{ renderCalls += 1; }}
globalThis.ResizeObserver = function(callback) {{
  observerCalls += 1;
  resizeCallback = callback;
  this.observe = function(target) {{ if (target !== container) throw new Error('wrong target'); }};
}};
{observer_source}
initStatsReleaseChartResizeObserver();
initStatsReleaseChartResizeObserver();
resizeCallback([{{ contentRect: {{ width: 640.4 }} }}]);
resizeCallback([{{ contentRect: {{ width: 699.6 }} }}]);
resizeCallback([{{ contentRect: {{ width: 700.4 }} }}]);
panel.hidden = true;
resizeCallback([{{ contentRect: {{ width: 710 }} }}]);
panel.hidden = false;
resizeCallback([{{ contentRect: {{ width: 710 }} }}]);
CATALOG_DATA_READY = false;
resizeCallback([{{ contentRect: {{ width: 720 }} }}]);
delete globalThis.ResizeObserver;
STATS_RELEASE_CHART_RESIZE_OBSERVER = null;
initStatsReleaseChartResizeObserver();
process.stdout.write(JSON.stringify({{
  observerCalls,
  renderCalls,
  lastWidth: LAST_STATS_RELEASE_CHART_WIDTH
}}));
"""
        result = json.loads(subprocess.check_output(["node", "-e", script], text=True))
        self.assertEqual(result, {"observerCalls": 1, "renderCalls": 2, "lastWidth": 710})

    def test_stats_render_slice_is_release_only(self):
        """The entire Stats render path must remain independent of catalog intake dates."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        stats_start = html.index("function buildDailyPublicationSeries(papers) {")
        stats_end = html.index("function escapeHtml(str) {", stats_start)
        stats_source = html[stats_start:stats_end]

        self.assertNotIn("added_date", stats_source)
        self.assertNotIn("Catalog Growth", stats_source)
        self.assertNotIn("intake", stats_source.lower())

    def test_stats_panel_lazy_render_waits_for_catalog_data(self):
        """Activating Stats before fetch completion must not lock an empty render."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        state_start = html.index("let ACTIVE_TOP_LEVEL_TAB = 'papers';")
        setter_start = html.index("function setTopLevelTab(tab, options) {", state_start)
        setter_end = html.index("function handleTopLevelTabKeydown(event) {", setter_start)
        setter_source = html[setter_start:setter_end]
        restore_start = html.index("function restoreTopLevelTabAfterCatalogLoad() {", setter_end)
        restore_end = html.index("initTopLevelTabInteractions();", restore_start)
        restore_source = html[restore_start:restore_end]
        build_start = html.index("function buildDOM(data) {")
        build_end = html.index("// ── Bootstrap: fetch papers.json", build_start)
        build_source = html[build_start:build_end]

        state_source = html[state_start:setter_start]
        self.assertIn("let HAS_RENDERED_STATS = false;", state_source)
        self.assertIn("let CATALOG_DATA_READY = false;", state_source)
        self.assertIn(
            "if (ACTIVE_TOP_LEVEL_TAB === 'stats' && !HAS_RENDERED_STATS) {\n"
            "    renderStatsPanel();\n"
            "  }",
            setter_source,
        )
        self.assertNotIn("typeof renderStatsPanel", setter_source)
        self.assertIn("setTopLevelTab(requestedTab, { updateHash: false });", restore_source)
        ready_index = build_source.index("CATALOG_DATA_READY = true;")
        reconcile_index = build_source.index("restoreTopLevelTabAfterCatalogLoad();")
        self.assertLess(ready_index, reconcile_index)
        self.assertNotIn("renderStatsPanel();", build_source)

    def test_stats_panel_reports_catalog_fetch_failure(self):
        """A rejected catalog request must replace the Stats loading message."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        state_start = html.index("let ALL_PAPERS = [];")
        state_end = html.index("let CURRENT_VIEW = 'list';", state_start)
        state_source = html[state_start:state_end]
        stats_start = html.index("function renderStatsPanel() {")
        stats_end = html.index("function escapeHtml(str) {", stats_start)
        stats_source = html[stats_start:stats_end]
        catch_start = html.index('.catch(function(err) {')
        catch_end = html.index("\n  });", catch_start)
        catch_source = html[catch_start:catch_end]

        self.assertIn("let CATALOG_DATA_ERROR = false;", state_source)
        self.assertIn("CATALOG_DATA_ERROR", stats_source)
        self.assertIn("Catalog data could not be loaded", stats_source)
        error_index = catch_source.index("CATALOG_DATA_ERROR = true;")
        reconcile_index = catch_source.index("restoreTopLevelTabAfterCatalogLoad();")
        self.assertLess(error_index, reconcile_index)
        self.assertNotIn("renderStatsPanel();", catch_source)
        self.assertIn("Failed to load resource data", catch_source)
        self.assertIn("if (!r.ok)", html)

    def test_timeline_tick_indices_keep_endpoints_without_collisions(self):
        """Tick selection must preserve first/last labels and enforce pixel spacing."""
        result = self.run_stats_series_helpers("""(function() {
  const plotWidth = 642;
  const minGap = 72;
  const indices = selectTimelineTickIndices(44, plotWidth, minGap);
  const positions = indices.map(function(index) { return (index + 0.5) * plotWidth / 44; });
  const gaps = positions.slice(1).map(function(position, index) {
    return position - positions[index];
  });
  return {
    indices: indices,
    first: indices[0],
    last: indices[indices.length - 1],
    minGap: Math.min.apply(null, gaps),
    singleton: selectTimelineTickIndices(1, 120, minGap),
    empty: selectTimelineTickIndices(0, 120, minGap)
  };
})()""")

        self.assertEqual(result["first"], 0)
        self.assertEqual(result["last"], 43)
        self.assertNotIn(42, result["indices"])
        self.assertGreaterEqual(result["minGap"], 72)
        self.assertEqual(result["singleton"], [0])
        self.assertEqual(result["empty"], [])

    def test_release_renderers_use_pixel_spaced_tick_helper(self):
        """Release Pulse x labels must use the shared collision-resistant selector."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        helper_start = html.index("function selectTimelineTickIndices(")
        helper_end = html.index("function renderReleasePulseChart(", helper_start)
        helper_source = html[helper_start:helper_end]
        render_start = helper_end
        render_end = html.index("function renderStatsPanel()", render_start)
        render_source = html[render_start:render_end]

        self.assertIn("minPixelGap", helper_source)
        self.assertIn("plotWidth", helper_source)
        self.assertIn("candidates", helper_source)
        self.assertIn("lastIndex", helper_source)
        self.assertIn("selectTimelineTickIndices", render_source)
        self.assertNotIn("index % xTickStep", render_source)

    def test_release_pulse_uses_one_shared_y_scale(self):
        """Bars and their trailing average must use the same papers-per-period scale."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        render_start = html.index("function renderReleasePulseChart(container, series, options) {")
        render_end = html.index("function renderStatsDistribution(", render_start)
        render_source = html[render_start:render_end]

        self.assertIn("var maxValue = Math.max", render_source)
        self.assertIn("count / maxValue * plotHeight", render_source)
        self.assertIn("average / maxValue * plotHeight", render_source)
        self.assertIn("Number(container.clientWidth)", render_source)
        self.assertIn("Number(container.clientHeight)", render_source)
        self.assertIn("niceStatsAxis(rawMax", render_source)
        self.assertNotIn("maxAverage", render_source)
        self.assertNotIn("timeline-axis-average", render_source)
        self.assertNotIn("Math.max(760", render_source)
        self.assertNotIn("scrollLeft", render_source)

    def test_stats_renderers_use_safe_accessible_inline_svg_and_dom(self):
        """Stats rendering must use safe DOM APIs, SVG text alternatives, and visible summaries."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        timeline_start = html.index("function renderReleasePulseChart(container, series, options) {")
        timeline_end = html.index("function renderStatsPanel() {", timeline_start)
        timeline_source = html[timeline_start:timeline_end]
        stats_start = timeline_end
        stats_end = html.index("function escapeHtml(str) {", stats_start)
        stats_source = html[stats_start:stats_end]

        for marker in (
            "createStatsSvgElement",
            "'title'",
            "'desc'",
            "'viewBox'",
            "timeline-grid",
            "timeline-bar",
            "timeline-line",
            "timeline-axis-count",
            "timeline-empty",
            "textContent",
            "renderStatsDistribution",
            "renderStatsActiveDirections",
        ):
            self.assertIn(marker, timeline_source)
        self.assertNotIn("renderStatsCategoryComposition", html)
        line_start = timeline_source.index("createStatsSvgElement('polyline'")
        line_end = timeline_source.index("}));", line_start)
        line_source = timeline_source[line_start:line_end]
        self.assertIn("setAttribute", timeline_source)
        self.assertIn("class: 'timeline-line'", line_source)
        self.assertIn("'pathLength': 1", line_source)
        self.assertNotIn("innerHTML", timeline_source)
        self.assertNotIn("innerHTML", stats_source)
        self.assertIn("buildDailyPublicationSeries(ALL_PAPERS)", stats_source)
        self.assertIn("buildMonthlyPublicationSeries(ALL_PAPERS)", stats_source)
        self.assertIn("buildStatsDistribution(ALL_PAPERS, '_primaryChapter', chapterLabels)", stats_source)
        self.assertIn("buildStatsDistribution(ALL_PAPERS, 'loop_topology'", stats_source)
        self.assertIn("anchorFor: function(row) { return getChapterDomId(row.key); }", stats_source)
        self.assertIn("{ facetGroup: 'loop_topology' }", stats_source)
        self.assertIn("renderStatsActiveDirections();", stats_source)
        self.assertIn("HAS_RENDERED_STATS = true;", stats_source)
        self.assertIn("if (!CATALOG_DATA_READY)", stats_source)
        self.assertIn("release-pulse-summary", html)
        self.assertIn("'title'", timeline_source)
        self.assertIn("'desc'", timeline_source)
        self.assertNotIn("renderLongArcChart", timeline_source)

    def test_stats_dashboard_omits_long_secondary_feeds(self):
        """The single-screen dashboard must not grow with tag or release feeds."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        for removed in (
            "stats-tag-explorer",
            "stats-tag-results",
            "renderStatsTagExplorer",
            "latest-releases-list",
            "latest-release-item",
            "renderLatestReleases",
            "getLatestReleasedPapers",
            "annual-volume",
            "buildAnnualReleaseSeries",
            "renderAnnualReleaseVolume",
            "stats-distribution-note",
            "stats-taxonomy-details",
            "stats-taxonomy-detail-grid",
        ):
            self.assertNotIn(removed, html)

    def test_stats_dashboard_uses_twelve_column_information_grid(self):
        """Stats CSS must use the approved compact 7/5 and 5/7 dashboard grid."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        stats_start = html.index("    /* ── Personal-site-aligned editorial system ── */")
        stats_end = html.index("  </style>", stats_start)
        stats_css = html[stats_start:stats_end]

        dashboard_start = stats_css.index("    .stats-dashboard-grid {")
        dashboard_end = stats_css.index("\n    }", dashboard_start)
        dashboard_rule = stats_css[dashboard_start:dashboard_end]
        reduced_motion_start = stats_css.rindex("    @media (prefers-reduced-motion: reduce)")
        bar_selector = "    .stats-primary-chart .timeline-bar {"
        bar_start = stats_css.rindex(bar_selector, 0, reduced_motion_start)
        bar_end = stats_css.index("\n    }", bar_start)
        bar_rule = stats_css[bar_start:bar_end]
        line_selector = "    .stats-primary-chart .timeline-line {"
        line_start = stats_css.rindex(line_selector, 0, reduced_motion_start)
        line_end = stats_css.index("\n    }", line_start)
        line_rule = stats_css[line_start:line_end]
        reduced_motion_end = stats_css.index(
            '    :where(html[data-theme="dark"])', reduced_motion_start
        )
        reduced_motion_css = stats_css[reduced_motion_start:reduced_motion_end]
        reduced_motion_selector = (
            "      .stats-primary-chart .timeline-bar,\n"
            "      .stats-primary-chart .timeline-line {"
        )
        reduced_motion_rule_start = reduced_motion_css.index(reduced_motion_selector)
        reduced_motion_rule_end = reduced_motion_css.index(
            "\n      }", reduced_motion_rule_start
        )
        reduced_motion_rule = reduced_motion_css[
            reduced_motion_rule_start:reduced_motion_rule_end
        ]

        self.assertIn("grid-template-columns: repeat(12, minmax(0, 1fr));", dashboard_rule)
        self.assertIn("align-items: start;", dashboard_rule)
        self.assertIn(".stats-pulse-card {\n      grid-column: 1 / -1;", stats_css)
        self.assertIn(
            ".stats-chapter-card,\n    .stats-topology-card,\n    .stats-directions-card {\n      grid-column: span 4;",
            stats_css,
        )
        self.assertNotIn(".stats-category-stack", stats_css)
        self.assertNotIn(".stats-category-donut", stats_css)
        self.assertNotIn(".stats-mechanism-card", stats_css)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr));", stats_css)
        self.assertIn("a.stats-distribution-row {\n      min-height: 0;", stats_css)
        chart_scroll_css = stats_css[stats_css.index("    .stats-chart-scroll {"):]
        self.assertIn("overflow: hidden;", chart_scroll_css)
        self.assertIn("height: clamp(220px, 27vh, 250px);", chart_scroll_css)
        self.assertIn("background: transparent;", stats_css)
        self.assertIn("border-top: 1px solid var(--border);", stats_css)
        self.assertNotIn("--stats-observatory", stats_css)
        self.assertIn(".stats-chart-tooltip", stats_css)
        self.assertIn("animation: stats-bar-rise", bar_rule)
        self.assertIn("stroke-dasharray: 1;", line_rule)
        self.assertIn("animation: stats-line-draw", line_rule)
        self.assertIn("@keyframes stats-bar-rise", stats_css)
        self.assertIn("@keyframes stats-line-draw", stats_css)
        self.assertIn(".stats-primary-chart .timeline-bar,", reduced_motion_rule)
        self.assertIn(".stats-primary-chart .timeline-line {", reduced_motion_rule)
        self.assertIn("animation: none;", reduced_motion_rule)
        self.assertIn("@media (max-width: 768px)", stats_css)
        self.assertIn("min-height: 44px;", stats_css)

    def test_stats_mobile_stacks_landscape_without_order_hacks(self):
        """Mobile Stats should stack naturally without reordering or horizontal overflow."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        stats_start = html.index("    /* ── Personal-site-aligned editorial system ── */")
        stats_end = html.index("  </style>", stats_start)
        stats_css = html[stats_start:stats_end]
        mobile_start = stats_css.index("    @media (max-width: 768px)")
        mobile_end = stats_css.index("    @media (max-width: 900px)", mobile_start)
        mobile_css = stats_css[mobile_start:mobile_end]
        chart_start = stats_css.index("    .stats-chart-scroll {")
        chart_end = stats_css.index("\n    }", chart_start)
        chart_rule = stats_css[chart_start:chart_end]

        self.assertIn(".stats-dashboard-grid {\n        display: block;", mobile_css)
        self.assertIn(
            ".stats-primary-chart .stats-range-button,\n"
            "      .stats-direction-tabs button {\n"
            "        flex: 1 1 0;\n"
            "        min-height: 44px;",
            mobile_css,
        )
        self.assertIn("overflow: hidden;", chart_rule)
        self.assertNotRegex(stats_css, r"(?m)^\s*order:\s*-1")

    def test_stats_uses_document_scroll_root_without_inner_clipping(self):
        """Stats overflow belongs to the document edge, never the middle main pane."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        stats_start = html.index("    /* ── Personal-site-aligned editorial system ── */")
        stats_end = html.index("  </style>", stats_start)
        stats_css = html[stats_start:stats_end]

        self.assertIn(
            "html:has(body.stats-mode),\n    html:has(body.briefing-mode),\n    body.stats-mode,\n    body.briefing-mode {",
            stats_css,
        )
        self.assertIn("height: auto;\n      min-height: 100%;", stats_css)
        self.assertIn("html:has(body.stats-mode), html:has(body.briefing-mode) {\n      overflow-y: auto;", stats_css)
        self.assertIn("body.stats-mode, body.briefing-mode {\n      min-height: 100vh;\n      overflow: visible;", stats_css)
        self.assertIn("min-height: calc(100vh - 61px);", stats_css)
        self.assertIn("body.stats-mode main, body.briefing-mode main {\n      height: auto;", stats_css)
        self.assertIn("overflow: visible;\n      overscroll-behavior: auto;", stats_css)
        self.assertNotIn("body.stats-mode main {\n        overflow: hidden;", stats_css)
        self.assertNotIn("scrollbar-gutter", stats_css)
        self.assertNotIn("body.stats-mode main::-webkit-scrollbar", stats_css)

        desktop_start = stats_css.index("@media (min-width: 1180px) and (min-height: 700px)")
        desktop_end = stats_css.index("@media (max-width: 1020px)", desktop_start)
        desktop_css = stats_css[desktop_start:desktop_end]
        self.assertIn("body.stats-mode .layout, body.briefing-mode .layout {\n        padding-top: 14px;", desktop_css)
        self.assertNotIn(".stats-metric-note {\n        display: none;", stats_css)

        footer_media_start = stats_css.index("@media (min-width: 1180px) and (min-height: 860px)")
        footer_media_end = stats_css.index("@media (max-width: 1020px)", footer_media_start)
        footer_media_css = stats_css[footer_media_start:footer_media_end]
        self.assertIn("body.stats-mode footer, body.briefing-mode footer {\n        display: none;", footer_media_css)
        self.assertNotIn(".stats-scope {\n        display: none;", stats_css)
        self.assertNotIn("body.stats-mode footer", stats_css[:footer_media_start])

    def test_stats_dashboard_refines_light_and_dark_theme_tokens(self):
        """Research Landscape must keep the same editorial grammar in dark mode."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        stats_start = html.index("    /* ── Personal-site-aligned editorial system ── */")
        stats_end = html.index("  </style>", stats_start)
        stats_css = html[stats_start:stats_end]

        self.assertIn("--stats-card-bg:", stats_css)
        self.assertIn("--stats-card-border:", stats_css)
        self.assertIn("--stats-track-bg:", stats_css)
        self.assertIn("--stats-data-1:", stats_css)
        dark_start = stats_css.index(':where(html[data-theme="dark"])')
        dark_source = stats_css[dark_start:]
        self.assertIn(".stats-panel", dark_source)
        self.assertIn("--stats-data-1:", dark_source)
        self.assertIn("background: transparent;", dark_source)
        self.assertNotIn("@media (prefers-color-scheme: dark)", html)
        desk_style = READING_DESK_CSS_PATH.read_text(encoding="utf-8")
        desk_script = READING_DESK_JS_PATH.read_text(encoding="utf-8")
        self.assertIn(':root[data-theme="dark"]', desk_style)
        self.assertIn("color-scheme: light;", desk_style)
        self.assertIn("color-scheme: dark;", desk_style)
        self.assertIn("document.documentElement.dataset.theme = readingDeskTheme", desk_script)
        self.assertNotIn("prefers-color-scheme", desk_script)

    def test_stats_small_text_uses_accessible_muted_color(self):
        """Small Stats labels must avoid the lower-contrast decorative text token."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        stats_start = html.index("    /* ── Personal-site-aligned editorial system ── */")
        stats_end = html.index("  </style>", stats_start)
        stats_css = html[stats_start:stats_end]
        note_start = stats_css.index("    .stats-metric-note {")
        note_end = stats_css.index("\n    }", note_start)
        note_rule = stats_css[note_start:note_end]
        ticks_start = stats_css.index("    .stats-panel .timeline-axis-label,")
        ticks_end = stats_css.index("\n    }", ticks_start)
        ticks_rule = stats_css[ticks_start:ticks_end]
        empty_selector = "    .stats-primary-chart .timeline-empty {"
        self.assertIn(empty_selector, stats_css)
        empty_start = stats_css.index(empty_selector)
        empty_end = stats_css.index("\n    }", empty_start)
        empty_rule = stats_css[empty_start:empty_end]

        self.assertIn("color: var(--text-muted);", note_rule)
        self.assertNotIn("var(--text-dim)", note_rule)
        self.assertIn("fill: var(--text-muted);", ticks_rule)
        self.assertNotIn("var(--text-dim)", ticks_rule)
        self.assertIn("color: var(--text-muted);", empty_rule)
        self.assertIn("border-color: var(--border);", empty_rule)

    def test_table_header_sort_buttons_exist_for_date_citations_and_stars_with_direction_controls(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('data-sort="date" onclick="setSort(\'date\')">&#128197; Date</button>', html)
        self.assertIn('<button class="sort-btn" data-sort="citations" onclick="setSort(\'citations\')">&#128218; Citations</button>', html)
        self.assertIn('<button class="sort-btn" data-sort="stars" onclick="setSort(\'stars\')">&#11088; GitHub Stars</button>', html)
        self.assertIn('class="sort-btn table-sort-btn" data-sort="date" onclick="setSort(\'date\')">Date</button>', html)
        self.assertIn('class="sort-btn table-sort-btn" data-sort="citations" onclick="setSort(\'citations\')">Citations</button>', html)
        self.assertIn('class="sort-btn table-sort-btn" data-sort="stars" onclick="setSort(\'stars\')">Stars</button>', html)
        self.assertIn('class="table-sort-direction-btn" data-sort="date"', html)
        self.assertIn('onclick="toggleSortDirection(\'date\')"', html)
        self.assertIn('class="table-sort-direction-btn" data-sort="citations"', html)
        self.assertIn('onclick="toggleSortDirection(\'citations\')"', html)
        self.assertIn('class="table-sort-direction-btn" data-sort="stars"', html)
        self.assertIn('onclick="toggleSortDirection(\'stars\')"', html)
        self.assertIn("let SORT_DIRECTIONS = {", html)
        self.assertIn("function getSortDirection(sortKey) {", html)
        self.assertIn("function toggleSortDirection(sortKey) {", html)
        self.assertIn("function updateSortButtons() {", html)

    def test_daily_watch_filters_include_code_and_comments_frontend_semantics(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("let HAS_CODE_ONLY = false;", html)
        self.assertIn("let HAS_COMMENTS_ONLY = false;", html)
        self.assertIn('<button type="button" class="sort-btn" id="has-code-toggle" aria-pressed="false" onclick="toggleHasCodeOnly()">w/ code</button>', html)
        self.assertIn('<button type="button" class="sort-btn" id="has-comments-toggle" aria-pressed="false" onclick="toggleHasCommentsOnly()">w/ comments</button>', html)
        self.assertIn("function matchHasCodeOnly(paper) {", html)
        matcher_start = html.index("function matchHasCodeOnly(paper) {")
        matcher_end = html.index("function paperMatchesActiveFilters", matcher_start)
        matcher_snippet = html[matcher_start:matcher_end]
        self.assertIn("paper.links && (paper.links.github || paper.links.hf)", matcher_snippet)
        self.assertNotIn("paper.links.project", matcher_snippet)
        self.assertIn("function paperHasCommunityComments(paper) {", html)
        self.assertIn("paper.community_comments || paper.comments || []", html)
        self.assertIn("function matchHasCommentsOnly(paper) {", html)
        self.assertIn("&& matchHasCodeOnly(paper)\n    && matchHasCommentsOnly(paper);", html)
        self.assertIn("setToggleButtonState('has-code-toggle', HAS_CODE_ONLY);", html)
        self.assertIn("setToggleButtonState('has-comments-toggle', HAS_COMMENTS_ONLY);", html)
        self.assertIn("labels.push('w/ code');", html)
        self.assertIn("labels.push('w/ comments');", html)

    def test_newly_arrived_filter_uses_latest_valid_added_date(self):
        """Only papers in the newest valid intake batch match while active."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        date_start = html.index("function normalizeDateInputValue(raw) {")
        date_end = html.index("function getPublicationDateFilter()", date_start)
        matcher_start = html.index("function matchNewlyArrivedOnly(paper) {")
        matcher_end = html.index("function matchHasCodeOnly(paper)", matcher_start)

        script = f"""
{html[date_start:date_end]}
let NEWLY_ARRIVED_ONLY = true;
const papers = [
  {{ entry_type: 'paper', added_date: '2026-09-01' }},
  {{ entry_type: 'paper', added_date: 'invalid' }},
  {{ entry_type: 'paper', added_date: '2026-09-03' }}
];
const blog = {{ entry_type: 'blog', added_date: '2026-09-03' }};
let LATEST_ADDED_DATE = getLatestAddedDateValue(papers);
{html[matcher_start:matcher_end]}
const active = papers.concat([blog]).map(matchNewlyArrivedOnly);
NEWLY_ARRIVED_ONLY = false;
process.stdout.write(JSON.stringify({{
  latest: LATEST_ADDED_DATE,
  active,
  inactive: matchNewlyArrivedOnly(blog)
}}));
"""
        output = subprocess.check_output(["node", "-e", script], text=True)
        self.assertEqual(json.loads(output), {
            "latest": "2026-09-03",
            "active": [False, False, True, False],
            "inactive": True,
        })

    def test_daily_watch_countdown_widget_and_schedule_logic_exist(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('<script src="assets/daily-watch-countdown.js"></script>', html)
        self.assertIn('id="daily-watch-countdown"', html)
        self.assertIn('id="daily-watch-countdown-value"', html)
        self.assertIn('id="daily-watch-countdown-meta"', html)
        self.assertIn("20:15 ET Sunday–Thursday", html)
        self.assertIn("DAILY_WATCH_COUNTDOWN.startDailyWatchCountdown();", html)
        self.assertIn("DAILY_WATCH_COUNTDOWN.updateDailyWatchCountdown();", html)
        self.assertIn(".daily-watch-countdown", html)

    def test_table_view_expanded_details_label_is_tldr(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('<div class="paper-table-detail-label">TL;DR</div>', html)
        self.assertNotIn('<div class="paper-table-detail-label">Summary</div>', html)

    def test_table_view_rows_use_full_publication_date_when_available(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("function getPaperDisplayDate(paper) {", html)
        self.assertIn("function getPaperSortDateValue(paper) {", html)
        self.assertIn("function comparePapersByDate(a, b, direction) {", html)
        helper_start = html.index("function getPaperDisplayDate(paper) {")
        helper_end = html.index("function comparePapersByDateDesc(a, b) {", helper_start)
        helper_snippet = html[helper_start:helper_end]
        self.assertIn("paper.published_date", helper_snippet)
        self.assertIn("? publishedDate", helper_snippet)
        self.assertNotIn("publishedDate.slice(0, 7)", helper_snippet)
        self.assertIn("paper.year ? String(paper.year) : ''", helper_snippet)
        self.assertNotIn("paper.added_date", helper_snippet)
        self.assertIn("formatTableText(getPaperDisplayDate(paper))", html)
        self.assertIn("direction === 'asc'", html)
        self.assertIn("bDate.localeCompare(aDate)", html)

    def test_card_view_entries_show_full_publication_date(self):
        """Cards show one publication date beside the authors, independent of detail state."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        desk = READING_DESK_JS_PATH.read_text(encoding="utf-8")
        render_start = html.index("function renderCard(paper, query) {")
        render_end = html.index("// ── State & Taxonomy", render_start)
        render_snippet = html[render_start:render_end]

        self.assertNotIn("desk-paper-footer", render_snippet)
        self.assertEqual(render_snippet.count("getPaperDisplayDate(paper)"), 1)
        self.assertIn("formatRowDate(publishedDate, false)", render_snippet)
        self.assertIn("formatRowDate(paper.added_date, true)", render_snippet)
        self.assertIn('class="paper-row-date paper-row-published"', render_snippet)
        self.assertIn('class="paper-row-date paper-row-added"', render_snippet)
        self.assertIn("<time>' + escapeHtml(getPaperDisplayDate(paper)) + '</time>'", desk)
        self.assertNotIn("paper.year", render_snippet)

    def test_paper_cards_keep_content_when_the_detail_column_changes(self):
        """The same full cards reflow with list width without conditional content hiding."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        desk = READING_DESK_JS_PATH.read_text(encoding="utf-8")
        style = READING_DESK_CSS_PATH.read_text(encoding="utf-8")
        self.assertIn('<body class="reading-desk">', html)
        self.assertIn('id="papers-panel" role="tabpanel" aria-labelledby="papers-tab" tabindex="0" data-card-density="compact"', html)
        self.assertNotIn("paper-density-toggle", html)
        self.assertNotIn("paper-density-compact", html)
        self.assertNotIn("paper-density-comfortable", html)
        self.assertNotIn("CURRENT_PAPER_DENSITY", html)
        self.assertNotIn("normalizePaperDensity", html)
        self.assertNotIn("applyPaperDensity", html)
        self.assertNotIn("setPaperDensity", html)
        self.assertNotIn("showComfortablePaperDensity", html)

        render_start = html.index("function renderCard(paper, query) {")
        render_end = html.index("// ── State & Taxonomy", render_start)
        render_snippet = html[render_start:render_end]
        self.assertIn('<article class="paper-card paper-row"', render_snippet)
        self.assertIn('class="desk-paper-select"', render_snippet)
        self.assertIn('aria-controls="paper-detail" aria-pressed="false"', render_snippet)
        self.assertIn('class="paper-row-thumb"', render_snippet)
        self.assertIn("highlightQuery(escapeHtml(formatCompactAuthors(paper)), query)", render_snippet)
        self.assertNotIn("desk-full-card", render_snippet)
        self.assertNotIn("desk-paper-footer", render_snippet)
        self.assertNotIn("desk-card-summary", render_snippet)
        self.assertIn('id="desk-show-details"', html)
        self.assertIn("const READING_DESK_COLLAPSE_WIDTH = 220;", desk)
        self.assertIn("wideList && readingDeskDetailCollapsed", desk)
        self.assertIn("setReadingDeskDetailCollapsed(false);", desk)
        self.assertIn('<dialog class="paper-detail" id="paper-detail" aria-labelledby="paper-detail-title">', html)
        detail_start = desk.index("function renderReadingDeskDetail(paper) {")
        detail_end = desk.index("function syncReadingDeskSelection(papers) {", detail_start)
        detail = desk[detail_start:detail_end]
        self.assertIn("<h3>Topic-map placement</h3>' + renderReadingDeskSurveyHtml(paper)", detail)
        self.assertIn("renderSurveyCoreBadgeHtml(paper)", detail)
        self.assertIn('<h3 id="desk-sources-title">Sources</h3>', detail)
        self.assertIn("renderPaperLinksHtml(paper, false)", detail)
        self.assertIn('<h3 id="desk-discussion-title">Discussion</h3>', detail)
        self.assertIn("renderCommunityCommentsHtml(paper, true)", detail)
        self.assertNotIn("Sources & discussion", detail)
        self.assertIn("escapeHtml(paper.desc", detail)
        self.assertNotIn(".slice(", detail)
        self.assertIn("dialog.show();", desk)
        self.assertIn("dialog.showModal();", desk)
        self.assertIn(".reading-desk #papers-panel .paper-card", style)
        self.assertNotIn("desk-full-card", style)
        self.assertNotRegex(style, r"\.desk-detail-collapsed[^{}]*\.paper-(?:card|title|meta)")
        self.assertIn("container: paper-list / inline-size;", style)
        self.assertIn("@container paper-list (max-width: 640px)", style)
        self.assertIn(".reading-desk #papers-panel .desk-list-links { display: flex; flex-wrap: wrap;", style)
        self.assertIn(".reading-desk .paper-detail .paper-chips { display: flex; flex-wrap: wrap;", style)
        self.assertNotIn("paper-tag", style)
        self.assertIn("@media (max-width: 1119px)", style)
        self.assertNotIn(".paper-density-toggle", style)
        self.assertNotIn(".paper-density-button", style)

    def test_footer_preserves_more_vertical_space_for_papers(self):
        """The persistent footer should remain a compact single-line information bar."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        style = html[html.index("<style>"):html.index("</style>")]
        footer_start = style.index("\n    footer {")
        footer_end = style.index("}", footer_start)
        footer_style = style[footer_start:footer_end]
        self.assertIn("padding: 10px 20px;", footer_style)
        self.assertIn("margin-top: 6px;", footer_style)

    def test_table_view_rows_keep_compact_link_rendering_hooks(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("function renderCompactPaperLinksHtml(paper)", html)
        self.assertIn("'<td class=\"paper-table-links-cell\">' + compactLinksHtml + '</td>'", html)
        self.assertIn("'<div class=\"paper-table-links\">' + linksHtml + '</div>'", html)

    def test_table_view_survey_sections_and_axes_use_filter_links(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        helper_start = html.index("function renderTableSectionHtml(paper) {")
        helper_end = html.index("function renderTableRow(paper, query) {", helper_start)
        helper = html[helper_start:helper_end]
        renderer_start = helper_end
        renderer_end = html.index("function renderTableView(query, papers) {", renderer_start)
        renderer = html[renderer_start:renderer_end]

        self.assertIn("renderSectionBadgeHtml(sectionId, index === 0, index > 0)", helper)
        self.assertIn("getVisibleAxisEntries(paper)", helper)
        self.assertIn("renderAxisChipHtml(entry)", helper)
        self.assertIn("renderTableSectionHtml(paper)", renderer)
        self.assertIn("renderTableAxesHtml(paper)", renderer)
        self.assertIn("paper._sectionLabel", renderer)
        self.assertNotIn("renderTableTagLinksHtml", html)

    def test_table_view_rows_use_button_disclosure_markup(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        renderer_start = html.index("function renderTableRow(paper, query) {")
        renderer_end = html.index("function renderTableView(query, papers) {", renderer_start)
        renderer = html[renderer_start:renderer_end]
        self.assertIn("const detailRowId = 'paper-table-detail-' + paperId;", html)
        self.assertIn('class="paper-table-disclosure"', html)
        self.assertIn("aria-controls=\"' + detailRowId + '\"", html)
        self.assertIn("id=\"' + detailRowId + '\"", html)
        self.assertNotIn('tabindex="0"', renderer)

    def test_table_view_toggle_ignores_interactive_children_and_syncs_button_state(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        guard = "event.target.closest('a, button, summary, input, select, textarea')"
        self.assertEqual(html.count(guard), 2)
        self.assertIn("const disclosureButton = summaryRow.querySelector('.paper-table-disclosure');", html)
        self.assertIn("if (disclosureButton) disclosureButton.setAttribute('aria-expanded', expanded ? 'true' : 'false');", html)

    def test_quick_filters_and_table_view_have_frontend_hooks(self):
        """Wire the newest-intake state through the existing filter hooks."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("if (paper.entry_type === 'blog') return false;", html)
        self.assertIn("if (paper.peer_reviewed != null) return paper.peer_reviewed === true;", html)
        self.assertIn("const venue = String(paper.venue || '').trim();", html)
        self.assertIn("let NEWLY_ARRIVED_ONLY = false;", html)
        self.assertIn("let LATEST_ADDED_DATE = '';", html)
        self.assertIn("function getLatestAddedDateValue(papers) {", html)
        self.assertIn("function matchNewlyArrivedOnly(paper) {", html)
        self.assertIn("LATEST_ADDED_DATE = getLatestAddedDateValue(ALL_PAPERS);", html)
        self.assertIn("function renderTableView(query, papers)", html)
        self.assertIn("function toggleTableRow(paperId)", html)
        self.assertIn("function setView(view)", html)
        for obsolete_name in (
            "TODAY_ONLY",
            "today-only-toggle",
            "matchTodayOnly",
            "toggleTodayOnly",
        ):
            self.assertNotIn(obsolete_name, html)
        self.assertNotIn("function getBrowserTodayString()", html)
        self.assertNotIn("function getRepoTodayString()", html)
        self.assertNotIn("let REPO_TODAY = '';", html)

    def test_mobile_compact_overrides_apply_after_base_control_styles(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        base_controls_index = html.index("/* ── Controls Bar (sort + year filter) ── */")

        self.assertIn("/* ── Mobile compact viewport overrides ── */", html)
        mobile_override_index = html.index("/* ── Mobile compact viewport overrides ── */")
        self.assertGreater(mobile_override_index, base_controls_index)

        mobile_override = html[mobile_override_index:]
        self.assertIn("@media (max-width: 768px)", mobile_override)
        self.assertIn("flex-wrap: nowrap;", mobile_override)
        self.assertIn("overflow-x: auto;", mobile_override)
        self.assertIn("position: static;", mobile_override)

    def test_mobile_directory_scroll_uses_window_when_main_is_not_scrollable(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        scroll_start = html.index("function scrollToSection(sectionId)")
        scroll_end = html.index("initReadingDesk();", scroll_start)
        scroll_snippet = html[scroll_start:scroll_end]

        self.assertIn("window.innerWidth <= 768", scroll_snippet)
        self.assertIn("window.scrollTo", scroll_snippet)
        self.assertIn("scrollRoot.scrollTo", scroll_snippet)

    def test_survey_nav_links_use_top_level_survey_anchor_navigation(self):
        """Chapter links must route through the tab/hash state machine before scrolling."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        init_start = html.index("function initSurveyNavInteractions() {")
        init_end = html.index("function observeSurveyChapters() {", init_start)
        init_source = html[init_start:init_end]

        self.assertIn("navigateToSurveyAnchor(getChapterDomId(link.dataset.chapter));", init_source)
        self.assertIn("event.preventDefault();", init_source)
        self.assertNotIn("scrollToSection(", init_source)
        self.assertNotIn("initTreeInteractions", html)
        self.assertNotIn("navigateToPaperSection", html)

    def test_search_count_is_not_table_view_only(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertNotIn("const shouldShowCount = hasActiveFilter || CURRENT_VIEW === 'table';", html)
        self.assertNotIn("shouldShowCount && total", html)
        self.assertIn("searchCount.textContent = total + ' result' + (total !== 1 ? 's' : '');", html)

    def test_custom_scrollbar_styles_are_subtle(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("--scrollbar-thumb:", html)
        self.assertIn("--scrollbar-thumb-hover:", html)
        self.assertIn("--scrollbar-track:", html)
        self.assertIn("main,", html)
        self.assertIn(".sidebar,", html)
        self.assertIn("scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);", html)
        self.assertIn("::-webkit-scrollbar-thumb", html)
        self.assertIn("background: var(--scrollbar-thumb);", html)


class DailyWatchCountdownLogicTests(unittest.TestCase):
    def run_daily_watch_helper(self, now_iso: str):
        script = f"""
const helper = require({json.dumps(str(DAILY_WATCH_COUNTDOWN_JS_PATH))});
const result = helper.computeNextDailyWatchRun(new Date({json.dumps(now_iso)}));
process.stdout.write(JSON.stringify({{
  iso: result.date.toISOString(),
  weekday: result.weekday,
  label: helper.formatDailyWatchRunLabel(result)
}}));
"""
        output = subprocess.check_output(["node", "-e", script], text=True)
        return json.loads(output)

    def test_daily_watch_helper_exists(self):
        self.assertTrue(DAILY_WATCH_COUNTDOWN_JS_PATH.exists())

    def test_daily_watch_helper_keeps_same_day_fetch_before_cutoff(self):
        result = self.run_daily_watch_helper("2026-04-23T12:00:00-04:00")
        self.assertEqual(result["iso"], "2026-04-24T00:15:00.000Z")
        self.assertEqual(result["weekday"], 4)
        self.assertEqual(result["label"], "Thu 20:15 ET")

    def test_daily_watch_helper_rolls_thursday_night_to_sunday(self):
        result = self.run_daily_watch_helper("2026-04-23T21:00:00-04:00")
        self.assertEqual(result["iso"], "2026-04-27T00:15:00.000Z")
        self.assertEqual(result["weekday"], 0)
        self.assertEqual(result["label"], "Sun 20:15 ET")

    def test_daily_watch_helper_handles_standard_time_offset(self):
        result = self.run_daily_watch_helper("2026-01-05T12:00:00-05:00")
        self.assertEqual(result["iso"], "2026-01-06T01:15:00.000Z")
        self.assertEqual(result["weekday"], 1)
        self.assertEqual(result["label"], "Mon 20:15 ET")


class CanonicalPaperMetadataTests(unittest.TestCase):
    def test_full_bandwidth_transformer_is_retained_as_adjacent_work(self):
        paper_path = REPO_ROOT / "papers" / "2608.08888.yaml"
        data = yaml.safe_load(paper_path.read_text(encoding="utf-8")) or {}

        self.assertEqual(data.get("catalog_fit"), "adjacent")
        self.assertEqual(data.get("survey_section", [])[0], "architecture/topology")
        self.assertEqual(data.get("loop_topology"), "shifted-parallel")

    def test_paper_2602_10520_is_placed_in_post_training(self):
        paper_path = REPO_ROOT / "papers" / "2602.10520.yaml"
        data = yaml.safe_load(paper_path.read_text(encoding="utf-8")) or {}

        self.assertEqual(data.get("survey_section"), ["training/post-training"])
        for field in build.RETIRED_FIELDS:
            self.assertNotIn(field, data)

    def test_all_repo_paper_yaml_files_use_the_survey_schema(self):
        violations = []
        for yaml_path in sorted((REPO_ROOT / "papers").glob("*.yaml")):
            if yaml_path.name.startswith("_"):
                continue
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            retired = [field for field in (*build.RETIRED_FIELDS, "family_tags") if field in data]
            if retired:
                violations.append(f"{yaml_path.name}: retired fields {retired}")
            try:
                build.normalize_paper_taxonomy_fields({k: v for k, v in data.items() if k not in retired}, yaml_path.name)
                build.normalize_survey_fields(data, yaml_path.name, build.REQUIRED_PAPER_SURVEY_FIELDS)
            except ValueError as exc:
                violations.append(str(exc))

        self.assertEqual(violations, [])

    def test_all_repo_paper_yaml_files_have_publication_dates(self):
        violations = []
        for yaml_path in sorted((REPO_ROOT / "papers").glob("*.yaml")):
            if yaml_path.name.startswith("_"):
                continue
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            published_date = data.get("published_date")
            if published_date in (None, ""):
                violations.append(f"{yaml_path.name}: missing published_date")
                continue
            try:
                build.normalize_optional_date_string(published_date, "published_date", yaml_path.name)
            except ValueError as exc:
                violations.append(str(exc))

        self.assertEqual(violations, [])

    def test_all_repo_paper_yaml_files_have_intake_dates(self):
        """Require every canonical paper source to record a valid catalog intake date."""
        violations = []
        for paper_path in sorted((REPO_ROOT / "papers").glob("*.yaml")):
            if paper_path.name.startswith("_"):
                continue
            data = yaml.safe_load(paper_path.read_text(encoding="utf-8")) or {}
            try:
                build.normalize_required_date_string(data.get("added_date"), "added_date", paper_path.name)
            except ValueError as exc:
                violations.append(str(exc))

        self.assertEqual(violations, [])

    def test_all_repo_blog_yaml_files_have_publication_dates_and_only_survey_sections(self):
        violations = []
        for yaml_path in sorted((REPO_ROOT / "blogs").glob("*.yaml")):
            if yaml_path.name.startswith("_"):
                continue
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            published_date = data.get("published_date")
            if published_date in (None, ""):
                violations.append(f"{yaml_path.name}: missing published_date")
            else:
                try:
                    build.normalize_optional_date_string(published_date, "published_date", yaml_path.name)
                except ValueError as exc:
                    violations.append(str(exc))
            for field in (*build.RETIRED_FIELDS, "family_tags"):
                if field in data:
                    violations.append(f"{yaml_path.name}: blogs must not set {field}")
            for field in build.SURVEY_FIELDS:
                if field != "survey_section" and field in data:
                    violations.append(f"{yaml_path.name}: blogs must not set {field}")
            try:
                build.normalize_survey_fields(data, yaml_path.name, ("survey_section",))
            except ValueError as exc:
                violations.append(str(exc))
            links = data.get("links") or {}
            if not links.get("blog"):
                violations.append(f"{yaml_path.name}: blogs must set links.blog")

        self.assertEqual(violations, [])


class ReadmeRenderingTests(unittest.TestCase):
    def test_readme_paper_entries_prefix_summary_title_with_publication_date(self):
        paper = {
            "title": "Dated Loop Paper",
            "authors": "Alice Example",
            "venue": "ICLR",
            "year": 2026,
            "published_date": "2026-04-26",
            "links": {},
        }

        markdown = build._paper_to_md(paper)

        self.assertIn("<summary>[04/26/2026] <strong>Dated Loop Paper</strong>", markdown)

    def _render_front_page(self, papers, blogs=()):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            header_path = tmp_path / "README_HEADER.md"
            footer_path = tmp_path / "README_FOOTER.md"
            readme_path = tmp_path / "README.md"
            header_path.write_text("# Test README", encoding="utf-8")
            footer_path.write_text("Footer", encoding="utf-8")

            with patch.object(build, "HEADER_FILE", header_path), \
                 patch.object(build, "FOOTER_FILE", footer_path), \
                 patch.object(build, "README_OUT", readme_path):
                build.build_readme(list(papers), list(blogs), {"public_pages_base": "https://example.test/repo"})

            return readme_path.read_text(encoding="utf-8")

    def test_build_readme_front_page_lists_anchors_latest_and_most_cited(self):
        papers = [
            {
                "title": "Older Survey Core Loop Paper",
                "venue": "ICLR",
                "year": 2019,
                "published_date": "2019-01-01",
                "added_date": "2026-04-24",
                **survey_fields(survey_section=["foundations/depth-sharing", "architecture/topology"], loop_topology="whole-stack"),
                "survey_core": True,
                "citations": 500,
                "links": {"arxiv": "https://arxiv.org/abs/1901.00001"},
            },
            {
                "title": "Newest Loop Paper",
                "venue": "arXiv",
                "year": 2026,
                "published_date": "2026-04-26",
                "added_date": "2026-09-27",
                **survey_fields(survey_section=["scaling/test-time"]),
                "github_stars": 1234,
                "links": {
                    "arxiv": "https://arxiv.org/abs/2604.00002",
                    "github": "https://github.com/example/newest",
                },
            },
            {
                "title": "Middle Must-Read Loop Paper",
                "venue": "ICLR",
                "year": 2026,
                "published_date": "2026-02-03",
                "added_date": "2026-09-20",
                **survey_fields(survey_section=["architecture/topology"], loop_topology="partial"),
                "must_read": True,
                "citations": 7,
                "links": {"arxiv": "https://arxiv.org/abs/2602.00003"},
            },
        ]

        readme = self._render_front_page(papers)

        self.assertIn(
            f"<b>3 papers</b> · {len(build.SURVEY_SECTIONS)} sections · "
            '<a href="https://example.test/repo/index.html">browse all →</a>',
            readme,
        )
        for retired in ("analysis", "designs", "applications", "Foundation"):
            self.assertNotIn(f" {retired} ", readme)

        start_here = readme[readme.index("## 🌟 Start here"):readme.index("## 🆕 Latest additions")]
        self.assertIn("| Paper | Venue | Loop | Links |", start_here)
        self.assertLess(start_here.index("Older Survey Core Loop Paper"), start_here.index("Middle Must-Read Loop Paper"))
        self.assertIn("| <b>Older Survey Core Loop Paper</b> | ICLR 2019 | whole-stack |", start_here)
        self.assertIn("| 🌟 <b>Middle Must-Read Loop Paper</b> | ICLR 2026 | partial |", start_here)
        self.assertNotIn("Newest Loop Paper", start_here)

        latest = readme[readme.index("## 🆕 Latest additions"):readme.index("## 🔥 Most cited")]
        self.assertIn("| Added | Paper | § | Links |", latest)
        self.assertLess(latest.index("Newest Loop Paper"), latest.index("Middle Must-Read Loop Paper"))
        self.assertLess(latest.index("Middle Must-Read Loop Paper"), latest.index("Older Survey Core Loop Paper"))
        self.assertIn("| 2026-09-27 | <b>Newest Loop Paper</b> | §6.2 |", latest)
        self.assertIn("| 2026-04-24 | <b>Older Survey Core Loop Paper</b> | §2.2 |", latest)
        self.assertIn('<a href="https://github.com/example/newest">Code ★1,234</a>', latest)

        most_cited = readme[readme.index("## 🔥 Most cited"):]
        self.assertLess(most_cited.index("Older Survey Core Loop Paper"), most_cited.index("Middle Must-Read Loop Paper"))
        self.assertNotIn("Newest Loop Paper", most_cited)

        self.assertEqual(readme.count("<details>"), 1)
        self.assertNotIn("## Table of Contents", readme)

    def test_build_readme_survey_map_counts_primary_and_any_placement(self):
        papers = [
            {"title": "A", "year": 2026, "links": {}, **survey_fields(survey_section=["architecture/topology", "scaling/test-time"])},
            {"title": "B", "year": 2026, "links": {}, **survey_fields(survey_section=["scaling/test-time"])},
            {"title": "C", "year": 2026, "links": {}, **survey_fields(survey_section=["architecture/topology"])},
        ]
        blogs = [
            {
                "title": "Blog", "entry_type": "blog", "venue": "Blog", "published_date": "2026-01-01",
                "survey_section": ["understanding/why"], "links": {"blog": "https://example.com/post"},
            }
        ]
        readme = self._render_front_page(papers, blogs)
        survey_map = readme[readme.index("## 🗺️ Topic map"):readme.index("## 🌟 Start here") if "## 🌟 Start here" in readme else readme.index("## 🆕 Latest additions")]

        self.assertLess(readme.index("## At a glance"), readme.index("## 🗺️ Topic map"))
        self.assertIn("<summary>Papers per section</summary>", survey_map)
        self.assertIn("| § | Section | Primary | Any |", survey_map)
        self.assertIn("| §4.1 | Architecture and Design › Loop topology | 2 | 2 |", survey_map)
        self.assertIn("| §6.2 | Scaling Laws › Test-time scaling | 1 | 2 |", survey_map)
        self.assertIn("| §2.1 | From Recurrent Computation to Iterative Depth › Recurrent networks and weight sharing across computation | 0 | 0 |", survey_map)
        self.assertIn("| §8.1 | Understanding Why Looped Models Work › Why looped models work | 0 | 0 |", survey_map)
        rows = [line for line in survey_map.splitlines() if line.startswith("| §") and not line.startswith("| § |")]
        self.assertEqual([row.split(" | ")[0][2:] for row in rows], [f"§{n}" for _, n, _ in build.SURVEY_SECTIONS])
        self.assertIn("<b>1 blogs</b>", readme)
        self.assertNotIn("## 🌟 Start here", readme)

    def test_build_readme_front_page_escapes_table_cells(self):
        readme = self._render_front_page(
            [
                {
                    "title": "Pipes | and <tags>",
                    "year": 2026,
                    "published_date": "2026-01-01",
                    "added_date": "2026-01-02",
                    **survey_fields(survey_section=["architecture/hybrid"], loop_topology="partial"),
                    "survey_core": True,
                    "links": {},
                }
            ]
        )
        self.assertIn("<b>Pipes &#124; and &lt;tags&gt;</b>", readme)
        self.assertIn("| 2026-01-02 | <b>Pipes &#124; and &lt;tags&gt;</b> | §4.6 |", readme)
        self.assertIn("| §4.6 | Architecture and Design › Hybrid looped architectures | 1 | 1 |", readme)

    def test_readme_paper_entries_hide_summary_tags_and_use_badge_links(self):
        paper = {
            "title": "Loop Test Paper",
            "authors": "Alice Example, Bob Example",
            "venue": "ICLR",
            "year": 2026,
            "desc": "Introduces a compact loop-model benchmark entry.",
            **survey_fields(),
            "links": {
                "arxiv": "https://arxiv.org/abs/2604.00000",
                "alphaxiv": "https://www.alphaxiv.org/abs/2604.00000",
                "github": "https://github.com/example/repo",
                "hf": "https://huggingface.co/example/model",
                "openreview": "https://openreview.net/forum?id=abc123",
                "project": "https://worldmodels.github.io/",
                "twitter": "https://x.com/example/status/1",
                "readme": "https://github.com/example/repo#readme",
            },
        }

        markdown = build._paper_to_md(paper)
        details_start = markdown.index("<details>")
        summary_start = markdown.index("<summary>")
        summary_end = markdown.index("</summary>")
        summary_html = markdown[summary_start:summary_end]

        self.assertTrue(markdown.startswith("<details>"))
        self.assertNotIn("- <details>", markdown)
        self.assertIn("<summary><strong>Loop Test Paper</strong>", markdown)
        self.assertNotIn("<code>", summary_html)
        self.assertNotIn("§", summary_html)
        self.assertNotIn("<summary>Expand details</summary>", markdown)
        self.assertNotIn("<summary>Expand details</summary>\n\n", markdown)
        self.assertNotIn("<br>\n  <details>", markdown)
        self.assertNotIn("- **[Loop Test Paper]", markdown)
        self.assertLess(details_start, summary_start)
        self.assertLess(summary_start, summary_end)
        self.assertIn('<img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.00000-b31b1b.svg">', markdown)
        self.assertEqual(markdown.count('https://img.shields.io/badge/arXiv-2604.00000-b31b1b.svg'), 1)
        self.assertEqual(markdown.count('https://img.shields.io/github/stars/example/repo?style=social'), 1)
        self.assertIn(
            '<a href="https://arxiv.org/abs/2604.00000"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.00000-b31b1b.svg"></a>',
            markdown,
        )
        self.assertIn(
            '<a href="https://github.com/example/repo/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/example/repo?style=social"></a>',
            markdown,
        )
        self.assertNotIn("img.shields.io/badge/Code", markdown)
        self.assertNotIn("img.shields.io/badge/Project", markdown)
        self.assertNotIn("img.shields.io/badge/GitHub-", markdown)
        self.assertGreater(markdown.index("Alice Example, Bob Example"), summary_end)
        self.assertGreater(markdown.index("Introduces a compact loop-model benchmark entry."), summary_end)
        self.assertIn("<div><strong>Authors:</strong> Alice Example, Bob Example · ICLR 2026</div>", markdown)
        self.assertIn(
            "<div><strong>Sections:</strong> §4.1 Loop topology · §6.2 Test-time scaling</div>",
            markdown,
        )
        self.assertIn(
            "<div><strong>Design:</strong> Loop topology: prelude-core-coda · Sharing: full · Depth control: sampled-train</div>",
            markdown,
        )
        for retired in ("Loop Mechanism:", "Focus:", "Domains:", "Foundation"):
            self.assertNotIn(retired, markdown)
        self.assertIn("<div><strong>TL;DR:</strong> Introduces a compact loop-model benchmark entry.</div>", markdown)

    def test_readme_marks_adjacent_work_and_explains_the_scope_boundary(self):
        markdown = build._paper_to_md(
            {
                "title": "Adjacent Recurrent Paper",
                "authors": "Alice Example",
                "venue": "arXiv",
                "year": 2026,
                "catalog_fit": "adjacent",
                "links": {"arxiv": "https://arxiv.org/abs/2604.00001"},
            }
        )

        self.assertIn("⚠️ Adjacent work", markdown)
        self.assertIn("<strong>Catalog fit:</strong>", markdown)
        self.assertIn("outside the strict single-forward loop-model scope", markdown)

    def test_must_read_paper_entries_prepend_star_in_summary(self):
        paper = {
            "title": "Must Read Loop Paper",
            "authors": "Alice Example",
            "venue": "ICLR",
            "year": 2026,
            "must_read": True,
            "links": {
                "arxiv": "https://arxiv.org/abs/2604.11111",
            },
        }

        markdown = build._paper_to_md(paper)

        self.assertIn("<summary>🌟 <strong>Must Read Loop Paper</strong>", markdown)

    def test_readme_blog_entries_list_survey_sections_without_design_axes(self):
        blog = {
            "title": "Loop Blog",
            "authors": "Alice Example",
            "venue": "Blog",
            "year": 2026,
            "entry_type": "blog",
            "desc": "Long-form note on loop-model training.",
            "survey_section": ["training/supervision-optimization", "systems/kv-memory"],
            "links": {
                "blog": "https://example.com/loop-blog",
            },
        }

        markdown = build._paper_to_md(blog)
        summary_start = markdown.index("<summary>")
        summary_end = markdown.index("</summary>")
        summary_html = markdown[summary_start:summary_end]

        self.assertIn("<summary><strong>Loop Blog</strong>", markdown)
        self.assertNotIn("§", summary_html)
        self.assertIn(
            "<div><strong>Sections:</strong> §5.1 Supervision, credit assignment, and loop-specific optimization"
            " · §7.2 KV cache and memory</div>",
            markdown,
        )
        self.assertNotIn("<strong>Design:</strong>", markdown)
        self.assertIn("<div><strong>TL;DR:</strong> Long-form note on loop-model training.</div>", markdown)
        self.assertIn(
            '<a href="https://example.com/loop-blog"><img alt="Blog" src="https://img.shields.io/badge/Blog-example.com-0ea5e9.svg"></a>',
            markdown,
        )

    def test_render_link_badge_uses_openreview_style_for_openreview_pdf_links(self):
        badge = build.render_link_badge("paper", "https://openreview.net/pdf?id=BZ5a1r-kVsf")

        self.assertEqual(
            badge,
            "[![OpenReview](https://img.shields.io/badge/OpenReview-Paper-8E44AD.svg)](https://openreview.net/pdf?id=BZ5a1r-kVsf)",
        )

    def test_render_link_badge_uses_website_label_for_project_links(self):
        badge = build.render_link_badge("project", "https://worldmodels.github.io/")

        self.assertEqual(
            badge,
            "[![Website](https://img.shields.io/badge/Website-Link-blue)](https://worldmodels.github.io/)",
        )

    def test_render_link_badge_uses_github_social_stars_style_and_stargazers_target(self):
        badge = build.render_link_badge("github", "https://github.com/knightnemo/Awesome-World-Models")

        self.assertEqual(
            badge,
            "[![GitHub stars](https://img.shields.io/github/stars/knightnemo/Awesome-World-Models?style=social)](https://github.com/knightnemo/Awesome-World-Models/stargazers)",
        )


def write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def paper_yaml(**overrides) -> dict:
    """Return a minimal valid paper YAML mapping using the survey schema."""
    data = {
        "title": "Loop Test Paper",
        "authors": ["Test Author"],
        "year": 2026,
        "published_date": "2026-03-10",
        "venue": "arXiv",
        **survey_fields(),
        "links": {"arxiv": "https://arxiv.org/abs/2603.08391"},
    }
    data.update(overrides)
    return {key: value for key, value in data.items() if value is not ...}


def blog_yaml(**overrides) -> dict:
    """Return a minimal valid blog YAML mapping."""
    data = {
        "title": "Loop Blog",
        "authors": ["Test Author"],
        "year": 2026,
        "published_date": "2026-04-21",
        "venue": "X Article",
        "survey_section": ["understanding/why", "architecture/topology"],
        "links": {"blog": "https://example.com/loop-blog"},
    }
    data.update(overrides)
    return {key: value for key, value in data.items() if value is not ...}


class LoadPapersRegressionTests(unittest.TestCase):
    def load(self, data: dict, name: str = "2603.08391.yaml") -> list[dict]:
        with TemporaryDirectory() as tmpdir:
            papers_dir = Path(tmpdir)
            write_yaml(papers_dir / name, data)
            with patch.object(build, "PAPERS_DIR", papers_dir):
                return build.load_papers()

    def test_load_papers_rejects_every_retired_taxonomy_field(self):
        for field, value in (
            ("category", "designs"),
            ("category_path", ["x"]),
            ("subcategory", "x"),
            ("foundation", True),
            ("mechanism_tags", ["flat-loop"]),
            ("focus_tags", ["architecture"]),
            ("domain_tags", ["reasoning"]),
            ("tags", ["DEQ"]),
            ("family_tags", ["deep-equilibrium"]),
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, f"2603.08391.yaml: {field} no longer exist"):
                    self.load(paper_yaml(**{field: value}))

    def test_load_papers_requires_every_survey_field(self):
        for field in build.REQUIRED_PAPER_SURVEY_FIELDS:
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, f"missing required {field}"):
                    self.load(paper_yaml(**{field: ...}))

    def test_load_papers_rejects_values_outside_the_survey_vocabulary(self):
        for overrides in (
            {"survey_section": ["design/topology"]},
            {"survey_section": []},
            {"loop_topology": "flat-loop"},
            {"sharing": "tied"},
            {"depth_control": "dynamic"},
            {"claims": ["speed"]},
            {"comparison": ["iso-time"]},
            {"survey_core": "yes"},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.load(paper_yaml(**overrides))

    def test_load_papers_normalizes_survey_fields(self):
        papers = self.load(paper_yaml(
            survey_section=["scaling/test-time", "architecture/topology", "scaling/test-time"],
            claims="stability",
            comparison=[],
            survey_core=True,
        ))
        paper = papers[0]
        self.assertEqual(paper["survey_section"], ["scaling/test-time", "architecture/topology"])
        self.assertEqual(paper["claims"], ["stability"])
        self.assertEqual(paper["comparison"], [])
        self.assertIs(paper["survey_core"], True)
        self.assertEqual(paper["loop_topology"], "prelude-core-coda")
        self.assertEqual(paper["entry_type"], "paper")
        self.assertNotIn("catalog_fit", paper)
        for field in build.RETIRED_FIELDS:
            self.assertNotIn(field, paper)
        self.assertNotIn("survey_core", self.load(paper_yaml())[0])

    def test_load_papers_keeps_adjacent_catalog_fit_with_full_survey_fields(self):
        papers = self.load(paper_yaml(catalog_fit="adjacent", loop_topology="shifted-parallel"))
        self.assertEqual(papers[0]["catalog_fit"], "adjacent")
        self.assertEqual(papers[0]["loop_topology"], "shifted-parallel")
        with self.assertRaisesRegex(ValueError, "missing required loop_topology"):
            self.load(paper_yaml(catalog_fit="adjacent", loop_topology=...))
        with self.assertRaisesRegex(ValueError, "invalid catalog_fit"):
            self.load(paper_yaml(catalog_fit="borderline"))

    def test_load_papers_derives_alphaxiv_from_arxiv_links(self):
        papers = self.load(paper_yaml(authors=...))

        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["links"]["alphaxiv"], "https://www.alphaxiv.org/abs/2603.08391")
        self.assertEqual(papers[0]["arxiv_id"], "2603.08391")

    def test_load_papers_requires_published_date(self):
        with self.assertRaisesRegex(ValueError, "missing required published_date"):
            self.load(paper_yaml(published_date=...))

    def test_load_papers_requires_a_primary_source_link(self):
        with self.assertRaisesRegex(ValueError, "at least one of links.arxiv, links.paper, or links.openreview"):
            self.load(paper_yaml(links={"github": "https://github.com/example/repo"}))

    def test_load_papers_preserves_must_read_flag(self):
        papers = self.load(paper_yaml(must_read=True))

        self.assertEqual(len(papers), 1)
        self.assertTrue(papers[0].get("must_read"))
        self.assertNotIn("must_read", self.load(paper_yaml(must_read=False))[0])

    def test_load_papers_normalizes_comment_links(self):
        papers = self.load(paper_yaml(links={
            "arxiv": "https://arxiv.org/abs/2603.08391",
            "comment": [{"label": "Thread", "url": "https://x.com/a"}, "https://example.com/b"],
        }))
        self.assertEqual(
            papers[0]["community_comments"],
            [{"label": "Thread", "url": "https://x.com/a"}, {"label": "Comment 2", "url": "https://example.com/b"}],
        )
        self.assertNotIn("comment", papers[0]["links"])


class LoadBlogsRegressionTests(unittest.TestCase):
    def load(self, data: dict) -> list[dict]:
        with TemporaryDirectory() as tmpdir:
            blogs_dir = Path(tmpdir)
            write_yaml(blogs_dir / "2026-04-21-loop-blog.yaml", data)
            with patch.object(build, "BLOGS_DIR", blogs_dir):
                return build.load_blogs()

    def test_load_blogs_requires_links_blog(self):
        with self.assertRaisesRegex(ValueError, "blogs require links.blog"):
            self.load(blog_yaml(links={}))

    def test_load_blogs_requires_survey_section(self):
        with self.assertRaisesRegex(ValueError, "missing required survey_section"):
            self.load(blog_yaml(survey_section=...))
        with self.assertRaisesRegex(ValueError, "invalid survey_section"):
            self.load(blog_yaml(survey_section=["design/topology"]))

    def test_load_blogs_reject_retired_fields(self):
        for field in (*build.RETIRED_FIELDS, "family_tags"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, f"{field} no longer exist"):
                    self.load(blog_yaml(**{field: ["x"]}))

    def test_load_blogs_reject_paper_design_axes(self):
        for field, value in (
            ("loop_topology", "partial"),
            ("sharing", "full"),
            ("depth_control", "fixed"),
            ("claims", ["stability"]),
            ("comparison", []),
            ("survey_core", True),
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, f"blogs only use survey_section, not {field}"):
                    self.load(blog_yaml(**{field: value}))

    def test_load_blogs_preserves_flat_blog_metadata(self):
        blogs = self.load(blog_yaml())

        self.assertEqual(len(blogs), 1)
        self.assertEqual(blogs[0]["entry_type"], "blog")
        self.assertEqual(blogs[0]["links"]["blog"], "https://example.com/loop-blog")
        self.assertEqual(blogs[0]["venueClass"], build.BLOG_VENUE_CLASS)
        self.assertEqual(blogs[0]["survey_section"], ["understanding/why", "architecture/topology"])
        self.assertEqual(blogs[0]["source_path"], "blogs/2026-04-21-loop-blog.yaml")
        for field in (*build.RETIRED_FIELDS, "loop_topology", "sharing", "depth_control", "claims", "comparison"):
            self.assertNotIn(field, blogs[0])


class TagsReferenceRegressionTests(unittest.TestCase):
    def render(self):
        papers = [
            {**survey_fields(survey_section=["architecture/topology", "scaling/test-time"]), "claims": ["stability", "expressivity"]},
            {**survey_fields(survey_section=["scaling/test-time"], loop_topology="partial"), "comparison": []},
        ]
        blogs = [{"survey_section": ["architecture/topology"]}]
        return build.render_tags_reference_text(papers, blogs)

    def test_render_tags_reference_lists_sections_by_part_and_chapter_with_counts(self):
        text = self.render()

        self.assertTrue(text.startswith("# Taxonomy vocabulary\n"))
        self.assertIn("There are no free-form tags", text)
        self.assertIn("## Taxonomy sections (`survey_section`)", text)
        self.assertIn("Counts are primary / any.", text)
        self.assertIn("- `architecture/topology` — §4.1 Loop topology (2 / 2)", text)
        self.assertIn("- `scaling/test-time` — §6.2 Test-time scaling (1 / 2)", text)
        self.assertIn("- `foundations/recurrence` — §2.1 Recurrent networks and weight sharing across computation (0 / 0)", text)
        for section_id, number, _ in build.SURVEY_SECTIONS:
            self.assertEqual(text.count(f"- `{section_id}` — §{number} "), 1)

        order = [
            "### Part I. Foundations",
            "**§2 From Recurrent Computation to Iterative Depth**",
            "- `foundations/recurrence`",
            "### Part II. What Looping Buys",
            "**§3 Capabilities, Benefits and Trade-offs**",
            "### Part III. Building, Training and Deploying",
            "**§4 Architecture and Design**",
            "- `architecture/topology`",
            "**§5 Learning Algorithms**",
            "**§6 Scaling Laws**",
            "- `scaling/test-time`",
            "**§7 Systems and Infrastructure**",
            "### Part IV. Understanding and Applications",
            "**§8 Understanding Why Looped Models Work**",
            "**§9 Applications**",
            "### Part V. Open Problems",
            "**§10 Open Problems**",
            "- `open-problems/monitorability-safety`",
            "## Loop topology (`loop_topology`)",
        ]
        positions = [text.index(marker) for marker in order]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(text.count("### Part "), len(build.SURVEY_PARTS))
        self.assertEqual(text.count("**§"), len(build.SURVEY_CHAPTERS))

    def test_render_tags_reference_lists_every_axis_value_with_paper_counts(self):
        text = self.render()
        for field, label in build.AXIS_LABELS.items():
            self.assertIn(f"## {label} (`{field}`)", text)
        self.assertIn("- `prelude-core-coda` (1)", text)
        self.assertIn("- `partial` (1)", text)
        self.assertIn("- `implicit-fixed-point` (0)", text)
        self.assertIn("- `full` (2)", text)
        self.assertIn("- `sampled-train` (2)", text)
        self.assertIn("- `stability` (1)", text)
        self.assertIn("- `test-time-scaling` (1)", text)
        self.assertIn("- `iso-param` (1)", text)
        self.assertIn("- `unclear` (0)", text)
        self.assertTrue(text.endswith("\n"))
        self.assertFalse(text.endswith("\n\n"))

    def test_render_tags_reference_has_no_free_form_tag_sections(self):
        text = self.render()
        for retired in (
            "mechanism_tags", "focus_tags", "domain_tags", "family_tags", "## tags", "Loop Mechanism",
            "alias tags", "category", "`foundation`",
        ):
            self.assertNotIn(retired, text)

    def test_repo_tags_reference_matches_current_yaml_inventory(self):
        expected = build.render_tags_reference_text(build.load_papers(), build.load_blogs())
        self.assertEqual(TAGS_PATH.read_text(encoding="utf-8"), expected)


class SourceFileMetadataTests(unittest.TestCase):
    def test_submission_metadata_has_minimal_deterministic_schema(self):
        papers = [
            {
                "source_path": "papers/b.yaml",
                "title": "forbidden paper title",
                "authors": "forbidden paper authors",
                "desc": "forbidden paper description",
                "metrics": {"citations": 99},
                "links": {"arxiv": "https://example.com/forbidden-paper"},
                **survey_fields(survey_section=["scaling/test-time", "architecture/topology"], claims=["stability", "expressivity"]),
            },
            {
                "source_path": "papers/a.yaml",
                **survey_fields(survey_section=["architecture/topology"], loop_topology="partial", comparison=[]),
            },
        ]
        blogs = [
            {"source_path": "blogs/c.yaml", "title": "forbidden blog title", "survey_section": ["understanding/why"]},
            {"source_path": "papers/a.yaml", "survey_section": ["architecture/topology"]},
        ]

        payload = build.render_submission_metadata(papers, blogs)
        reversed_payload = build.render_submission_metadata(list(reversed(papers)), list(reversed(blogs)))

        self.assertEqual(payload, reversed_payload)
        self.assertEqual(set(payload), {"existing_paths", "survey_taxonomy", "inventories"})
        self.assertEqual(payload["existing_paths"], ["blogs/c.yaml", "papers/a.yaml", "papers/b.yaml"])
        self.assertEqual(payload["survey_taxonomy"], build.render_survey_taxonomy())
        self.assertEqual(
            list(payload["inventories"]),
            ["survey_section", "loop_topology", "sharing", "depth_control", "claims", "comparison"],
        )

        sections = payload["inventories"]["survey_section"]
        self.assertEqual(len(sections), len(build.VALID_SURVEY_SECTIONS))
        self.assertEqual({row["label"] for row in sections}, set(build.VALID_SURVEY_SECTIONS))
        self.assertEqual(
            sections[:3],
            [
                {"label": "architecture/topology", "count": 3},
                {"label": "scaling/test-time", "count": 1},
                {"label": "understanding/why", "count": 1},
            ],
        )
        zero_rows = [row["label"] for row in sections if row["count"] == 0]
        self.assertEqual(zero_rows, sorted(zero_rows, key=str.lower))

        self.assertEqual(
            payload["inventories"]["loop_topology"][:2],
            [{"label": "partial", "count": 1}, {"label": "prelude-core-coda", "count": 1}],
        )
        self.assertEqual(payload["inventories"]["sharing"][0], {"label": "full", "count": 2})
        self.assertEqual(
            payload["inventories"]["claims"][:4],
            [
                {"label": "expressivity", "count": 1},
                {"label": "stability", "count": 1},
                {"label": "test-time-scaling", "count": 1},
                {"label": "compute-efficiency", "count": 0},
            ],
        )
        self.assertEqual(payload["inventories"]["comparison"][0], {"label": "iso-param", "count": 1})
        for field, values in (*build.SURVEY_SCALAR_FIELDS, *build.SURVEY_LIST_FIELDS):
            self.assertEqual({row["label"] for row in payload["inventories"][field]}, set(values))
            for row in payload["inventories"][field]:
                self.assertEqual(set(row), {"label", "count"})

        serialized = json.dumps(payload)
        entry_data = json.dumps({key: payload[key] for key in ("existing_paths", "inventories")})
        for forbidden_field in (
            '"title"', '"authors"', '"desc"', '"metrics"', '"links"', '"briefings"', '"tags"',
            '"tag_inventories"', '"papers"', '"blogs"', '"generated"',
        ):
            self.assertNotIn(forbidden_field, entry_data)
        for forbidden_value in (
            "forbidden paper title",
            "forbidden paper authors",
            "forbidden paper description",
            "forbidden blog title",
        ):
            self.assertNotIn(forbidden_value, serialized)

    def test_build_submission_metadata_writes_rendered_payload(self):
        papers = [{"source_path": "papers/a.yaml", **survey_fields()}]
        blogs = [{"source_path": "blogs/b.yaml", "survey_section": ["understanding/why"]}]

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "submission-meta.json"
            with patch.object(build, "SUBMISSION_META_OUT", output_path):
                build.build_submission_metadata(papers, blogs)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(payload, build.render_submission_metadata(papers, blogs))

    def test_repo_submission_metadata_matches_current_yaml_inventory(self):
        expected = build.render_submission_metadata(build.load_papers(), build.load_blogs())
        payload = json.loads((REPO_ROOT / "submission-meta.json").read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

    def test_loaded_entries_expose_source_paths(self):
        paper = build.load_papers()[0]
        blog = build.load_blogs()[0]

        self.assertTrue(paper["source_file"].endswith(".yaml"))
        self.assertTrue(paper["source_path"].startswith("papers/"))
        self.assertTrue(blog["source_file"].endswith(".yaml"))
        self.assertTrue(blog["source_path"].startswith("blogs/"))

    def test_generated_json_uses_the_survey_taxonomy(self):
        payload = json.loads((REPO_ROOT / "papers.json").read_text(encoding="utf-8"))
        papers = [
            paper
            for row in payload["paper_chunks"]
            for paper in json.loads((REPO_ROOT / row["path"]).read_text(encoding="utf-8"))["papers"]
        ]
        self.assertEqual(len(papers), payload["meta"]["paper_total"])
        self.assertEqual(payload["survey_taxonomy"], build.render_survey_taxonomy())
        self.assertEqual(payload["meta"]["taxonomy_note"], build.TAXONOMY_NOTE)
        self.assertNotIn("mechanism_tags", payload)
        for paper in papers:
            source = paper.get("id")
            for field in build.REQUIRED_PAPER_SURVEY_FIELDS:
                self.assertIn(field, paper, source)
            build.normalize_survey_fields(paper, source, build.REQUIRED_PAPER_SURVEY_FIELDS)
            for field in (*build.RETIRED_FIELDS, "family_tags"):
                self.assertNotIn(field, paper, source)
        for blog in payload.get("blogs", []):
            self.assertTrue(blog.get("survey_section"), blog.get("id"))
            for field in (*build.RETIRED_FIELDS, "loop_topology", "sharing", "depth_control", "claims", "comparison"):
                self.assertNotIn(field, blog, blog.get("id"))

    def test_blog_yaml_files_use_published_date_prefix(self):
        blog_files = [path.name for path in (REPO_ROOT / "blogs").glob("*.yaml") if not path.name.startswith("_")]
        self.assertTrue(blog_files)
        for name in blog_files:
            self.assertRegex(name, r"^\d{4}-\d{2}-\d{2}-")


class DocumentationConsistencyTests(unittest.TestCase):
    def test_docs_explain_the_adjacent_work_exception(self):
        for text in (
            TAXONOMY_PATH.read_text(encoding="utf-8"),
            CONTRIBUTING_PATH.read_text(encoding="utf-8"),
            README_HEADER_PATH.read_text(encoding="utf-8"),
            PAPER_TEMPLATE_PATH.read_text(encoding="utf-8"),
        ):
            self.assertIn("catalog_fit", text)
            self.assertIn("adjacent", text.lower())
            self.assertIn("strict", text.lower())

    def test_docs_explain_flat_blogs_section(self):
        for text in (
            TAXONOMY_PATH.read_text(encoding="utf-8"),
            CONTRIBUTING_PATH.read_text(encoding="utf-8"),
            README_HEADER_PATH.read_text(encoding="utf-8"),
            BLOG_TEMPLATE_PATH.read_text(encoding="utf-8"),
        ):
            self.assertIn("Blogs", text)
            self.assertIn("flat", text.lower())
            self.assertIn("blog", text.lower())

    def test_docs_point_contributors_to_tags_reference(self):
        for text in (
            TAXONOMY_PATH.read_text(encoding="utf-8"),
            CONTRIBUTING_PATH.read_text(encoding="utf-8"),
            README_HEADER_PATH.read_text(encoding="utf-8"),
            README_FOOTER_PATH.read_text(encoding="utf-8"),
            ISSUE_TEMPLATE_CONFIG_PATH.read_text(encoding="utf-8"),
        ):
            self.assertIn("TAGS.md", text)

    def test_reader_facing_text_never_frames_the_taxonomy_as_a_survey_paper(self):
        """Only preserved data keys, identifiers, CSS classes and DOM ids may still say "survey"."""
        preserved = re.compile(
            r"survey_(?:section|core|taxonomy)\w*"  # YAML/JSON keys and derived names
            r"|\bSURVEY\w*"  # Python/JS constants
            r"|\b[a-z]\w*Survey\w*|\bsurvey[A-Z]\w*"  # camelCase JS identifiers
            r"|\bdata-survey-anchor|surveyAnchor"  # DOM data attribute
            r"|\.?survey-[a-z][a-z-]*"  # CSS classes and DOM ids
            r"|invalid-survey-value"  # audit finding code
        )
        paths = (
            REPO_ROOT / "README.md", TAGS_PATH, TAXONOMY_PATH, CONTRIBUTING_PATH, INDEX_HTML_PATH, SUBMIT_PAGE_PATH,
            READING_DESK_JS_PATH, README_HEADER_PATH, README_FOOTER_PATH, PR_TEMPLATE_PATH, FIX_ERROR_TEMPLATE_PATH,
            ISSUE_TEMPLATE_CONFIG_PATH, ISSUE_TEMPLATE_CONFIG_TEMPLATE_PATH, PAPER_TEMPLATE_PATH, BLOG_TEMPLATE_PATH,
        )
        for path in paths:
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                remainder = preserved.sub("", line)
                self.assertNotIn("survey", remainder.lower(), f"{path.name}:{number}: {line.strip()[:160]}")
        for text in (build.TAXONOMY_NOTE, build.BLOG_SECTION_DESC):
            self.assertNotIn("survey", text.lower())

    def test_contributor_docs_require_published_date_and_explain_added_date(self):
        for text in (
            CONTRIBUTING_PATH.read_text(encoding="utf-8"),
            PAPER_TEMPLATE_PATH.read_text(encoding="utf-8"),
            BLOG_TEMPLATE_PATH.read_text(encoding="utf-8"),
        ):
            self.assertIn("`published_date`", text)
            self.assertIn("`added_date`", text)
            self.assertIn("`YYYY-MM-DD`", text)
            self.assertNotIn("older historical entries may omit `published_date` and `added_date`", text.lower())
            self.assertNotIn("historical entries may omit them", text.lower())


class AddArxivYamlRegressionTests(unittest.TestCase):
    ARXIV_DATA = {
        "title": "Loop's Test Paper",
        "authors": ["Test Author", "O'Brien"],
        "year": 2026,
        "published_date": "2026-04-20",
        "summary": "Introduces a looped model. It works well.",
        "id": "2604.11791",
    }

    def parse(self, *extra: str):
        argv = ["add_arxiv_yaml.py", "2604.11791", *extra]
        with patch.object(add_arxiv_yaml.sys, "argv", argv):
            return add_arxiv_yaml.parse_args()

    def required_args(self):
        return (
            "--section", "scaling/test-time",
            "--loop-topology", "prelude-core-coda",
            "--sharing", "full",
            "--depth-control", "sampled-train",
        )

    def test_add_arxiv_helper_has_survey_flags_and_no_retired_options(self):
        text = ADD_ARXIV_YAML_PATH.read_text(encoding="utf-8")
        for retired in (
            "--category", "category_path", "--mechanism", "mechanism_tags", "focus_tags", "domain_tags",
            "--foundation", "--tag", "flat-loop",
        ):
            self.assertNotIn(retired, text)
        for flag in (
            "--section", "--loop-topology", "--sharing", "--depth-control", "--claim", "--comparison",
            "--survey-core", "--catalog-fit",
        ):
            self.assertIn(f'"{flag}"', text)

    def test_add_arxiv_helper_requires_section_and_scalar_axes(self):
        required = list(self.required_args())
        for index in range(0, len(required), 2):
            missing = required[:index] + required[index + 2:]
            with self.subTest(missing=required[index]):
                with patch("sys.stderr"), self.assertRaises(SystemExit):
                    self.parse(*missing)
        for bad in (
            ("--section", "design/topology"),
            ("--loop-topology", "flat-loop"),
            ("--claim", "speed"),
            ("--comparison", "iso-time"),
            ("--catalog-fit", "strict"),
        ):
            with self.subTest(bad=bad):
                with patch("sys.stderr"), self.assertRaises(SystemExit):
                    self.parse(*self.required_args(), *bad)

    def test_add_arxiv_helper_renders_a_skeleton_the_build_accepts(self):
        args = self.parse(
            *self.required_args(),
            "--section", "architecture/topology",
            "--section", "scaling/test-time",
            "--claim", "test-time-scaling",
            "--claim", "stability",
            "--claim", "test-time-scaling",
            "--comparison", "iso-flop",
            "--survey-core",
            "--catalog-fit", "adjacent",
            "--added-date", "2026-10-12",
        )
        text = add_arxiv_yaml.render_yaml(dict(self.ARXIV_DATA), args)
        data = yaml.safe_load(text)

        build.reject_retired_fields(data, "2604.11791.yaml")
        build.validate_links(data["links"], "2604.11791.yaml")
        self.assertEqual(build.normalize_paper_taxonomy_fields(data, "2604.11791.yaml"), {"catalog_fit": "adjacent"})
        self.assertEqual(
            build.normalize_survey_fields(data, "2604.11791.yaml", build.REQUIRED_PAPER_SURVEY_FIELDS),
            {
                "survey_section": ["scaling/test-time", "architecture/topology"],
                "loop_topology": "prelude-core-coda",
                "sharing": "full",
                "depth_control": "sampled-train",
                "claims": ["test-time-scaling", "stability"],
                "comparison": ["iso-flop"],
                "survey_core": True,
            },
        )
        self.assertEqual(data["title"], "Loop's Test Paper")
        self.assertEqual(data["authors"], ["Test Author", "O'Brien"])
        self.assertEqual(data["published_date"], "2026-04-20")
        self.assertEqual(data["added_date"], "2026-10-12")
        self.assertEqual(data["desc"], "Introduces a looped model.")
        self.assertEqual(data["links"], {"arxiv": "https://arxiv.org/abs/2604.11791"})
        self.assertNotIn("must_read", data)
        for field in build.RETIRED_FIELDS:
            self.assertNotIn(f"{field}:", text)

    def test_add_arxiv_helper_defaults_to_strict_scope_and_empty_lists(self):
        args = self.parse(*self.required_args(), "--added-date", "2026-10-12")
        text = add_arxiv_yaml.render_yaml(dict(self.ARXIV_DATA), args)
        data = yaml.safe_load(text)

        self.assertIn("claims: []\n", text)
        self.assertIn("comparison: []\n", text)
        self.assertNotIn("catalog_fit", data)
        self.assertNotIn("survey_core", data)
        self.assertEqual(build.normalize_paper_taxonomy_fields(data, "x.yaml"), {"catalog_fit": "strict"})
        survey = build.normalize_survey_fields(data, "x.yaml", build.REQUIRED_PAPER_SURVEY_FIELDS)
        self.assertEqual(survey["survey_section"], ["scaling/test-time"])
        self.assertEqual(survey["claims"], [])
        self.assertEqual(survey["comparison"], [])

    def test_add_arxiv_helper_writes_a_loadable_paper_file(self):
        args = self.parse(*self.required_args(), "--added-date", "2026-10-12")
        with TemporaryDirectory() as tmpdir:
            papers_dir = Path(tmpdir)
            (papers_dir / "2604.11791.yaml").write_text(
                add_arxiv_yaml.render_yaml(dict(self.ARXIV_DATA), args), encoding="utf-8"
            )
            with patch.object(build, "PAPERS_DIR", papers_dir):
                papers = build.load_papers()
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["survey_section"], ["scaling/test-time"])
        self.assertEqual(papers[0]["links"]["alphaxiv"], "https://www.alphaxiv.org/abs/2604.11791")

    def test_fetch_arxiv_entry_requires_usable_published_date(self):
        payload = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <entry>
    <id>http://arxiv.org/abs/2604.11791v1</id>
    <published>2026/04/20</published>
    <title>Loop Test Paper</title>
    <summary>Test summary.</summary>
    <author><name>Test Author</name></author>
  </entry>
</feed>
"""

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return payload.encode("utf-8")

        with patch.object(add_arxiv_yaml.urllib.request, "urlopen", return_value=FakeResponse()):
            with self.assertRaisesRegex(SystemExit, "Missing usable published_date in arXiv metadata"):
                add_arxiv_yaml.fetch_arxiv_entry("2604.11791")


class ContributionWorkflowTests(unittest.TestCase):
    @staticmethod
    def load_repo_meta() -> dict:
        return json.loads(REPO_META_PATH.read_text(encoding="utf-8"))

    @staticmethod
    def load_issue_config() -> dict:
        return yaml.safe_load(ISSUE_TEMPLATE_CONFIG_PATH.read_text(encoding="utf-8"))

    @staticmethod
    def run_submit_script(expression: str):
        """Evaluate submit.html's taxonomy, YAML and picker helpers in Node with a stub DOM.

        ``expression`` may hold several statements; the value of the last one is returned.
        """
        html = SUBMIT_PAGE_PATH.read_text(encoding="utf-8")

        def between(start_marker: str, end_marker: str) -> str:
            start = html.index(start_marker)
            return html[start:html.index(end_marker, start)]

        helpers = "\n".join((
            between("const SCALAR_AXES = ", "function syncRequiredFieldStates() {"),
            between("function renderPrimarySectionSelect() {", "function renderAllPickers() {"),
            between("function computeShortname(values) {", "function setActionDisabled(disabled) {"),
        ))
        script = f"""
const elements = {{}};
const document = {{
  getElementById: function(id) {{
    if (!elements[id]) elements[id] = {{ id: id, innerHTML: '', textContent: '', value: '', disabled: false }};
    return elements[id];
  }}
}};
{helpers}
const result = eval({json.dumps(expression)});
process.stdout.write(JSON.stringify(result));
"""
        output = subprocess.check_output(["node", "-e", script], text=True)
        return json.loads(output)

    def test_old_submission_issue_templates_are_removed(self):
        self.assertFalse((REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "add_paper.yml").exists())
        self.assertFalse((REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "add_blog.yml").exists())
        self.assertTrue(FIX_ERROR_TEMPLATE_PATH.exists())

    def test_repo_meta_file_and_generated_js_exist(self):
        meta = self.load_repo_meta()
        js = REPO_META_JS_PATH.read_text(encoding="utf-8")
        self.assertEqual(meta["github_owner"], "huskydoge")
        self.assertEqual(meta["default_repo_name"], "Awesome-Loop-Models")
        self.assertEqual(meta["public_repo_name"], "Awesome-Loop-Models")
        self.assertTrue(ISSUE_TEMPLATE_CONFIG_TEMPLATE_PATH.exists())
        self.assertIn(f'githubOwner: {json.dumps(meta["github_owner"])}', js)
        self.assertIn(f'defaultRepoName: {json.dumps(meta["default_repo_name"])}', js)
        self.assertIn(f'publicRepoName: {json.dumps(meta["public_repo_name"])}', js)
        self.assertIn("inferRepoNameFromLocation", js)
        self.assertIn("getGitHubRepoBase", js)
        self.assertIn("getGitHubBlobUrl", js)
        self.assertIn("getGitHubNewFileBase", js)

    def test_issue_template_config_points_to_submit_guide(self):
        meta = self.load_repo_meta()
        config = self.load_issue_config()
        self.assertFalse(config.get("blank_issues_enabled", True))
        urls = [item.get("url", "") for item in config.get("contact_links", [])]
        self.assertIn(f'https://{meta["github_owner"]}.github.io/{meta["public_repo_name"]}/submit.html', urls)
        self.assertIn(f'https://github.com/{meta["github_owner"]}/{meta["public_repo_name"]}/blob/main/TAGS.md', urls)
        self.assertNotIn("issue form", config["contact_links"][0].get("about", "").lower())
        self.assertIn("fork", config["contact_links"][0].get("about", "").lower())

    def test_fix_error_issue_template_still_exists_for_non_submission_issues(self):
        text = FIX_ERROR_TEMPLATE_PATH.read_text(encoding="utf-8")
        self.assertIn("Fix an Error", text)
        self.assertIn("broken link", text.lower())
        self.assertNotIn("Add a Paper", text)
        self.assertNotIn("Add a Blog", text)

    def test_pull_request_template_exists_for_submission_review(self):
        template = PR_TEMPLATE_PATH.read_text(encoding="utf-8")
        self.assertIn("submit.html", template)
        self.assertIn("papers/", template)
        self.assertIn("blogs/", template)
        self.assertIn("generated YAML", template)
        self.assertIn("taxonomy", template.lower())
        self.assertIn("controlled taxonomy-vocabulary", template.lower())
        self.assertNotIn("new category", template.lower())
        self.assertNotIn("new tags", template.lower())

    def test_submit_page_contains_survey_pickers_yaml_preview_and_fork_first_github_guidance(self):
        html = SUBMIT_PAGE_PATH.read_text(encoding="utf-8")
        script = html[html.index('<script src="assets/repo-meta.js?v=2"></script>'):]
        self.assertIn("fetchJson('submission-meta.json')", script)
        self.assertIn("fetchJson('papers.json')", script)
        self.assertIn("catalog.survey_taxonomy", script)
        self.assertNotIn("data.papers", script)
        self.assertNotIn("data.blogs", script)
        self.assertNotIn("deriveFallbackSourcePath", html)
        self.assertIn("data.existing_paths", script)
        self.assertIn("isValidSurveyTaxonomy(data.survey_taxonomy)", script)
        self.assertIn("isValidCountedInventory(inventories[field])", script)
        self.assertIn("const SCALAR_AXES = ['loop_topology', 'sharing', 'depth_control'];", script)
        self.assertIn("const LIST_AXES = ['claims', 'comparison'];", script)
        for marker in (
            "submission-form",
            "resource-kind-toggle",
            "resource-title-input",
            "authors-input",
            "published-date-input",
            "shortname-input",
            "primary-link-input",
            'id="primary-section-select"',
            'id="extra-sections-list"',
            'id="paper-axes-section"',
            'id="loop_topology-picker"',
            'id="sharing-picker"',
            'id="depth_control-picker"',
            'id="claims-picker"',
            'id="comparison-picker"',
            "yaml-preview-output",
            "target-path-output",
            "effective-shortname-output",
            "extracted-arxiv-id-output",
            "path-status-output",
            "github-repo-url-output",
            "copy-target-path-btn",
            "Open GitHub repo (fork first)",
            "GitHub fork / PR handoff",
            "Manual GitHub step",
            "Ready to copy into your fork",
            "Step 1",
            "Step 2",
            "Step 3",
            "copyTargetPath",
            "openGitHubRepoForFork",
            "buildYamlPreview",
            "slugifyFilenamePart",
            "extractArxivId",
            "targetFileExists",
            "Topic-map placement",
            "Design axes",
            "PR message",
            "Open the vocabulary (TAGS.md)",
            "How to choose values (TAXONOMY.md)",
        ):
            self.assertIn(marker, html)
        for retired in (
            "tag_inventories", "Searchable tag picker", "tag-picker-search", "category-select", "Paper Category",
            "three flat paper categories", "Browser-facing loop-form tags", "hierarchical-loop", "flat-loop",
            "parallel-loop", "implicit-layer", "domain-tags-manual-input", "alias-tags-manual-input",
            "mergeSuggestedCountedInventory", "SUGGESTED_DOMAIN_TAGS", "efficient-loop", "new-category-input",
            "Custom Category / Path", "category/subcategory", "category_path", "family_tags", "Family Tags",
            "Open prefilled GitHub issue", "Open GitHub editor for PR", "buildGitHubNewFileUrl", "new/main?filename=",
            "What counts as a blog?", "substantive public long-form technical post",
        ):
            self.assertNotIn(retired, html)
        self.assertNotIn("new category", html.lower())
        self.assertNotIn("new tags", html.lower())
        self.assertLess(html.index("Generate YAML and prepare your fork / PR"), html.index("Topic-map placement"))
        self.assertLess(html.index("resource-title-input"), html.index('id="primary-section-select"'))
        self.assertLess(html.index('id="primary-section-select"'), html.index('id="loop_topology-picker"'))
        self.assertLess(html.index('id="comparison-picker"'), html.index("Generated target path"))

    def test_submit_taxonomy_and_inventory_validators(self):
        taxonomy = json.dumps(build.render_survey_taxonomy())
        result = self.run_submit_script(f"""
const taxonomy = {taxonomy};
const withoutAxis = JSON.parse(JSON.stringify(taxonomy));
delete withoutAxis.axes.comparison;
const badSection = JSON.parse(JSON.stringify(taxonomy));
badSection.sections[0].number = 2.1;
const emptyChapters = Object.assign({{}}, taxonomy, {{ chapters: [] }});
const counts = indexInventoryCounts({{
  survey_section: [{{ label: 'architecture/topology', count: 3 }}],
  claims: [{{ label: 'stability', count: 2 }}],
  tags: [{{ label: 'LoopLM', count: 9 }}]
}});
({{
  valid: isValidSurveyTaxonomy(taxonomy),
  invalid: [isValidSurveyTaxonomy(withoutAxis), isValidSurveyTaxonomy(badSection), isValidSurveyTaxonomy(emptyChapters), isValidSurveyTaxonomy(null)],
  countFields: Object.keys(counts),
  sectionCount: counts.survey_section['architecture/topology'],
  claimCount: counts.claims.stability,
  emptyCounts: indexInventoryCounts(undefined)
}})
""")
        self.assertTrue(result["valid"])
        self.assertEqual(result["invalid"], [False, False, False, False])
        self.assertEqual(
            result["countFields"],
            ["survey_section", "loop_topology", "sharing", "depth_control", "claims", "comparison"],
        )
        self.assertEqual(result["sectionCount"], 3)
        self.assertEqual(result["claimCount"], 2)
        self.assertEqual(
            result["emptyCounts"],
            {field: {} for field in ("survey_section", "loop_topology", "sharing", "depth_control", "claims", "comparison")},
        )

    def test_submit_inventory_helper_rejects_malformed_rows(self):
        result = self.run_submit_script("""({
  valid: isValidCountedInventory([{label: 'architecture/topology', count: 0}]),
  malformed: [
    isValidCountedInventory([null]),
    isValidCountedInventory([[]]),
    isValidCountedInventory([{label: '', count: 0}]),
    isValidCountedInventory([{label: '   ', count: 0}]),
    isValidCountedInventory([{label: 3, count: 0}]),
    isValidCountedInventory([{label: 'partial', count: -1}]),
    isValidCountedInventory([{label: 'partial', count: 1.5}]),
    isValidCountedInventory([{label: 'partial', count: Infinity}]),
    isValidCountedInventory([{label: 'partial', count: NaN}]),
    isValidCountedInventory([
      Object.assign(Object.create(null), {label: 'partial', count: 1})
    ]),
    isValidCountedInventory(undefined)
  ]
})""")

        self.assertTrue(result["valid"])
        self.assertEqual(result["malformed"], [False] * 11)

    def test_repo_submission_metadata_passes_the_submit_page_validators(self):
        payload = json.loads((REPO_ROOT / "submission-meta.json").read_text(encoding="utf-8"))
        result = self.run_submit_script(f"""
const data = {json.dumps(payload)};
({{
  taxonomy: isValidSurveyTaxonomy(data.survey_taxonomy),
  inventories: ['survey_section'].concat(SCALAR_AXES, LIST_AXES).map(function(field) {{
    return isValidCountedInventory(data.inventories[field]);
  }})
}})
""")
        self.assertEqual(result, {"taxonomy": True, "inventories": [True] * 6})

    def test_submit_generates_paper_yaml_that_the_build_accepts(self):
        taxonomy = json.dumps(build.render_survey_taxonomy())
        result = self.run_submit_script(f"""
STATE.taxonomy = {taxonomy};
STATE.metadataLoading = false;
STATE.existingPaths = new Set(['papers/2604.11791.yaml']);
const values = {{
  kind: 'paper', title: 'Loop "Quoted" Paper', authors: ['A. Author', 'B. Author'], publishedDate: '2026-04-20',
  venue: 'arXiv', shortname: '', primaryLink: 'https://arxiv.org/abs/2604.11792v2', code: 'https://github.com/x/y',
  openreview: '', project: '', github: '', twitter: '', description: 'Loops.', addedDate: '2026-10-12'
}};
const missingSection = getValidationError(values);
STATE.primarySection = 'scaling/test-time';
STATE.extraSections = ['architecture/topology', 'scaling/test-time', 'architecture/depth-control'];
const missingAxis = getValidationError(values);
STATE.scalar = {{ loop_topology: 'prelude-core-coda', sharing: 'full', depth_control: 'unspecified' }};
STATE.lists.claims = new Set(['stability', 'test-time-scaling']);
({{
  missingSection: missingSection,
  missingAxis: missingAxis,
  ready: getValidationError(values),
  sections: getSurveySections(),
  path: buildTargetPath(values),
  duplicate: targetFileExists('papers/2604.11791.yaml'),
  yaml: buildYamlPreview(values),
  snippet: buildSnippet()
}})
""")
        self.assertEqual(result["missingSection"], "Please choose the primary section.")
        self.assertEqual(
            result["missingAxis"],
            "Please choose a loop topology value (use unspecified if the paper does not say).",
        )
        self.assertEqual(result["ready"], "")
        self.assertEqual(result["sections"], ["scaling/test-time", "architecture/topology", "architecture/depth-control"])
        self.assertEqual(result["path"], "papers/2604.11792.yaml")
        self.assertTrue(result["duplicate"])

        data = yaml.safe_load(result["yaml"])
        build.reject_retired_fields(data, "generated.yaml")
        build.validate_links(data["links"], "generated.yaml")
        survey = build.normalize_survey_fields(data, "generated.yaml", build.REQUIRED_PAPER_SURVEY_FIELDS)
        self.assertEqual(
            survey,
            {
                "survey_section": ["scaling/test-time", "architecture/topology", "architecture/depth-control"],
                "loop_topology": "prelude-core-coda",
                "sharing": "full",
                "depth_control": "unspecified",
                "claims": ["test-time-scaling", "stability"],
                "comparison": [],
                "survey_core": False,
            },
        )
        self.assertEqual(data["title"], 'Loop "Quoted" Paper')
        self.assertEqual(data["published_date"], "2026-04-20")
        self.assertEqual(data["added_date"], "2026-10-12")
        self.assertEqual(data["links"], {"arxiv": "https://arxiv.org/abs/2604.11792v2", "github": "https://github.com/x/y"})
        self.assertNotIn("must_read", data)
        self.assertNotIn("catalog_fit", data)
        self.assertTrue(result["yaml"].index("survey_section:") < result["yaml"].index("desc:"))
        self.assertTrue(result["snippet"].startswith("survey_section:\n"))
        self.assertTrue(result["snippet"].endswith("survey_core: false"))

    def test_submit_generates_blog_yaml_with_only_survey_sections(self):
        taxonomy = json.dumps(build.render_survey_taxonomy())
        result = self.run_submit_script(f"""
STATE.taxonomy = {taxonomy};
STATE.metadataLoading = false;
STATE.formKind = 'blog';
STATE.primarySection = 'understanding/why';
STATE.scalar = {{ loop_topology: 'partial', sharing: 'full', depth_control: 'fixed' }};
STATE.lists.claims = new Set(['stability']);
const values = {{
  kind: 'blog', title: 'A Blog Post', authors: ['A. Author'], publishedDate: '2026-04-21', venue: 'Lab Blog',
  shortname: 'Loop Notes!', primaryLink: 'https://example.com/post', code: '', openreview: '', project: '',
  github: '', twitter: 'https://x.com/a/status/1', description: 'Notes.', addedDate: '2026-10-12'
}};
({{ error: getValidationError(values), path: buildTargetPath(Object.assign({{}}, values, {{ shortname: 'loop-notes' }})), yaml: buildYamlPreview(values) }})
""")
        self.assertEqual(result["error"], "")
        self.assertEqual(result["path"], "blogs/2026-04-21-loop-notes.yaml")
        data = yaml.safe_load(result["yaml"])
        build.reject_retired_fields(data, "blog.yaml")
        build.validate_blog_links(data["links"], "blog.yaml")
        self.assertEqual(data["survey_section"], ["understanding/why"])
        for field in build.SURVEY_FIELDS:
            if field != "survey_section":
                self.assertNotIn(field, data)
        self.assertEqual(data["links"], {"blog": "https://example.com/post", "twitter": "https://x.com/a/status/1"})

    def test_submit_pickers_render_chapter_groups_counts_and_axis_controls(self):
        taxonomy = json.dumps(build.render_survey_taxonomy())
        result = self.run_submit_script(f"""
STATE.taxonomy = {taxonomy};
STATE.counts = indexInventoryCounts({{
  survey_section: [{{ label: 'architecture/topology', count: 7 }}],
  loop_topology: [{{ label: 'partial', count: 4 }}],
  claims: [{{ label: 'stability', count: 2 }}]
}});
STATE.primarySection = 'architecture/topology';
STATE.extraSections = ['scaling/test-time'];
STATE.scalar.loop_topology = 'partial';
STATE.lists.claims.add('stability');
renderPrimarySectionSelect();
renderExtraSectionList();
renderAxisPicker('loop_topology');
renderAxisPicker('claims');
({{
  primary: elements['primary-section-select'].innerHTML,
  primaryValue: elements['primary-section-select'].value,
  extras: elements['extra-sections-list'].innerHTML,
  extraCount: elements['extra-sections-count'].textContent,
  topology: elements['loop_topology-picker'].innerHTML,
  claims: elements['claims-picker'].innerHTML
}})
""")
        self.assertEqual(result["primary"].count("<optgroup"), len(build.SURVEY_CHAPTERS))
        self.assertIn('<optgroup label="§4 Architecture and Design">', result["primary"])
        self.assertIn('<option value="architecture/topology">§4.1 Loop topology (7)</option>', result["primary"])
        self.assertIn('<option value="scaling/test-time">§6.2 Test-time scaling (0)</option>', result["primary"])
        self.assertEqual(result["primaryValue"], "architecture/topology")
        self.assertIn("§4.1 Loop topology — primary", result["extras"])
        self.assertIn("§6.2 Test-time scaling — #2", result["extras"])
        self.assertIn('data-extra-section="architecture/topology" checked disabled', result["extras"])
        self.assertEqual(result["extraCount"], "1 selected")
        self.assertIn('<select class="field-select" id="loop_topology-select" data-scalar-axis="loop_topology">', result["topology"])
        self.assertIn('<option value="partial" selected>partial (4)</option>', result["topology"])
        self.assertIn('<label class="picker-title" for="loop_topology-select">Loop topology</label>', result["topology"])
        self.assertIn('data-list-axis="claims" value="stability" checked', result["claims"])
        self.assertIn('<span class="option-count">2</span>', result["claims"])
        self.assertIn("1 selected", result["claims"])

    def test_submit_page_marks_required_fields_and_gives_picker_actions_more_spacing(self):
        html = SUBMIT_PAGE_PATH.read_text(encoding="utf-8")
        self.assertIn(".panel {\n      background: transparent;\n      border: 0;\n      border-top: 1px solid var(--border);\n      border-radius: 0;\n      box-shadow: none;", html)
        self.assertIn('class="site-header"', html)
        self.assertIn('class="site-brand-mark" aria-hidden="true">LM</span>', html)
        self.assertIn('href="index.html#stats">Stats</a>', html)
        self.assertIn('aria-current="page">Submit</a>', html)
        self.assertIn(".field.is-required .field-label::after", html)
        self.assertIn("content: ' *';", html)
        self.assertIn(".field.is-invalid .field-label", html)
        self.assertIn(".field.is-invalid .field-input", html)
        self.assertIn(".picker.is-invalid .picker-title", html)
        self.assertIn(".picker-actions {\n      margin-block: var(--space-4);", html)
        self.assertIn(".preview-box {\n      border: 0;\n      border-top: 1px solid var(--border);", html)
        self.assertIn(".github-branch-callout {\n      border: 0;\n      border-left: 3px solid rgba(9, 105, 218, 0.28);", html)
        self.assertIn("syncRequiredFieldStates()", html)
        self.assertIn("syncPickerValidity()", html)

    def test_submit_pickers_use_delegated_listeners_that_survive_rerendering(self):
        html = SUBMIT_PAGE_PATH.read_text(encoding="utf-8")
        start = html.index("function wirePickers() {")
        source = html[start:html.index("function setResourceKind(kind) {", start)]
        self.assertIn("document.getElementById('primary-section-select').addEventListener('change'", source)
        self.assertIn("document.getElementById('extra-sections-list').addEventListener('change'", source)
        self.assertIn("document.getElementById('paper-axes-section').addEventListener('change'", source)
        self.assertIn("event.target.dataset.scalarAxis", source)
        self.assertIn("event.target.dataset.listAxis", source)
        self.assertNotIn("renderAllPickers()", source)

    def test_paper_template_mentions_must_read_but_submit_page_does_not_generate_it(self):
        template = PAPER_TEMPLATE_PATH.read_text(encoding="utf-8")
        html = SUBMIT_PAGE_PATH.read_text(encoding="utf-8")
        script = html[html.index('<script src="assets/repo-meta.js?v=2"></script>'):]
        self.assertIn("must_read", template)
        self.assertIn("maintainer-only", template.lower())
        self.assertNotIn("must_read", script)
        self.assertNotIn("catalog_fit", script)
        self.assertIn("<code>must_read</code> and <code>catalog_fit</code> are maintainer-only and omitted.", html)

    def test_submit_page_uses_responsive_nested_layout_and_english_selectable_published_date_input(self):
        html = SUBMIT_PAGE_PATH.read_text(encoding="utf-8")
        self.assertIn(".grid {\n      display: grid;\n      gap: var(--space-4);\n      grid-template-columns: 1fr;", html)
        self.assertIn(".wizard-grid {\n      display: grid;\n      gap: var(--space-3);\n      grid-template-columns: repeat(3, minmax(0, 1fr));", html)
        self.assertIn(".form-grid {\n      display: grid;\n      gap: var(--space-3);\n      grid-template-columns: repeat(2, minmax(0, 1fr));", html)
        self.assertIn(".axis-pickers {\n      display: grid;\n      gap: var(--space-3);\n      grid-template-columns: repeat(3, minmax(0, 1fr));", html)
        self.assertIn(".survey-pickers {\n      display: grid;\n      gap: var(--space-3);\n      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);", html)
        self.assertIn("@media (max-width: 980px)", html)
        narrow = html[html.index("@media (max-width: 980px)"):]
        self.assertIn(".axis-pickers,\n      .survey-pickers,", narrow[:narrow.index("}")])
        self.assertNotIn(".tag-pickers", html)
        self.assertIn("@media (max-width: 640px)", html)
        self.assertIn(".hero-link {\n        flex: 1 1 100%;", html)
        self.assertIn(".kind-toggle {\n        width: 100%;", html)
        self.assertIn(".preview-card pre {\n        max-width: 100%;\n        overflow-x: auto;", html)
        self.assertIn(".action-row {\n        display: grid;\n        grid-template-columns: 1fr;", html)
        self.assertIn('id="published-date-input" type="text"', html)
        self.assertIn('placeholder="YYYY-MM-DD"', html)
        self.assertIn('inputmode="numeric"', html)
        self.assertIn('id="published-date-picker-btn"', html)
        self.assertIn('aria-label="Open calendar"', html)
        self.assertIn('id="published-date-native-input" type="date"', html)
        self.assertIn('showPicker()', html)
        self.assertIn("Use the calendar button or type plain", html)
        self.assertIn("Please enter published_date as YYYY-MM-DD.", html)

    def test_submit_page_uses_repo_agnostic_public_links_and_shared_repo_meta_helper(self):
        html = SUBMIT_PAGE_PATH.read_text(encoding="utf-8")
        self.assertIn('id="hero-tags-link"', html)
        self.assertIn('id="hero-contributing-link"', html)
        self.assertIn('<script src="assets/repo-meta.js?v=2"></script>', html)
        self.assertIn('const REPO_META = window.REPO_META;', html)
        self.assertIn("const GITHUB_REPO_BASE = REPO_META.getGitHubRepoBase();", html)
        self.assertIn("const GITHUB_TAGS_URL = REPO_META.getGitHubBlobUrl('TAGS.md');", html)
        self.assertIn("const GITHUB_CONTRIBUTING_URL = REPO_META.getGitHubBlobUrl('CONTRIBUTING.md');", html)
        self.assertIn("initializeDocLinks()", html)
        self.assertNotIn("const GITHUB_NEW_FILE_BASE = REPO_META.getGitHubNewFileBase();", html)
        self.assertNotIn("const DEFAULT_GITHUB_OWNER = 'huskydoge';", html)
        self.assertNotIn("const DEFAULT_REPO_NAME = 'Awesome-Loop-Models';", html)
        self.assertNotIn("function inferRepoNameFromLocation()", html)
        self.assertNotIn("const GITHUB_NEW_FILE_BASE = 'https://github.com/huskydoge/Awesome-Loop-Models/new/main';", html)

    def test_readme_header_template_uses_public_pages_placeholders(self):
        text = README_HEADER_PATH.read_text(encoding="utf-8")
        self.assertIn("{{PUBLIC_SUBMIT_URL}}", text)
        self.assertIn("{{PUBLIC_INDEX_URL}}", text)
        self.assertNotIn("](submit.html)", text)
        self.assertNotIn("](index.html)", text)
        self.assertNotIn("→ index.html", text)
        self.assertNotIn("→ submit.html", text)
        self.assertIn("Interactive Browser", text)
        self.assertIn("PR Submission Guide", text)
        self.assertIn(" · ", text)

    def test_generated_readme_uses_public_pages_browser_and_submit_links(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("https://huskydoge.github.io/Awesome-Loop-Models/submit.html", readme)
        self.assertIn("https://huskydoge.github.io/Awesome-Loop-Models/index.html", readme)
        self.assertNotIn("](submit.html)", readme)
        self.assertNotIn("](index.html)", readme)

    def test_site_footer_uses_shared_repo_meta_link_helper_and_blob_contributing_guide(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('<link rel="icon" type="image/png" href="assets/favicon.png" />', html)
        favicon = FAVICON_PATH.read_bytes()
        self.assertTrue(favicon.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertIn('id="header-github-link"', html)
        self.assertIn('id="footer-github-link"', html)
        self.assertIn('id="footer-contributing-link"', html)
        self.assertIn('<script src="assets/repo-meta.js?v=2"></script>', html)
        self.assertIn('const REPO_META = window.REPO_META;', html)
        self.assertIn("initializeRepoLinks();", html)
        self.assertIn("REPO_META.getGitHubRepoBase()", html)
        self.assertIn("REPO_META.getGitHubBlobUrl('CONTRIBUTING.md')", html)
        self.assertNotIn("const DEFAULT_GITHUB_OWNER = 'huskydoge';", html)
        self.assertNotIn("const DEFAULT_REPO_NAME = 'Awesome-Loop-Models';", html)
        self.assertNotIn("function inferRepoNameFromLocation()", html)
        self.assertNotIn("https://github.com/huskydoge/Awesome-Loop-Models\">View on GitHub", html)

    def test_site_avoids_remote_google_fonts(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertNotIn("fonts.googleapis.com", html)
        self.assertNotIn("fonts.gstatic.com", html)

    def test_site_uses_a_small_favicon(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('<link rel="icon" type="image/png" href="assets/favicon.png" />', html)

        favicon = FAVICON_PATH.read_bytes()
        self.assertTrue(favicon.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(favicon[12:16], b"IHDR")
        self.assertEqual(int.from_bytes(favicon[16:20], "big"), 64)
        self.assertEqual(int.from_bytes(favicon[20:24], "big"), 64)
        self.assertLess(len(favicon), 20_000)

    def test_repo_docs_describe_submission_guide_and_pr_submission(self):
        contributing = CONTRIBUTING_PATH.read_text(encoding="utf-8")
        readme_header = README_HEADER_PATH.read_text(encoding="utf-8")
        readme_footer = README_FOOTER_PATH.read_text(encoding="utf-8")

        self.assertIn("submit.html", contributing)
        self.assertIn("{{PUBLIC_SUBMIT_URL}}", readme_header)
        self.assertIn("{{PUBLIC_SUBMIT_URL}}", readme_footer)
        self.assertIn("PR Submission Guide", readme_header)
        self.assertIn("PR Submission Guide", readme_footer)
        self.assertIn("Submission Guide", readme_footer)
        self.assertIn("What counts as a blog?", contributing)
        self.assertIn("fork", contributing.lower())
        self.assertIn("pull request", contributing.lower())
        self.assertIn("branch in your fork", contributing.lower())
        self.assertIn("taxonomy change", contributing.lower())
        self.assertIn("controlled taxonomy-vocabulary change", contributing.lower())
        self.assertNotIn("new category", contributing.lower())
        self.assertNotIn("new tags", contributing.lower())
        self.assertIn("generated YAML", readme_footer)
        self.assertNotIn("https://huskydoge.github.io/Awesome-Loop-Models/submit.html", contributing)
        self.assertIn("https://huskydoge.github.io/Awesome-Loop-Models/submit.html", (REPO_ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertNotIn("prefilled GitHub issue", contributing)
        self.assertNotIn("issue body", contributing.lower())
        self.assertNotIn("issue template", contributing.lower())
        self.assertNotIn("GitHub's web editor", contributing)


if __name__ == "__main__":
    unittest.main()
