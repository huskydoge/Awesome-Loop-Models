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
FAVICON_PATH = REPO_ROOT / "assets" / "favicon.png"


class BuildTaxonomyTests(unittest.TestCase):
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


class TagFilterUiTests(unittest.TestCase):
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
        self.assertIn("body.filter-sidebar-open h1", html)
        self.assertIn("body.filter-sidebar-open .filter-sidebar-toggle-row", html)
        self.assertIn("body.filter-sidebar-open header {\n        padding: 12px;", html)
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
        self.assertIn("let ALL_RESOURCES = [];", html)
        self.assertIn("function createBlogSection()", html)
        self.assertIn("function createBlogTreeNode()", html)
        self.assertIn("BLOG_SECTION_META", html)
        self.assertIn("section-blogs", html)
        self.assertIn("blogs-grid", html)

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

    def test_old_submission_issue_templates_are_removed(self):
        self.assertFalse((REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "add_paper.yml").exists())
        self.assertFalse((REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "add_blog.yml").exists())
        self.assertTrue(FIX_ERROR_TEMPLATE_PATH.exists())

    def test_repo_meta_file_and_generated_js_exist(self):
        meta = self.load_repo_meta()
        js = REPO_META_JS_PATH.read_text(encoding="utf-8")
        self.assertEqual(meta["github_owner"], "huskydoge")
        self.assertEqual(meta["default_repo_name"], "Awesome-Loop-Models-Private")
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
        self.assertIn("fetch('papers.json')", html)
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
        self.assertIn("source_path", html)
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
