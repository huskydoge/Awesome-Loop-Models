import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

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


class BuildTaxonomyTests(unittest.TestCase):
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

    def test_foundation_category_is_rejected_as_legacy_shelf(self):
        paper = {"category": "foundation"}
        with self.assertRaisesRegex(ValueError, "invalid category"):
            build.normalize_paper_taxonomy_fields(paper, "paper.yaml")

    def test_analysis_category_is_valid(self):
        paper = {"category": "analysis"}
        normalized = build.normalize_paper_taxonomy_fields(paper, "paper.yaml")
        self.assertEqual(normalized["category"], "analysis")
        self.assertNotIn("category_path", normalized)
        self.assertFalse(normalized["foundation"])

    def test_applications_category_is_valid(self):
        paper = {"category": "applications"}
        normalized = build.normalize_paper_taxonomy_fields(paper, "paper.yaml")
        self.assertEqual(normalized["category"], "applications")
        self.assertNotIn("category_path", normalized)
        self.assertFalse(normalized["foundation"])

    def test_designs_category_is_valid(self):
        paper = {"category": "designs"}
        normalized = build.normalize_paper_taxonomy_fields(paper, "paper.yaml")
        self.assertEqual(normalized["category"], "designs")
        self.assertNotIn("category_path", normalized)
        self.assertFalse(normalized["foundation"])

    def test_legacy_category_values_are_rejected(self):
        legacy_categories = (
            "neural_algorithmic",
            "model_family",
            "training",
            "capability",
            "efficiency",
            "fastrun",
            "slowrun",
            "methods",
            "optimization",
            "architecture",
            "design",
            "algorithm",
        )
        for category in legacy_categories:
            with self.subTest(category=category):
                with self.assertRaisesRegex(ValueError, "invalid category"):
                    build.normalize_paper_taxonomy_fields({"category": category}, "paper.yaml")

    def test_explicit_foundation_flag_keeps_designs_category_and_adds_badge(self):
        paper = {
            "category": "designs",
            "foundation": True,
        }
        normalized = build.normalize_paper_taxonomy_fields(paper, "paper.yaml")
        self.assertEqual(normalized["category"], "designs")
        self.assertNotIn("category_path", normalized)
        self.assertTrue(normalized["foundation"])

    def test_legacy_category_path_mappings_are_rejected(self):
        legacy_cases = (
            {"category": "capability", "category_path": ["theory_mechanisms"]},
            {"category": "efficiency", "category_path": ["training_objectives"]},
            {"category": "fastrun", "category_path": ["architecture-routing"]},
            {"category": "slowrun", "category_path": ["empirical-limits"]},
        )
        for paper in legacy_cases:
            with self.subTest(paper=paper):
                with self.assertRaisesRegex(ValueError, "invalid category"):
                    build.normalize_paper_taxonomy_fields(paper, "paper.yaml")

    def test_category_path_field_is_rejected(self):
        paper = {"category": "designs", "category_path": ["unknown_branch"]}
        with self.assertRaisesRegex(ValueError, "category_path is no longer supported"):
            build.normalize_paper_taxonomy_fields(paper, "paper.yaml")

    def test_subcategory_field_is_rejected(self):
        paper = {"category": "designs", "subcategory": ["anything"]}
        with self.assertRaisesRegex(ValueError, "subcategory is no longer supported"):
            build.normalize_paper_taxonomy_fields(paper, "paper.yaml")

    def test_focus_tags_are_normalized_and_validated(self):
        focus_tags = build.normalize_focus_tags(["architecture", "data", "architecture"], "paper.yaml")
        self.assertEqual(focus_tags, ["architecture", "data"])

    def test_mechanism_tags_are_normalized_and_validated(self):
        mechanism_tags = build.normalize_mechanism_tags(
            ["implicit-layer", "Implicit Layer", "hierarchical-loop", "flat-loop"], "paper.yaml"
        )
        self.assertEqual(mechanism_tags, ["implicit-layer", "hierarchical-loop", "flat-loop"])

        with self.assertRaisesRegex(ValueError, "invalid mechanism_tags"):
            build.normalize_mechanism_tags(["recurrent-depth"], "paper.yaml")

    def test_mechanism_tag_allowlist_is_loop_form_only(self):
        self.assertEqual(
            build.VALID_MECHANISM_TAGS,
            ("hierarchical-loop", "flat-loop", "parallel-loop", "implicit-layer"),
        )
        self.assertFalse(hasattr(build, "MECHANISM_TAG_ALIASES"))
        for old_tag in ("recurrent-depth", "adaptive-compute", "algorithmic-loop", "memory-compression", "recursive-loop", "hierarchy-loop"):
            self.assertNotIn(old_tag, build.VALID_MECHANISM_TAGS)

    def test_mechanism_tag_merging_does_not_map_old_alias_values(self):
        mechanism_tags = build.merge_mechanism_tags(["DEQ", "recurrent-depth", "flat-loop"], ["Implicit Layer"])
        self.assertEqual(mechanism_tags, ["flat-loop", "implicit-layer"])

    def test_focus_tags_do_not_accept_mechanism_aliases(self):
        with self.assertRaisesRegex(ValueError, "invalid focus_tags"):
            build.split_focus_and_mechanism_tags(["architecture", "recurrent-depth"], "paper.yaml")

    def test_domain_tags_do_not_emit_mechanism_tags(self):
        domain_tags, mechanism_tags = build.split_domain_and_mechanism_tags(["implicit-layers", "reasoning"])
        self.assertEqual(domain_tags, ["implicit-layers", "reasoning"])
        self.assertEqual(mechanism_tags, [])

    def test_invalid_focus_tags_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid focus_tags"):
            build.normalize_focus_tags(["made-up-tag"], "paper.yaml")

    def test_legacy_category_guess_helpers_are_removed(self):
        self.assertFalse(hasattr(build, "guess_capability_category"))
        self.assertFalse(hasattr(build, "guess_efficiency_category"))

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

    def test_build_json_trims_briefings_for_browser_without_changing_catalog_entries(self):
        with TemporaryDirectory() as tmpdir:
            json_out = Path(tmpdir) / "papers.json"
            papers = [{"id": "2604.21999", "title": "A paper"}]
            blogs = [{"id": "blog-1", "title": "A blog"}]
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
            payload = json.loads(json_out.read_text(encoding="utf-8"))

        self.assertEqual(payload["papers"], papers)
        self.assertEqual(payload["blogs"], blogs)
        self.assertEqual(payload["meta"]["briefing_total"], 2)
        self.assertEqual(payload["meta"]["latest_briefing_date"], "2026-04-28")
        self.assertEqual(payload["meta"]["briefing_section_title"], "Daily Briefing")
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
        helper_end = html.index("function escapeHtml(str) {", helper_start)
        helpers = html[helper_start:helper_end]
        script = f"""
{helpers}
const result = {expression};
process.stdout.write(JSON.stringify(result));
"""
        output = subprocess.check_output(["node", "-e", script], text=True)
        return json.loads(output)

    @staticmethod
    def run_top_level_tab_block(initial_hash: str, test_body: str):
        """Evaluate the complete production tab state and interaction block in Node."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        state_start = html.index("let ACTIVE_TOP_LEVEL_TAB = 'papers';")
        state_end = html.index("let CURRENT_VIEW = 'category';", state_start)
        block_start = html.index("function normalizeTopLevelTab(tab) {")
        block_end = html.index("const TAG_GROUP_LABELS = {", block_start)
        production_block = html[state_start:state_end] + html[block_start:block_end]
        script = f"""
let browserHash = {json.dumps(initial_hash)};
let focusedTabId = null;
const hashWrites = [];
const renderStatsCalls = [];
const scrollRequests = [];
const animationFrameCallbacks = [];
const windowListeners = {{}};

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

const tabs = [makeTab('papers-tab', true, 0), makeTab('stats-tab', false, -1)];
const papersPanel = {{ hidden: false }};
const statsPanel = {{ hidden: true }};
const bodyClasses = {{}};
const elements = {{
  'papers-tab': tabs[0],
  'stats-tab': tabs[1],
  'papers-panel': papersPanel,
  'stats-panel': statsPanel,
  'section-designs': {{}},
  'section-blogs': {{}}
}};
const document = {{
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
const window = {{
  location: {{}},
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
function scrollToSection(sectionId) {{ scrollRequests.push(sectionId); }}

{production_block}
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
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("Publication date:", html)
        self.assertIn('<input type="date" id="publication-date-start" class="date-input" placeholder="Start" />', html)
        self.assertIn('<input type="date" id="publication-date-end" class="date-input" placeholder="End" />', html)
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

    def test_tag_filter_chips_show_paper_counts(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("tag-filter-chip-count", html)
        self.assertIn("tag.count", html)

    def test_tag_filter_chip_counts_render_as_numbers_only(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("+ '<span class=\"tag-filter-chip-count\">' + tag.count + '</span>'", html)
        self.assertNotIn("tag.count + ' papers'", html)
        self.assertNotIn("tag.count + \" papers\"", html)

    def test_tag_filter_tags_are_sorted_by_descending_count(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("const countDiff = b.count - a.count;", html)
        self.assertIn("if (countDiff !== 0) return countDiff;", html)

    def test_tag_filter_exposes_mechanism_focus_and_domain_groups(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("mechanism: 'Loop Mechanism'", html)
        self.assertIn("focus: 'Focus Tags'", html)
        self.assertIn("domain: 'Domain Tags'", html)
        self.assertIn("paper.mechanism_tags", html)
        self.assertNotIn("paper.category_path", html)
        self.assertNotIn("paper.subcategory", html)
        self.assertNotIn("normalizePathSegments", html)
        self.assertNotIn("family: 'Family Tags'", html)
        self.assertNotIn("paper.family_tags", html)

    def test_paper_titles_link_to_primary_paper_pages(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("function getPrimaryPaperUrl(paper)", html)
        self.assertIn("paper.links.blog", html)
        self.assertIn("paper.links.arxiv", html)
        self.assertIn("paper.links.paper", html)
        self.assertIn('class=\"paper-title-link\"', html)

    def test_foundation_badge_and_category_disclaimer_are_rendered(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("foundation-badge", html)
        self.assertIn("Theoretical and Mechanical Analysis, Architecture and Algorithm Designs, and Applications Focused", html)
        self.assertIn("category-disclaimer", html)

    def test_must_read_star_marker_is_rendered_in_frontend_titles(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("must-read-marker", html)
        self.assertIn("paper.must_read", html)
        self.assertIn("🌟", html)
        self.assertIn("const titleHtml = mustReadMarkerHtml + titleTextHtml + foundationBadgeHtml;", html)
        self.assertIn("mustReadMarkerHtml + '<span>' + highlightQuery(paper.title, query) + '</span>' + foundationBadgeHtml", html)

    def test_filter_sidebar_hooks_exist_and_top_panel_resizer_is_removed(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('id="filter-sidebar-toggle"', html)
        self.assertIn('aria-controls="filter-sidebar-panel"', html)
        self.assertIn('id="filter-sidebar-panel"', html)
        self.assertIn('class="controls-bar filter-sidebar-controls"', html)
        self.assertIn('class="tag-filter-shell filter-sidebar-tag-shell"', html)
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
        self.assertIn(".tag-chip {\n        max-width: 100%;", html)
        self.assertIn("setFilterSidebarOpen(true);", html)
        self.assertNotIn(".filter-sidebar-backdrop", html)
        self.assertNotIn('id="filter-sidebar-backdrop"', html)
        self.assertNotIn("getElementById('filter-sidebar-backdrop')", html)
        self.assertNotIn("body.filter-sidebar-open .filter-sidebar-backdrop", html)
        self.assertNotIn('id="top-panel-resizer"', html)
        self.assertNotIn("function initTopPanelResizer() {", html)
        self.assertNotIn("top-panel-collapsed", html)

    def test_category_counts_are_synced_after_filtering(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("function buildFilteredNodeCounts(filteredPapers) {", html)
        self.assertIn("function syncDynamicCounts(filteredPapers) {", html)
        self.assertIn("counts.blogs = blogCount;", html)
        self.assertIn("syncDynamicCounts(filteredPapers);", html)
        self.assertIn("section.dataset.nodeKey", html)
        self.assertIn("node.dataset.nodeKey", html)

    def test_blogs_section_support_exists_in_frontend(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("let ALL_BLOGS = [];", html)
        self.assertIn("function createBlogTreeNode()", html)
        self.assertIn("BLOG_SECTION_META", html)
        self.assertIn("section-blogs", html)
        self.assertIn("blogs-grid", html)

    def test_catalog_section_builders_create_empty_grid_shells(self):
        """Keep section construction free of eager catalog card rendering."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        category_start = html.index("function createCategorySection(node, pathParts, depth) {")
        category_end = html.index("function createBlogSection()", category_start)
        category_builder = html[category_start:category_end]
        blog_start = category_end
        blog_end = html.index("function renderTreeInto(container)", blog_start)
        blog_builder = html[blog_start:blog_end]
        renderer_start = html.index("function renderAllGrids(q) {")
        renderer_end = html.index("function updateDailyBriefingNotice()", renderer_start)
        renderer = html[renderer_start:renderer_end]

        self.assertIn('grid.dataset.nodeKey = getNodeKey(pathParts);', category_builder)
        self.assertIn('grid.id = "grid-" + pathParts.join("__");', category_builder)
        self.assertIn("grid.id = 'blogs-grid';", blog_builder)
        for builder in (category_builder, blog_builder):
            self.assertNotIn("grid.innerHTML", builder)
            self.assertNotIn("renderCard(", builder)

        self.assertIn(
            "grid.innerHTML = papers.map(function(paper) { return renderCard(paper, query); }).join('');",
            renderer,
        )
        self.assertIn(
            "blogsGrid.innerHTML = blogs.map(function(blog) { return renderCard(blog, query); }).join('');",
            renderer,
        )
        self.assertEqual(html.count("grid.innerHTML ="), 1)
        self.assertEqual(html.count("blogsGrid.innerHTML ="), 1)

    def test_table_rows_are_rendered_only_for_table_view_and_cleared_in_category_view(self):
        """Preserve lazy table rendering when view modes change."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        renderer_start = html.index("function renderAllGrids(q) {")
        renderer_end = html.index("function updateDailyBriefingNotice()", renderer_start)
        renderer = html[renderer_start:renderer_end]

        self.assertIn(
            "if (CURRENT_VIEW === 'table') {\n    renderTableView(query, filteredPapers);\n  } else {",
            renderer,
        )
        self.assertIn("if (tableBody && tableBody.children.length) tableBody.textContent = '';", renderer)
        self.assertEqual(renderer.count("renderTableView(query, filteredPapers);"), 1)

    def test_daily_briefing_notice_exists_in_frontend(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("let ALL_BRIEFINGS = [];", html)
        self.assertIn('<aside class="daily-briefing-notice"', html)
        self.assertIn('id="daily-briefing-notice"', html)
        self.assertIn('id="daily-briefing-notice-summary"', html)
        self.assertIn('id="daily-briefing-notice-candidates"', html)
        self.assertIn('id="daily-briefing-notice-compact"', html)
        self.assertIn('id="daily-briefing-notice-new-papers"', html)
        self.assertIn('id="daily-briefing-notice-toggle"', html)
        self.assertIn('id="daily-briefing-notice-detail"', html)
        self.assertIn('aria-controls="daily-briefing-notice-detail"', html)
        self.assertIn('Details ↓', html)
        self.assertIn('New today:', html)
        self.assertIn('daily-briefing-notice-paper-link', html)
        self.assertIn("function renderDailyBriefingNoticeCandidate(candidate)", html)
        self.assertIn("function isDailyBriefingNewPaper(candidate)", html)
        self.assertIn("function renderDailyBriefingCompactPaper(candidate)", html)
        self.assertIn("function setDailyBriefingNoticeExpanded(expanded)", html)
        self.assertIn("function updateDailyBriefingNotice()", html)
        self.assertIn("ALL_BRIEFINGS = data.briefings || [];", html)
        self.assertIn("updateDailyBriefingNotice();", html)
        self.assertIn(".daily-briefing-notice {\n      left: 32px;", html)
        self.assertIn(".daily-watch-countdown {\n      right: 32px;", html)
        self.assertIn("transform: none;", html)
        self.assertNotIn("transform: rotate(-1.2deg)", html)
        self.assertNotIn("transform: rotate(1.2deg)", html)
        self.assertIn(".papers-only-tools > .search-wrap { order: 2; }", html)
        self.assertIn(".papers-only-tools > .daily-briefing-notice { order: 4; }", html)
        self.assertIn(".papers-only-tools > .daily-watch-countdown { order: 5; }", html)
        self.assertIn("max-height: min(42vh, 320px);", html)
        self.assertIn("max-height: 220px;", html)
        self.assertIn(".daily-briefing-notice-detail::-webkit-scrollbar", html)
        self.assertIn("width: 2px;", html)
        self.assertNotIn("width: 4px;", html)
        self.assertIn("scrollbar-color: var(--scrollbar-thumb) transparent;", html)
        self.assertIn("daily-briefing-notice-source", html)
        self.assertIn("source md ↗", html)
        self.assertIn("body.filter-sidebar-open .daily-briefing-notice", html)
        self.assertNotIn('<a class="daily-briefing-notice"', html)
        self.assertNotIn("daily-briefing-notice-cta", html)
        self.assertNotIn("Read ↗", html)
        self.assertNotIn("function createDailyBriefingTreeNode()", html)
        self.assertNotIn("function createDailyBriefingSection()", html)
        self.assertNotIn("daily-briefing-card", html)
        self.assertNotIn("section-daily-briefing", html)
        self.assertNotIn("daily-briefing-notes", html)
        self.assertNotIn("<summary>Notes</summary>", html)

    def test_papers_side_widgets_reflow_before_they_can_overlap_masthead_tools(self):
        """Side widgets must leave absolute positioning throughout the mid-width range."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        media_start = html.index("@media (max-width: 1344px) {")
        media_end = html.index("/* ── Sidebar contribute link ── */", media_start)
        media_css = html[media_start:media_end]

        self.assertIn(".daily-briefing-notice,\n      .daily-watch-countdown {", media_css)
        for declaration in (
            "position: relative;",
            "top: auto;",
            "left: auto;",
            "right: auto;",
            "width: min(560px, 100%);",
        ):
            self.assertIn(declaration, media_css)
        self.assertNotIn("@media (max-width: 1080px)", html)

    def test_category_section_counts_render_as_numbers_only(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("'<span class=\"category-count\">' + count + '</span>'", html)
        self.assertIn("'<span class=\"category-node-count\">' + count + '</span>'", html)
        self.assertNotIn("count + ' paper' + (count !== 1 ? 's' : '')", html)

    def test_daily_watch_filter_controls_and_table_view_markup_exist(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        for snippet in (
            "Accepted only",
            "Today",
            "w/ code",
            "w/ comments",
            "Category view",
            "Table view",
            "table-view-shell",
            "papers-table-body",
        ):
            self.assertIn(snippet, html)

        header_start = html.index('<table class="papers-table" aria-label="Table view of loop-model resources">')
        header_end = html.index("</thead>", header_start)
        header_snippet = html[header_start:header_end]
        expected_markers = (
            '<th scope="col">Title</th>',
            'class="sort-btn table-sort-btn" data-sort="date" onclick="setSort(\'date\')">Date</button>',
            '<th scope="col">Venue</th>',
            '<th scope="col">Links</th>',
            '<th scope="col">Focus</th>',
            '<th scope="col">Domains</th>',
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
        self.assertNotIn("Added", header_snippet)

    def test_top_level_papers_and_stats_tab_shell_exists(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        for snippet in (
            '<button type="button" class="top-level-tab active" id="papers-tab" role="tab" aria-controls="papers-panel" aria-selected="true" tabindex="0"',
            '<button type="button" class="top-level-tab" id="stats-tab" role="tab" aria-controls="stats-panel" aria-selected="false" tabindex="-1"',
            '<div class="top-level-panel" id="papers-panel" role="tabpanel" aria-labelledby="papers-tab" tabindex="0">',
            '<section class="top-level-panel stats-panel" id="stats-panel" role="tabpanel" aria-labelledby="stats-tab" tabindex="0" hidden>',
        ):
            self.assertIn(snippet, html)

        for snippet in (
            'role="tablist"',
            "let ACTIVE_TOP_LEVEL_TAB = 'papers';",
            "function setTopLevelTab(tab, options) {",
            "function applyTopLevelTab() {",
            "Category view",
            "Table view",
        ):
            self.assertIn(snippet, html)

    def test_top_level_tabs_are_a_global_masthead_mode_switch(self):
        """The site mode switch belongs to the masthead and owns the page layout."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        header_start = html.index("<header>")
        header_end = html.index("</header>", header_start)
        header = html[header_start:header_end]
        masthead_start = header.index('<div class="site-masthead">')
        masthead_end = header.index('<div class="papers-only-tools"', masthead_start)
        masthead = header[masthead_start:masthead_end]
        tools = header[masthead_end:]
        main_start = html.index('<main id="main">')
        main_end = html.index("</main>", main_start)
        main = html[main_start:main_end]

        self.assertIn('<div class="site-brand">', masthead)
        self.assertIn('<div class="top-level-tabs" role="tablist"', masthead)
        self.assertIn('<div class="header-actions">', masthead)
        brand_index = masthead.index('<div class="site-brand">')
        tabs_index = masthead.index('<div class="top-level-tabs" role="tablist"')
        actions_index = masthead.index('<div class="header-actions">')
        self.assertLess(brand_index, tabs_index)
        self.assertLess(tabs_index, actions_index)
        self.assertNotIn("top-level-tabs", main)
        for marker in (
            'class="header-sub"',
            'id="daily-briefing-notice"',
            'id="daily-watch-countdown"',
            'class="search-wrap"',
            'id="filter-sidebar-toggle"',
            'id="filter-sidebar-panel"',
        ):
            self.assertIn(marker, tools)
        for element_id in (
            "papers-tab",
            "stats-tab",
            "header-github-link",
            "daily-briefing-notice",
            "daily-watch-countdown",
        ):
            self.assertEqual(html.count(f'id="{element_id}"'), 1)

        apply_start = html.index("function applyTopLevelTab() {")
        apply_end = html.index("function setTopLevelTab(tab, options) {", apply_start)
        apply_helper = html[apply_start:apply_end]
        self.assertIn("document.body.classList.toggle('stats-mode', isStats);", apply_helper)

        style = html[html.index("<style>"):html.index("</style>")]
        for selector in (
            "body.stats-mode .papers-only-tools",
            "body.stats-mode .sidebar",
            "body.stats-mode .layout",
            "body.stats-mode main",
            "body.stats-mode .stats-panel",
        ):
            self.assertIn(selector, style)
        mobile_start = style.index("@media (max-width: 768px)")
        mobile_css = style[mobile_start:]
        self.assertIn(".site-masthead", mobile_css)
        self.assertIn(".top-level-tabs", mobile_css)
        self.assertIn("flex-basis: 100%;", mobile_css)
        self.assertIn(".site-brand {\n        order: 1;", mobile_css)
        self.assertIn(".site-masthead .top-level-tabs {\n        order: 2;", mobile_css)
        self.assertIn(".site-masthead .header-actions {\n        order: 3;", mobile_css)

        compact_start = style.rindex("@media (max-width: 480px)")
        compact_css = style[compact_start:]
        self.assertIn(".site-masthead .header-actions {\n        order: 3;", compact_css)

    def test_top_level_tabs_restore_hash_and_support_keyboard_navigation(self):
        """Top-level tabs must preserve category hashes and expose full tab keyboard UX."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")

        hash_start = html.index("function getTopLevelTabFromHash(hash) {")
        hash_end = html.index("function applyTopLevelTab() {", hash_start)
        hash_helper = html[hash_start:hash_end]
        self.assertIn("return hash === '#stats' ? 'stats' : 'papers';", hash_helper)

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
        self.assertIn("restoreCategoryHashPosition(window.location.hash)", init_helper)

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
        sections_created_index = build_helper.index("container.appendChild(section)")
        restore_index = build_helper.index("restoreTopLevelTabAfterCatalogLoad();")
        category_restore_index = build_helper.index("restoreCategoryHashPosition(window.location.hash);")
        self.assertLess(data_ready_index, restore_index)
        self.assertLess(sections_created_index, category_restore_index)
        self.assertLess(restore_index, category_restore_index)

        bootstrap_start = html.index("initTopLevelTabInteractions();", restore_end)
        bootstrap_end = html.index("const TAG_GROUP_LABELS = {", bootstrap_start)
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
        """Only the dedicated Stats hash may select Stats; all other hashes select Papers."""
        result = self.run_top_level_tab_block("", """
const hashes = ['#stats', '#papers', '', '#section-designs'];
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
                {"hash": "", "tab": "papers"},
                {"hash": "#section-designs", "tab": "papers"},
            ],
        )

    def test_top_level_keyboard_navigation_behavior(self):
        """Arrow/Home/End activate and focus tabs while Enter/Space retain native click."""
        result = self.run_top_level_tab_block("", """
function runKey(tabIndex, key) {
  setBrowserHash(tabIndex === 0 ? '#papers' : '#stats');
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
  runKey(0, 'ArrowLeft'),
  runKey(1, 'ArrowLeft'),
  runKey(1, 'Home'),
  runKey(0, 'End'),
  runKey(0, 'Enter'),
  runKey(0, ' ')
];
process.stdout.write(JSON.stringify(result));
""")
        expected = []
        for key, source, target in (
            ("ArrowRight", "papers-tab", "stats"),
            ("ArrowRight", "stats-tab", "papers"),
            ("ArrowLeft", "papers-tab", "stats"),
            ("ArrowLeft", "stats-tab", "papers"),
            ("Home", "stats-tab", "papers"),
            ("End", "papers-tab", "stats"),
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
  papersSelected: tabs[0].attributes['aria-selected'],
  statsSelected: tabs[1].attributes['aria-selected'],
  renderCalls: renderStatsCalls,
  hashWrites: hashWrites,
  listeners: {
    papersClick: (tabs[0].listeners.click || []).length,
    papersKeydown: (tabs[0].listeners.keydown || []).length,
    statsClick: (tabs[1].listeners.click || []).length,
    statsKeydown: (tabs[1].listeners.keydown || []).length,
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
        self.assertEqual(result["renderCalls"], [{"ready": False, "error": False}])
        self.assertEqual(result["hashWrites"], [])
        self.assertEqual(
            result["listeners"],
            {
                "papersClick": 1,
                "papersKeydown": 1,
                "statsClick": 1,
                "statsKeydown": 1,
                "hashchange": 1,
            },
        )

    def test_top_level_click_history_reconcile_and_category_restore_behavior(self):
        """Clicks write once; history restores state and section position without rewriting."""
        result = self.run_top_level_tab_block("", """
tabs[1].listeners.click[0]();
const firstClick = { active: ACTIVE_TOP_LEVEL_TAB, writes: hashWrites.slice() };
tabs[1].listeners.click[0]();
const repeatedClick = { active: ACTIVE_TOP_LEVEL_TAB, writes: hashWrites.slice() };

hashWrites.length = 0;
setBrowserHash('#stats');
dispatchWindowEvent('hashchange');
const statsHistory = { active: ACTIVE_TOP_LEVEL_TAB, writes: hashWrites.slice() };

CATALOG_DATA_READY = true;
setBrowserHash('#section-designs');
dispatchWindowEvent('hashchange');
const categoryHistoryBeforeFrame = {
  active: ACTIVE_TOP_LEVEL_TAB,
  hash: window.location.hash,
  writes: hashWrites.slice(),
  queuedFrames: animationFrameCallbacks.length,
  scrolls: scrollRequests.slice()
};
flushAnimationFrames();
const categoryHistoryAfterFrame = { scrolls: scrollRequests.slice() };

scrollRequests.length = 0;
setBrowserHash('#section-designs');
dispatchWindowEvent('hashchange');
setBrowserHash('#stats');
dispatchWindowEvent('hashchange');
flushAnimationFrames();
const staleCategoryFrame = {
  active: ACTIVE_TOP_LEVEL_TAB,
  hash: window.location.hash,
  scrolls: scrollRequests.slice()
};

const result = {
  firstClick: firstClick,
  repeatedClick: repeatedClick,
  statsHistory: statsHistory,
  categoryHistoryBeforeFrame: categoryHistoryBeforeFrame,
  categoryHistoryAfterFrame: categoryHistoryAfterFrame,
  staleCategoryFrame: staleCategoryFrame
};
process.stdout.write(JSON.stringify(result));
""")
        self.assertEqual(result["firstClick"], {"active": "stats", "writes": ["#stats"]})
        self.assertEqual(result["repeatedClick"], {"active": "stats", "writes": ["#stats"]})
        self.assertEqual(result["statsHistory"], {"active": "stats", "writes": []})
        self.assertEqual(
            result["categoryHistoryBeforeFrame"],
            {
                "active": "papers",
                "hash": "#section-designs",
                "writes": [],
                "queuedFrames": 1,
                "scrolls": [],
            },
        )
        self.assertEqual(result["categoryHistoryAfterFrame"], {"scrolls": ["section-designs"]})
        self.assertEqual(
            result["staleCategoryFrame"],
            {"active": "stats", "hash": "#stats", "scrolls": []},
        )

    def test_catalog_load_reconcile_preserves_empty_hash_user_choice_but_honors_hash(self):
        """Load completion preserves an unrepresented user choice unless a hash drives state."""
        result = self.run_top_level_tab_block("", """
tabs[1].listeners.click[0]();
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
const explicitCategory = ACTIVE_TOP_LEVEL_TAB;

process.stdout.write(JSON.stringify({
  emptyHashAfterClick: emptyHashAfterClick,
  explicitPapers: explicitPapers,
  explicitStats: explicitStats,
  explicitCategory: explicitCategory
}));
""")
        self.assertEqual(
            result,
            {
                "emptyHashAfterClick": "stats",
                "explicitPapers": "papers",
                "explicitStats": "stats",
                "explicitCategory": "papers",
            },
        )

    def test_paper_section_navigation_leaves_stats_and_restores_repeated_hash(self):
        """Sidebar navigation must reveal Papers and restore even when the hash is unchanged."""
        result = self.run_top_level_tab_block("#stats", """
CATALOG_DATA_READY = true;
navigateToPaperSection('section-designs');
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
navigateToPaperSection('section-designs');
const repeatedNavigation = {
  active: ACTIVE_TOP_LEVEL_TAB,
  hash: window.location.hash,
  writes: hashWrites.slice(),
  queuedFrames: animationFrameCallbacks.length
};
flushAnimationFrames();

process.stdout.write(JSON.stringify({
  firstNavigation: firstNavigation,
  firstScrolls: firstScrolls,
  repeatedNavigation: repeatedNavigation,
  repeatedScrolls: scrollRequests
}));
""")
        self.assertEqual(
            result["firstNavigation"],
            {
                "active": "papers",
                "hash": "#section-designs",
                "writes": ["#section-designs"],
                "papersHidden": False,
                "statsHidden": True,
                "queuedFrames": 0,
            },
        )
        self.assertEqual(result["firstScrolls"], ["section-designs"])
        self.assertEqual(
            result["repeatedNavigation"],
            {
                "active": "papers",
                "hash": "#section-designs",
                "writes": [],
                "queuedFrames": 1,
            },
        )
        self.assertEqual(result["repeatedScrolls"], ["section-designs"])

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
            "slicePublicationRange",
            "buildReleaseStatsSummary",
            "buildAnnualReleaseSeries",
            "getLatestReleasedPapers",
        ):
            self.assertIn(f"function {function_name}(", helpers)
        self.assertNotIn("added_date", helpers)
        self.assertIn("range === '90d'", helpers)
        self.assertIn("range === 'all'", helpers)
        self.assertIn("windowSize = 14", helpers)
        self.assertIn("windowSize = 30", helpers)
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
  ]);
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
    emptySummary: buildReleaseStatsSummary(null, null, null),
    summary: buildReleaseStatsSummary(summaryPapers, summaryDaily, summaryMonthly),
    annual: buildAnnualReleaseSeries([
      { published_date: '2026-01-01' },
      { published_date: '2024-12-31' },
      { published_date: '2025-06-15' },
      { published_date: '2024-01-01' },
      { published_date: 'invalid' },
      { added_date: '2023-01-01' }
    ]),
    latest: getLatestReleasedPapers(summaryPapers, 5).map(function(paper) { return paper.id; }),
    noLatest: getLatestReleasedPapers(null, -1)
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
                "latestReleaseDate": None,
                "peakMonth": None,
            },
        )
        self.assertEqual(result["averages"], [2, 3, 2])
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
                    "windowSize": 30,
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
            {"range": "1y", "granularity": "day", "windowSize": 30, "series": []},
        )
        self.assertEqual(result["summary"]["totalPapers"], 11)
        self.assertEqual(result["summary"]["releasesLast30Days"], 3)
        self.assertEqual(result["summary"]["latestReleaseDate"], "2026-07-03")
        self.assertEqual(
            result["summary"]["peakMonth"],
            {"key": "2026-01", "label": "2026-01", "count": 3, "cumulative": 3},
        )
        self.assertEqual(
            result["annual"],
            [
                {"key": "2024", "label": "2024", "count": 2},
                {"key": "2025", "label": "2025", "count": 1},
                {"key": "2026", "label": "2026", "count": 1},
            ],
        )
        self.assertEqual(
            result["latest"],
            ["latest-a1", "latest-a2", "latest-b", "june", "mar-a"],
        )
        self.assertEqual(result["noLatest"], [])

    def test_stats_panel_has_kpis_charts_and_accessible_fallback_summaries(self):
        """Stats markup must expose useful values beyond SVG color or hover states."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        stats_start = html.index('<section class="top-level-panel stats-panel"')
        stats_end = html.index("</section>", stats_start)
        stats_markup = html[stats_start:stats_end]

        for marker in (
            'class="stats-kpis"',
            'id="stats-total-papers"',
            'id="stats-latest-seven"',
            'id="stats-date-coverage"',
            'id="stats-peak-day"',
            'id="catalog-growth-chart"',
            'id="publication-trend-chart"',
            'id="catalog-growth-summary"',
            'id="publication-trend-summary"',
            "Catalog Growth",
            "Publication Trend",
            "Papers in this catalog by publication month",
            "latest 7 recorded days",
        ):
            self.assertIn(marker, stats_markup)
        self.assertIn('aria-live="polite"', stats_markup)
        self.assertNotIn("stats-panel-placeholder", stats_markup)

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
        state_end = html.index("const TAG_GROUP_LABELS", state_start)
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

    def test_timeline_renderer_uses_pixel_spaced_tick_helper(self):
        """SVG x labels must come from the shared collision-resistant selector."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        helper_start = html.index("function selectTimelineTickIndices(")
        helper_end = html.index("function renderTimelineChart(", helper_start)
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

    def test_stats_renderers_use_safe_accessible_inline_svg(self):
        """Timeline rendering must use DOM APIs and include axes plus text alternatives."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        timeline_start = html.index("function renderTimelineChart(container, series, options) {")
        timeline_end = html.index("function renderStatsPanel() {", timeline_start)
        timeline_source = html[timeline_start:timeline_end]
        stats_start = timeline_end
        stats_end = html.index("function escapeHtml(str) {", stats_start)
        stats_source = html[stats_start:stats_end]

        for marker in (
            "createElementNS",
            "'title'",
            "'desc'",
            "'viewBox'",
            "timeline-grid",
            "timeline-bar",
            "timeline-line",
            "timeline-axis-left",
            "timeline-axis-right",
            "timeline-empty",
            "textContent",
        ):
            self.assertIn(marker, timeline_source)
        self.assertIn("setAttribute", timeline_source)
        self.assertNotIn("innerHTML", timeline_source)
        self.assertNotIn("innerHTML", stats_source)
        self.assertIn("buildDailyPublicationSeries(ALL_PAPERS)", stats_source)
        self.assertIn("buildMonthlyPublicationSeries(ALL_PAPERS)", stats_source)
        self.assertIn("HAS_RENDERED_STATS = true;", stats_source)
        self.assertIn("if (!CATALOG_DATA_READY)", stats_source)

    def test_stats_charts_are_editorial_responsive_and_scroll_locally(self):
        """Chart CSS must retain readable SVG width without overflowing the page."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        stats_start = html.index("    .stats-panel {")
        stats_end = html.index("    /* ── Category Section ── */", stats_start)
        stats_css = html[stats_start:stats_end]

        scroll_start = stats_css.index("    .stats-chart-scroll {")
        scroll_end = stats_css.index("\n    }", scroll_start)
        scroll_rule = stats_css[scroll_start:scroll_end]
        chart_start = stats_css.index("    .timeline-chart {")
        chart_end = stats_css.index("\n    }", chart_start)
        chart_rule = stats_css[chart_start:chart_end]
        card_start = stats_css.index("    .stats-chart-card {")
        card_end = stats_css.index("\n    }", card_start)
        card_rule = stats_css[card_start:card_end]
        grid_start = stats_css.index("    .timeline-grid {")
        grid_end = stats_css.index("\n    }", grid_start)
        grid_rule = stats_css[grid_start:grid_end]
        bar_start = stats_css.index("    .timeline-bar {")
        bar_end = stats_css.index("\n    }", bar_start)
        bar_rule = stats_css[bar_start:bar_end]
        line_start = stats_css.index("    .timeline-line {")
        line_end = stats_css.index("\n    }", line_start)
        line_rule = stats_css[line_start:line_end]

        self.assertIn("width: 100%;", scroll_rule)
        self.assertIn("max-width: 100%;", scroll_rule)
        self.assertIn("overflow-x: auto;", scroll_rule)
        self.assertIn("min-width: 760px;", chart_rule)
        self.assertIn("color: var(--text-muted);", chart_rule)
        self.assertIn("border: 1px solid var(--border);", card_rule)
        self.assertIn("stroke: var(--border);", grid_rule)
        self.assertIn("fill: var(--accent);", bar_rule)
        self.assertIn("stroke: var(--accent2);", line_rule)
        self.assertNotIn("animation:", stats_css)

    def test_stats_small_text_uses_accessible_muted_color(self):
        """Small Stats labels must avoid the lower-contrast decorative text token."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        stats_start = html.index("    .stats-panel {")
        stats_end = html.index("    /* ── Category Section ── */", stats_start)
        stats_css = html[stats_start:stats_end]
        note_start = stats_css.index("    .stats-kpi-note {")
        note_end = stats_css.index("\n    }", note_start)
        note_rule = stats_css[note_start:note_end]
        ticks_start = stats_css.index("    .timeline-axis-label,")
        ticks_end = stats_css.index("\n    }", ticks_start)
        ticks_rule = stats_css[ticks_start:ticks_end]

        self.assertIn("color: var(--text-muted);", note_rule)
        self.assertNotIn("var(--text-dim)", note_rule)
        self.assertIn("fill: var(--text-muted);", ticks_rule)
        self.assertNotIn("var(--text-dim)", ticks_rule)

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

    def test_today_filter_uses_published_date_not_added_date(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("function matchTodayOnly(paper) {", html)
        matcher_start = html.index("function matchTodayOnly(paper) {")
        matcher_end = html.index("function matchHasCodeOnly(paper)", matcher_start)
        matcher_snippet = html[matcher_start:matcher_end]
        self.assertIn("getPaperPublicationDateValue(paper) === getRepoTodayString()", matcher_snippet)
        self.assertNotIn("paper.added_date", matcher_snippet)

    def test_daily_watch_countdown_widget_and_schedule_logic_exist(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('<script src="assets/daily-watch-countdown.js"></script>', html)
        self.assertIn('id="daily-watch-countdown"', html)
        self.assertIn('id="daily-watch-countdown-value"', html)
        self.assertIn('id="daily-watch-countdown-meta"', html)
        self.assertIn("20:05 ET Sunday–Thursday", html)
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
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        render_start = html.index("function renderCard(paper, query) {")
        render_end = html.index("// ── State & Category Tree", render_start)
        render_snippet = html[render_start:render_end]

        self.assertIn("const paperDisplayDate = getPaperDisplayDate(paper);", render_snippet)
        self.assertIn("authorsStr + ' · ' + paperDisplayDate", render_snippet)
        self.assertIn("'<div class=\"paper-meta\">' + paperDisplayDate + '</div>'", render_snippet)
        self.assertNotIn("authorsStr + ' · ' + paper.year", render_snippet)

    def test_table_view_rows_keep_compact_link_rendering_hooks(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("function renderCompactPaperLinksHtml(paper)", html)
        self.assertIn("'<td class=\"paper-table-links-cell\">' + compactLinksHtml + '</td>'", html)
        self.assertIn("'<div class=\"paper-table-links\">' + linksHtml + '</div>'", html)

    def test_table_view_rows_use_button_disclosure_markup(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("const detailRowId = 'paper-table-detail-' + paperId;", html)
        self.assertIn('class="paper-table-disclosure"', html)
        self.assertIn("aria-controls=\"' + detailRowId + '\"", html)
        self.assertIn("id=\"' + detailRowId + '\"", html)
        self.assertNotIn('tabindex="0"', html)

    def test_table_view_toggle_ignores_interactive_children_and_syncs_button_state(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        guard = "event.target.closest('a, button, summary, input, select, textarea')"
        self.assertEqual(html.count(guard), 2)
        self.assertIn("const disclosureButton = summaryRow.querySelector('.paper-table-disclosure');", html)
        self.assertIn("if (disclosureButton) disclosureButton.setAttribute('aria-expanded', expanded ? 'true' : 'false');", html)

    def test_daily_watch_filters_and_table_view_have_frontend_hooks(self):
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("paper.entry_type !== 'blog' && paper.venue !== 'arXiv'", html)
        self.assertIn("function getRepoTodayString()", html)
        self.assertIn("generated_local_date", html)
        self.assertIn("getPaperPublicationDateValue(paper) === getRepoTodayString()", html)
        self.assertIn("function renderTableView(query, papers)", html)
        self.assertIn("function toggleTableRow(paperId)", html)
        self.assertIn("function setView(view)", html)

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
        scroll_end = html.index("function initTreeInteractions()", scroll_start)
        scroll_snippet = html[scroll_start:scroll_end]

        self.assertIn("window.innerWidth <= 768", scroll_snippet)
        self.assertIn("window.scrollTo", scroll_snippet)
        self.assertIn("scrollRoot.scrollTo", scroll_snippet)

    def test_tree_links_use_top_level_paper_section_navigation(self):
        """Tree links must route through the tab/hash state machine before scrolling."""
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        init_start = html.index("function initTreeInteractions()")
        init_end = html.index("function initScrollObserver()", init_start)
        init_source = html[init_start:init_end]

        self.assertIn("navigateToPaperSection(sectionId);", init_source)
        self.assertNotIn("scrollToSection(sectionId);", init_source)

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
        self.assertEqual(result["iso"], "2026-04-24T00:05:00.000Z")
        self.assertEqual(result["weekday"], 4)
        self.assertEqual(result["label"], "Thu 20:05 ET")

    def test_daily_watch_helper_rolls_thursday_night_to_sunday(self):
        result = self.run_daily_watch_helper("2026-04-23T21:00:00-04:00")
        self.assertEqual(result["iso"], "2026-04-27T00:05:00.000Z")
        self.assertEqual(result["weekday"], 0)
        self.assertEqual(result["label"], "Sun 20:05 ET")

    def test_daily_watch_helper_handles_standard_time_offset(self):
        result = self.run_daily_watch_helper("2026-01-05T12:00:00-05:00")
        self.assertEqual(result["iso"], "2026-01-06T01:05:00.000Z")
        self.assertEqual(result["weekday"], 1)
        self.assertEqual(result["label"], "Mon 20:05 ET")


class CanonicalPaperMetadataTests(unittest.TestCase):
    def test_paper_2602_10520_is_classified_as_designs(self):
        paper_path = REPO_ROOT / "papers" / "2602.10520.yaml"
        data = yaml.safe_load(paper_path.read_text(encoding="utf-8")) or {}

        self.assertEqual(data.get("category"), "designs")
        self.assertNotIn("category_path", data)

    def test_all_repo_paper_yaml_categories_are_canonical(self):
        canonical_categories = {
            "applications",
            "analysis",
            "designs",
        }
        legacy_categories = {
            "foundation",
            "slowrun",
            "fastrun",
            "algorithm",
            "model_family",
            "design",
            "capability",
            "methods",
            "efficiency",
            "optimization",
            "training",
            "architecture",
        }
        legacy_path_segments = {
            "vision",
            "robotics_vla",
            "scientific_imaging",
            "implicit_equilibrium",
            "recursive_reasoning",
            "adaptive_inference",
            "routing_mixture",
            "memory_compression",
            "parallel_execution",
            "capability-scaling",
            "theory-mechanisms",
            "empirical-limits",
            "adaptive-budgeting",
            "architecture-routing",
            "training-recipes",
            "architecture_capability",
            "theory_mechanisms",
            "empirical_limits",
            "scaling_limits",
            "adaptive_budgeting",
            "routing_allocation",
            "state_compression",
            "training_objectives",
        }

        violations = []
        for yaml_path in sorted((REPO_ROOT / "papers").glob("*.yaml")):
            if yaml_path.name.startswith("_"):
                continue
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            category = data.get("category")
            if category not in canonical_categories:
                violations.append(f"{yaml_path.name}: non-canonical category {category}")
            if category in legacy_categories:
                violations.append(f"{yaml_path.name}: legacy category {category}")

            raw_path = data.get("category_path") or []
            if isinstance(raw_path, str):
                path_segments = [segment.strip() for segment in raw_path.split("/") if segment.strip()]
            else:
                path_segments = [str(segment).strip() for segment in raw_path if str(segment).strip()]
            if path_segments:
                violations.append(f"{yaml_path.name}: canonical paper YAML should omit category_path")
            for segment in path_segments:
                if segment in legacy_path_segments:
                    violations.append(f"{yaml_path.name}: legacy category_path segment {segment}")

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

    def test_all_repo_blog_yaml_files_have_publication_dates_and_no_taxonomy_fields(self):
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
            if data.get("category") not in (None, ""):
                violations.append(f"{yaml_path.name}: blogs must not set category")
            if data.get("category_path") not in (None, "", []):
                violations.append(f"{yaml_path.name}: blogs must not set category_path")
            if data.get("foundation") not in (None, False, ""):
                violations.append(f"{yaml_path.name}: blogs must not set foundation")
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

    def test_build_readme_sorts_each_category_by_publication_date_desc(self):
        papers = [
            {
                "title": "Older Foundation Loop Paper",
                "authors": "Alice Example",
                "venue": "ICLR",
                "year": 2025,
                "published_date": "2025-12-31",
                "category": "designs",
                "foundation": True,
                "links": {},
            },
            {
                "title": "Newest Loop Paper",
                "authors": "Bob Example",
                "venue": "ICLR",
                "year": 2026,
                "published_date": "2026-04-26",
                "category": "designs",
                "links": {},
            },
            {
                "title": "Middle Loop Paper",
                "authors": "Carol Example",
                "venue": "ICLR",
                "year": 2026,
                "published_date": "2026-02-03",
                "category": "designs",
                "links": {},
            },
        ]

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
                build.build_readme(papers, [], {"public_pages_base": "https://example.test/repo"})

            readme = readme_path.read_text(encoding="utf-8")

        newest_index = readme.index("Newest Loop Paper")
        middle_index = readme.index("Middle Loop Paper")
        older_index = readme.index("Older Foundation Loop Paper")
        self.assertLess(newest_index, middle_index)
        self.assertLess(middle_index, older_index)

    def test_readme_paper_entries_hide_summary_tags_and_use_badge_links(self):
        paper = {
            "title": "Loop Test Paper",
            "authors": "Alice Example, Bob Example",
            "venue": "ICLR",
            "year": 2026,
            "desc": "Introduces a compact loop-model benchmark entry.",
            "tags": ["LoopTest"],
            "mechanism_tags": ["flat-loop"],
            "focus_tags": ["architecture"],
            "domain_tags": ["reasoning"],
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

        self.assertIn("<summary><strong>Loop Test Paper</strong>", markdown)
        self.assertNotIn("<code>LoopTest</code>", summary_html)
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
        self.assertIn("<div><strong>Loop Mechanism:</strong> flat-loop</div>", markdown)
        self.assertIn("<div><strong>Focus:</strong> architecture</div>", markdown)
        self.assertIn("<div><strong>Domains:</strong> reasoning</div>", markdown)
        self.assertIn("<div><strong>TL;DR:</strong> Introduces a compact loop-model benchmark entry.</div>", markdown)

    def test_foundation_paper_entries_hide_foundation_summary_chip(self):
        paper = {
            "title": "Foundation Loop Paper",
            "authors": "Alice Example",
            "venue": "NeurIPS",
            "year": 2020,
            "foundation": True,
            "links": {
                "paper": "https://example.com/foundation-paper",
            },
        }

        markdown = build._paper_to_md(paper)

        self.assertIn("<summary><strong>Foundation Loop Paper</strong>", markdown)
        self.assertNotIn(f"<code>{build.FOUNDATION_LABEL}</code>", markdown)

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

    def test_readme_blog_entries_hide_summary_tags(self):
        blog = {
            "title": "Loop Blog",
            "authors": "Alice Example",
            "venue": "Blog",
            "year": 2026,
            "entry_type": "blog",
            "desc": "Long-form note on loop-model training.",
            "tags": ["BPTT", "checkpointing"],
            "focus_tags": ["training-algorithm"],
            "domain_tags": ["efficient-loop"],
            "links": {
                "blog": "https://example.com/loop-blog",
            },
        }

        markdown = build._paper_to_md(blog)
        summary_start = markdown.index("<summary>")
        summary_end = markdown.index("</summary>")
        summary_html = markdown[summary_start:summary_end]

        self.assertIn("<summary><strong>Loop Blog</strong>", markdown)
        self.assertNotIn("<code>BPTT</code>", summary_html)
        self.assertNotIn("<code>checkpointing</code>", summary_html)
        self.assertIn("<div><strong>Focus:</strong> training-algorithm</div>", markdown)
        self.assertIn("<div><strong>Domains:</strong> efficient-loop</div>", markdown)
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


class LoadPapersRegressionTests(unittest.TestCase):
    def test_load_papers_rejects_legacy_family_tags(self):
        with TemporaryDirectory() as tmpdir:
            papers_dir = Path(tmpdir)
            paper_path = papers_dir / "2603.08391.yaml"
            paper_path.write_text(
                yaml.safe_dump(
                    {
                        "title": "Deep Equilibrium Loop Test Paper",
                        "authors": ["Test Author"],
                        "year": 2026,
                        "published_date": "2026-03-10",
                        "venue": "arXiv",
                        "category": "analysis",
                        "mechanism_tags": ["implicit-layer"],
                        "family_tags": ["deep-equilibrium", "hierarchical-recursion"],
                        "tags": ["DEQ", "HRM"],
                        "domain_tags": ["implicit-layers", "reasoning"],
                        "links": {
                            "arxiv": "https://arxiv.org/abs/2603.08391",
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            with patch.object(build, "PAPERS_DIR", papers_dir):
                with self.assertRaisesRegex(ValueError, "family_tags is no longer supported"):
                    build.load_papers()

    def test_load_papers_requires_explicit_loop_mechanism_tags(self):
        with TemporaryDirectory() as tmpdir:
            papers_dir = Path(tmpdir)
            paper_path = papers_dir / "2603.08391.yaml"
            paper_path.write_text(
                yaml.safe_dump(
                    {
                        "title": "Deep Equilibrium Loop Test Paper",
                        "authors": ["Test Author"],
                        "year": 2026,
                        "published_date": "2026-03-10",
                        "venue": "arXiv",
                        "category": "analysis",
                        "tags": ["DEQ", "HRM"],
                        "domain_tags": ["implicit-layers", "reasoning"],
                        "links": {
                            "arxiv": "https://arxiv.org/abs/2603.08391",
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            with patch.object(build, "PAPERS_DIR", papers_dir):
                with self.assertRaisesRegex(ValueError, "missing mechanism_tags"):
                    build.load_papers()

    def test_load_papers_derives_alphaxiv_from_arxiv_links(self):
        with TemporaryDirectory() as tmpdir:
            papers_dir = Path(tmpdir)
            paper_path = papers_dir / "2603.08391.yaml"
            paper_path.write_text(
                yaml.safe_dump(
                    {
                        "title": "Loop Test Paper",
                        "year": 2026,
                        "published_date": "2026-03-10",
                        "venue": "arXiv",
                        "category": "analysis",
                        "mechanism_tags": ["flat-loop"],
                        "links": {
                            "arxiv": "https://arxiv.org/abs/2603.08391",
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            with patch.object(build, "PAPERS_DIR", papers_dir):
                papers = build.load_papers()

        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["links"]["alphaxiv"], "https://www.alphaxiv.org/abs/2603.08391")

    def test_load_papers_requires_published_date(self):
        with TemporaryDirectory() as tmpdir:
            papers_dir = Path(tmpdir)
            paper_path = papers_dir / "2603.08391.yaml"
            paper_path.write_text(
                yaml.safe_dump(
                    {
                        "title": "Loop Test Paper",
                        "year": 2026,
                        "venue": "arXiv",
                        "category": "analysis",
                        "mechanism_tags": ["flat-loop"],
                        "links": {
                            "arxiv": "https://arxiv.org/abs/2603.08391",
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            with patch.object(build, "PAPERS_DIR", papers_dir):
                with self.assertRaisesRegex(ValueError, "missing required published_date"):
                    build.load_papers()

    def test_load_papers_preserves_must_read_flag(self):
        with TemporaryDirectory() as tmpdir:
            papers_dir = Path(tmpdir)
            paper_path = papers_dir / "2603.08391.yaml"
            paper_path.write_text(
                yaml.safe_dump(
                    {
                        "title": "Must Read Loop Test Paper",
                        "authors": ["Test Author"],
                        "year": 2026,
                        "published_date": "2026-03-10",
                        "venue": "arXiv",
                        "category": "analysis",
                        "must_read": True,
                        "mechanism_tags": ["flat-loop"],
                        "links": {
                            "arxiv": "https://arxiv.org/abs/2603.08391",
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            with patch.object(build, "PAPERS_DIR", papers_dir):
                papers = build.load_papers()

        self.assertEqual(len(papers), 1)
        self.assertTrue(papers[0].get("must_read"))


class LoadBlogsRegressionTests(unittest.TestCase):
    def test_load_blogs_requires_links_blog(self):
        with TemporaryDirectory() as tmpdir:
            blogs_dir = Path(tmpdir)
            blog_path = blogs_dir / "loop-blog.yaml"
            blog_path.write_text(
                yaml.safe_dump(
                    {
                        "title": "Loop Blog",
                        "year": 2026,
                        "published_date": "2026-04-21",
                        "venue": "Lab Blog",
                        "focus_tags": ["architecture"],
                        "links": {},
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            with patch.object(build, "BLOGS_DIR", blogs_dir):
                with self.assertRaisesRegex(ValueError, "blogs require links.blog"):
                    build.load_blogs()

    def test_load_blogs_requires_explicit_loop_mechanism_tags(self):
        with TemporaryDirectory() as tmpdir:
            blogs_dir = Path(tmpdir)
            blog_path = blogs_dir / "loop-blog.yaml"
            blog_path.write_text(
                yaml.safe_dump(
                    {
                        "title": "Loop Blog",
                        "year": 2026,
                        "published_date": "2026-04-21",
                        "venue": "Lab Blog",
                        "focus_tags": ["architecture"],
                        "links": {
                            "blog": "https://example.com/loop-blog",
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            with patch.object(build, "BLOGS_DIR", blogs_dir):
                with self.assertRaisesRegex(ValueError, "missing mechanism_tags"):
                    build.load_blogs()

    def test_load_blogs_preserves_flat_blog_metadata(self):
        with TemporaryDirectory() as tmpdir:
            blogs_dir = Path(tmpdir)
            blog_path = blogs_dir / "loop-blog.yaml"
            blog_path.write_text(
                yaml.safe_dump(
                    {
                        "title": "Loop Blog",
                        "authors": ["Test Author"],
                        "year": 2026,
                        "published_date": "2026-04-21",
                        "venue": "X Article",
                        "focus_tags": ["architecture"],
                        "mechanism_tags": ["flat-loop"],
                        "domain_tags": ["language-modeling"],
                        "links": {
                            "blog": "https://example.com/loop-blog",
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            with patch.object(build, "BLOGS_DIR", blogs_dir):
                blogs = build.load_blogs()

        self.assertEqual(len(blogs), 1)
        self.assertEqual(blogs[0]["entry_type"], "blog")
        self.assertEqual(blogs[0]["links"]["blog"], "https://example.com/loop-blog")
        self.assertEqual(blogs[0]["venueClass"], build.BLOG_VENUE_CLASS)
        self.assertNotIn("category", blogs[0])


class TagsReferenceRegressionTests(unittest.TestCase):
    def test_render_tags_reference_text_includes_sections_and_counts(self):
        text = build.render_tags_reference_text(
            [
                {
                    "mechanism_tags": ["flat-loop"],
                    "focus_tags": ["architecture"],
                    "domain_tags": ["reasoning"],
                    "tags": ["LoopLM"],
                }
            ],
            [
                {
                    "mechanism_tags": ["flat-loop", "implicit-layer"],
                    "focus_tags": ["architecture", "data"],
                    "domain_tags": ["reasoning", "vision"],
                    "tags": ["LoopLM", "BlogAlias"],
                }
            ],
        )

        self.assertIn("# TAGS", text)
        self.assertIn("## Loop Mechanism (`mechanism_tags`)", text)
        self.assertIn("`flat-loop` (2)", text)
        self.assertIn("`implicit-layer` (1)", text)
        self.assertNotIn("family_tags", text)
        self.assertNotIn("universal-transformer", text)
        self.assertIn("## focus_tags", text)
        self.assertIn("`architecture` (2)", text)
        self.assertIn("`data` (1)", text)
        self.assertIn("## domain_tags", text)
        self.assertIn("`reasoning` (2)", text)
        self.assertIn("`vision` (1)", text)
        self.assertIn("## tags", text)
        self.assertIn("alias tags currently used across the repo", text)
        self.assertNotIn("alias / mechanism", text)
        self.assertIn("`LoopLM` (2)", text)
        self.assertIn("`BlogAlias` (1)", text)

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
                "tags": ["forbidden-paper-alias"],
                "mechanism_tags": ["flat-loop"],
                "focus_tags": ["architecture"],
                "domain_tags": ["vision"],
            },
            {
                "source_path": "papers/a.yaml",
                "mechanism_tags": ["flat-loop", "implicit-layer"],
                "focus_tags": ["data"],
                "domain_tags": ["reasoning", "vision"],
            },
        ]
        blogs = [
            {
                "source_path": "blogs/c.yaml",
                "title": "forbidden blog title",
                "mechanism_tags": [],
                "focus_tags": [],
                "domain_tags": [],
            },
            {
                "source_path": "papers/a.yaml",
                "mechanism_tags": [],
                "focus_tags": [],
                "domain_tags": [],
            },
        ]

        payload = build.render_submission_metadata(papers, blogs)
        reversed_payload = build.render_submission_metadata(list(reversed(papers)), list(reversed(blogs)))

        self.assertEqual(payload, reversed_payload)
        self.assertEqual(set(payload), {"existing_paths", "tag_inventories"})
        self.assertEqual(
            payload["existing_paths"],
            ["blogs/c.yaml", "papers/a.yaml", "papers/b.yaml"],
        )
        self.assertEqual(set(payload["tag_inventories"]), {"mechanism", "focus", "domain"})
        self.assertEqual(
            payload["tag_inventories"]["mechanism"],
            [
                {"label": "flat-loop", "count": 2},
                {"label": "implicit-layer", "count": 1},
                {"label": "hierarchical-loop", "count": 0},
                {"label": "parallel-loop", "count": 0},
            ],
        )
        self.assertEqual(
            payload["tag_inventories"]["focus"],
            [
                {"label": "architecture", "count": 1},
                {"label": "data", "count": 1},
                {"label": "inference-algorithm", "count": 0},
                {"label": "objective-loss", "count": 0},
                {"label": "training-algorithm", "count": 0},
            ],
        )
        self.assertEqual(
            payload["tag_inventories"]["domain"],
            [
                {"label": "vision", "count": 2},
                {"label": "reasoning", "count": 1},
            ],
        )
        for inventory in payload["tag_inventories"].values():
            for row in inventory:
                self.assertEqual(set(row), {"label", "count"})

        serialized = json.dumps(payload)
        for forbidden_field in (
            '"title"',
            '"authors"',
            '"desc"',
            '"metrics"',
            '"links"',
            '"briefings"',
            '"tags"',
            '"papers"',
            '"blogs"',
            '"generated"',
        ):
            self.assertNotIn(forbidden_field, serialized)
        for forbidden_value in (
            "forbidden paper title",
            "forbidden paper authors",
            "forbidden paper description",
            "forbidden-paper-alias",
            "forbidden blog title",
        ):
            self.assertNotIn(forbidden_value, serialized)

    def test_build_submission_metadata_writes_rendered_payload(self):
        papers = [{"source_path": "papers/a.yaml", "mechanism_tags": ["flat-loop"]}]
        blogs = [{"source_path": "blogs/b.yaml", "domain_tags": ["reasoning"]}]

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "submission-meta.json"
            with patch.object(build, "SUBMISSION_META_OUT", output_path):
                build.build_submission_metadata(papers, blogs)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(payload, build.render_submission_metadata(papers, blogs))

    def test_loaded_entries_expose_source_paths(self):
        paper = build.load_papers()[0]
        blog = build.load_blogs()[0]

        self.assertTrue(paper["source_file"].endswith(".yaml"))
        self.assertTrue(paper["source_path"].startswith("papers/"))
        self.assertTrue(blog["source_file"].endswith(".yaml"))
        self.assertTrue(blog["source_path"].startswith("blogs/"))

    def test_generated_json_uses_loop_form_mechanism_allowlist(self):
        payload = json.loads((REPO_ROOT / "papers.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["mechanism_tags"], list(build.VALID_MECHANISM_TAGS))
        allowed = set(build.VALID_MECHANISM_TAGS)
        for entry in [*payload["papers"], *payload.get("blogs", [])]:
            self.assertTrue(entry.get("mechanism_tags"), entry.get("source_path"))
            self.assertLessEqual(set(entry.get("mechanism_tags", [])), allowed, entry.get("source_path"))
        for paper in payload["papers"]:
            self.assertNotIn("category_path", paper, paper.get("source_path"))

    def test_blog_yaml_files_use_published_date_prefix(self):
        blog_files = [path.name for path in (REPO_ROOT / "blogs").glob("*.yaml") if not path.name.startswith("_")]
        self.assertTrue(blog_files)
        for name in blog_files:
            self.assertRegex(name, r"^\d{4}-\d{2}-\d{2}-")


class DocumentationConsistencyTests(unittest.TestCase):
    def test_docs_explain_three_coarse_categories_and_foundation_badge(self):
        texts = [
            TAXONOMY_PATH.read_text(encoding="utf-8"),
            CONTRIBUTING_PATH.read_text(encoding="utf-8"),
            README_HEADER_PATH.read_text(encoding="utf-8"),
            PAPER_TEMPLATE_PATH.read_text(encoding="utf-8"),
        ]
        for text in texts:
            self.assertIn("Theoretical and Mechanical Analysis", text)
            self.assertIn("Architecture and Algorithm Designs", text)
            self.assertIn("Applications Focused", text)
            self.assertIn("theoretical and mechanical analysis", text.lower())
            self.assertIn("foundation", text.lower())
            self.assertNotIn("Capability and Scaling Studies", text)
            self.assertNotIn("Inference and Optimization Methods", text)
            self.assertNotIn("For backward compatibility", text)
            self.assertNotIn("old metadata is mapped", text)

    def test_docs_explain_that_browser_tag_filters_use_mechanism_focus_and_domain_tags(self):
        taxonomy = TAXONOMY_PATH.read_text(encoding="utf-8")
        contributing = CONTRIBUTING_PATH.read_text(encoding="utf-8")
        readme_header = README_HEADER_PATH.read_text(encoding="utf-8")
        blog_template = BLOG_TEMPLATE_PATH.read_text(encoding="utf-8")

        for text in (taxonomy, contributing, readme_header, blog_template):
            self.assertIn("mechanism_tags", text)
            self.assertIn("focus_tags", text)
            self.assertIn("domain_tags", text)
            self.assertIn("browser", text.lower())
            self.assertIn("hierarchical-loop", text)
            self.assertIn("flat-loop", text)
            self.assertIn("parallel-loop", text)
            self.assertIn("implicit-layer", text)
            self.assertNotIn("family_tags", text)
            self.assertNotIn("family tags", text.lower())

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
    def test_add_arxiv_helper_does_not_emit_category_path_and_requires_loop_mechanism(self):
        text = ADD_ARXIV_YAML_PATH.read_text(encoding="utf-8")
        self.assertNotIn("--category-path", text)
        self.assertNotIn("category_path", text)
        self.assertIn("required=True", text)
        for tag in build.VALID_MECHANISM_TAGS:
            self.assertIn(tag, text)

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
    def run_submission_inventory_helpers(expression: str):
        """Evaluate the submission inventory pure helpers from submit.html in Node."""
        html = SUBMIT_PAGE_PATH.read_text(encoding="utf-8")
        helper_start = html.index("function isValidCountedInventory(inventory) {")
        helper_end = html.index("function getSortedSelected(group) {", helper_start)
        helpers = html[helper_start:helper_end]
        script = f"""
{helpers}
const result = {expression};
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
        self.assertIn("controlled tag-vocabulary", template.lower())
        self.assertNotIn("new category", template.lower())
        self.assertNotIn("new tags", template.lower())

    def test_submit_page_contains_searchable_tag_picker_yaml_preview_and_fork_first_github_guidance(self):
        html = SUBMIT_PAGE_PATH.read_text(encoding="utf-8")
        self.assertIn("Searchable tag picker", html)
        self.assertIn("fetch('submission-meta.json')", html)
        self.assertNotIn("fetch('papers.json')", html)
        self.assertNotIn("deriveFallbackSourcePath", html)
        self.assertIn("existing_paths", html)
        self.assertIn("tag_inventories", html)
        self.assertIn("isValidCountedInventory(inventories.mechanism)", html)
        self.assertIn("isValidCountedInventory(inventories.focus)", html)
        self.assertIn("isValidCountedInventory(inventories.domain)", html)
        self.assertIn(
            "STATE.options.domain = mergeSuggestedCountedInventory(inventories.domain, SUGGESTED_DOMAIN_TAGS);",
            html,
        )
        self.assertIn("submission-form", html)
        self.assertIn("resource-kind-toggle", html)
        self.assertIn("resource-title-input", html)
        self.assertIn("authors-input", html)
        self.assertIn("published-date-input", html)
        self.assertIn("shortname-input", html)
        self.assertIn("primary-link-input", html)
        self.assertIn("category-select", html)
        self.assertIn("yaml-preview-output", html)
        self.assertIn("target-path-output", html)
        self.assertIn("effective-shortname-output", html)
        self.assertIn("extracted-arxiv-id-output", html)
        self.assertIn("path-status-output", html)
        self.assertIn("github-repo-url-output", html)
        self.assertIn("copy-target-path-btn", html)
        self.assertIn("Open GitHub repo (fork first)", html)
        self.assertIn("GitHub fork / PR handoff", html)
        self.assertIn("Manual GitHub step", html)
        self.assertIn("Ready to copy into your fork", html)
        self.assertIn("Step 1", html)
        self.assertIn("Step 2", html)
        self.assertIn("Step 3", html)
        self.assertNotIn("What counts as a blog?", html)
        self.assertNotIn("substantive public long-form technical post", html)
        self.assertIn("copyTargetPath", html)
        self.assertIn("openGitHubRepoForFork", html)
        self.assertIn("buildYamlPreview", html)
        self.assertIn("slugifyFilenamePart", html)
        self.assertIn("extractArxivId", html)
        self.assertIn("targetFileExists", html)
        self.assertNotIn("data.papers", html)
        self.assertNotIn("data.blogs", html)
        self.assertIn("tag-picker-search", html)
        self.assertIn("Paper Category", html)
        self.assertIn("three flat paper categories", html)
        self.assertIn("Browser-facing loop-form tags", html)
        self.assertIn("hierarchical-loop", html)
        self.assertIn("flat-loop", html)
        self.assertIn("parallel-loop", html)
        self.assertIn("implicit-layer", html)
        self.assertIn("domain-tags-manual-input", html)
        self.assertIn("alias-tags-manual-input", html)
        self.assertNotIn("new-category-input", html)
        self.assertNotIn("Custom Category / Path", html)
        self.assertNotIn("mechanism-tags-manual-input", html)
        self.assertNotIn("focus-tags-manual-input", html)
        self.assertNotIn("category/subcategory", html)
        self.assertNotIn("category_path", html)
        self.assertNotIn("new category", html.lower())
        self.assertNotIn("new tags", html.lower())
        self.assertIn("PR message", html)
        self.assertLess(html.index("Generate YAML and prepare your fork / PR"), html.index("Searchable tag picker"))
        self.assertLess(html.index("resource-title-input"), html.index("Searchable tag picker"))
        self.assertLess(html.index("Searchable tag picker"), html.index("Generated target path"))
        self.assertNotIn('id="alias-picker"', html)
        self.assertNotIn("Open prefilled GitHub issue", html)
        self.assertNotIn("Open GitHub editor for PR", html)
        self.assertNotIn("buildGitHubNewFileUrl", html)
        self.assertNotIn("new/main?filename=", html)
        self.assertNotIn("focus-tags-output", html)
        self.assertNotIn("domain-tags-output", html)
        self.assertNotIn("alias-tags-output", html)
        self.assertNotIn("family-tags-manual-input", html)
        self.assertNotIn("Family Tags", html)
        self.assertNotIn("family_tags", html)
        self.assertNotIn("tag-snippet", html)
        self.assertNotIn("Auto-filled from the searchable picker", html)
        self.assertNotIn("Paper mode", html)
        self.assertNotIn("Taxonomy category required", html)
        self.assertNotIn("Automatic YAML generation is disabled for new paper category proposals", html)
        self.assertIn("efficient-loop", html)

    def test_submit_inventory_helpers_merge_observed_and_suggested_domain_tags(self):
        result = self.run_submission_inventory_helpers("""({
  missingSuggestion: mergeSuggestedCountedInventory(
    [{label: 'vision', count: 4}, {label: 'reasoning', count: 2}],
    ['efficient-loop', 'reasoning']
  ),
  observedSuggestion: mergeSuggestedCountedInventory(
    [{label: 'vision', count: 2}, {label: 'efficient-loop', count: 2}],
    ['efficient-loop']
  )
})""")

        self.assertEqual(
            result["missingSuggestion"],
            [
                {"label": "vision", "count": 4},
                {"label": "reasoning", "count": 2},
                {"label": "efficient-loop", "count": 0},
            ],
        )
        self.assertEqual(
            result["observedSuggestion"],
            [
                {"label": "efficient-loop", "count": 2},
                {"label": "vision", "count": 2},
            ],
        )
        self.assertEqual(
            sum(row["label"] == "efficient-loop" for row in result["observedSuggestion"]),
            1,
        )

    def test_submit_inventory_helper_rejects_malformed_rows(self):
        result = self.run_submission_inventory_helpers("""({
  valid: isValidCountedInventory([{label: 'flat-loop', count: 0}]),
  malformed: [
    isValidCountedInventory([null]),
    isValidCountedInventory([[]]),
    isValidCountedInventory([{label: '', count: 0}]),
    isValidCountedInventory([{label: '   ', count: 0}]),
    isValidCountedInventory([{label: 3, count: 0}]),
    isValidCountedInventory([{label: 'flat-loop', count: -1}]),
    isValidCountedInventory([{label: 'flat-loop', count: 1.5}]),
    isValidCountedInventory([{label: 'flat-loop', count: Infinity}]),
    isValidCountedInventory([{label: 'flat-loop', count: NaN}]),
    isValidCountedInventory([
      Object.assign(Object.create(null), {label: 'flat-loop', count: 1})
    ])
  ]
})""")

        self.assertTrue(result["valid"])
        self.assertEqual(result["malformed"], [False] * 10)

    def test_submit_page_marks_required_fields_and_gives_tag_actions_more_spacing(self):
        html = SUBMIT_PAGE_PATH.read_text(encoding="utf-8")
        self.assertIn(".panel {\n      background: var(--surface);\n      border: 1px solid var(--border);\n      border-radius: var(--radius);\n      box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);\n      padding: var(--space-5);\n      display: grid;\n      gap: var(--space-4);", html)
        self.assertIn(".field.is-required .field-label::after", html)
        self.assertIn("content: ' *';", html)
        self.assertIn(".field.is-invalid .field-label", html)
        self.assertIn(".field.is-invalid .field-input", html)
        self.assertIn(".tag-picker-actions {", html)
        self.assertIn("margin-block: var(--space-4);", html)
        self.assertIn(".preview-box {\n      border: 0;\n      border-top: 1px solid var(--border);", html)
        self.assertIn(".github-branch-callout {\n      border: 0;\n      border-left: 3px solid rgba(9, 105, 218, 0.28);", html)
        self.assertIn("syncRequiredFieldStates()", html)

    def test_submit_page_tag_search_updates_menu_without_replacing_input(self):
        html = SUBMIT_PAGE_PATH.read_text(encoding="utf-8")
        self.assertIn("function refreshPickerMenu(group) {", html)
        self.assertIn("menu.innerHTML = renderPickerMenuHtml(group);", html)
        self.assertIn("refreshPickerMenu(group);", html)
        input_handler_start = html.index("searchInput.addEventListener('input', function(event) {")
        input_handler_end = html.index("});", input_handler_start)
        input_handler = html[input_handler_start:input_handler_end]
        self.assertNotIn("renderPicker(group)", input_handler)

    def test_paper_template_mentions_must_read_but_submit_page_does_not_surface_it(self):
        template = PAPER_TEMPLATE_PATH.read_text(encoding="utf-8")
        html = SUBMIT_PAGE_PATH.read_text(encoding="utf-8")
        self.assertIn("must_read", template)
        self.assertIn("maintainer-only", template.lower())
        self.assertNotIn("must_read", html)

    def test_submit_page_uses_responsive_nested_layout_and_english_selectable_published_date_input(self):
        html = SUBMIT_PAGE_PATH.read_text(encoding="utf-8")
        self.assertIn(".grid {\n      display: grid;\n      gap: var(--space-4);\n      grid-template-columns: 1fr;", html)
        self.assertIn(".wizard-grid {\n      display: grid;\n      gap: var(--space-3);\n      grid-template-columns: repeat(3, minmax(0, 1fr));", html)
        self.assertIn(".form-grid {\n      display: grid;\n      gap: var(--space-3);\n      grid-template-columns: repeat(2, minmax(0, 1fr));", html)
        self.assertIn(".tag-pickers {\n      display: grid;\n      gap: var(--space-3);\n      grid-template-columns: repeat(3, minmax(0, 1fr));", html)
        self.assertIn("@media (max-width: 980px)", html)
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
        self.assertIn("controlled tag-vocabulary change", contributing.lower())
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
