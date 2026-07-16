# Paper Stats Tab Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an accessible `Papers | Stats` surface with daily catalog-growth and monthly publication timelines backed by complete canonical dates.

**Architecture:** Backfill missing paper intake dates from Git first-add history, then aggregate the existing `papers.json` paper records in the browser. Extend `index.html` with a top-level ARIA tab state, lazy inline-SVG rendering, deterministic KPI helpers, and responsive styles while preserving the current Papers filters and Category/Table views.

**Tech Stack:** Canonical YAML, Python build validation, static HTML/CSS, ES5-compatible browser JavaScript, inline SVG, Python `unittest` source regressions.

---

### Task 1: Require complete canonical intake dates

**Files:**
- Modify: `tests/test_build.py`
- Modify: the 39 `papers/*.yaml` files currently missing `added_date`

**Step 1: Write the failing regression test**

Add a repository-source test near the existing date validation tests:

```python
def test_all_canonical_papers_have_added_date(self):
    missing = []
    for paper_path in sorted(PAPERS_DIR.glob("*.yaml")):
        if paper_path.name.startswith("_"):
            continue
        paper = yaml.safe_load(paper_path.read_text(encoding="utf-8")) or {}
        if not paper.get("added_date"):
            missing.append(paper_path.name)
    self.assertEqual(missing, [])
```

Use the existing module-level repository path constants where available; do not introduce a second repo-root calculation.

**Step 2: Record the expected failing command**

Do not run the test suite on the shared machine without explicit approval. The CI/Slurm command is:

```bash
python3 -m unittest tests.test_build.<class-name>.test_all_canonical_papers_have_added_date
```

Expected before the backfill: failure listing 39 YAML filenames.

**Step 3: Backfill Git-confirmed dates**

Add quoted intake dates immediately after `published_date` in each missing canonical YAML:

- `added_date: "2026-04-24"` for the 37 files whose first-add Git date is 2026-04-24;
- `papers/2511.07384.yaml`: `added_date: "2026-04-26"`;
- `papers/2605.07721.yaml`: `added_date: "2026-05-11"`.

Do not change `published_date`, other metadata, generated artifacts, or any audit files.

**Step 4: Inspect the source invariant**

Use lightweight inspection:

```bash
rg -L '^added_date:' papers/*.yaml
git diff --check -- papers tests/test_build.py
```

Expected: only `_template.yaml.example` may be irrelevant to the canonical glob; all canonical paper YAML files contain `added_date`, and the diff check is clean.

**Step 5: Commit**

```bash
git add papers tests/test_build.py
git commit -m "data: complete paper intake dates"
```

### Task 2: Add the top-level Papers and Stats tab shell

**Files:**
- Modify: `tests/test_build.py`
- Modify: `index.html`

**Step 1: Write failing markup/state assertions**

Add a focused frontend regression test that requires:

```python
for snippet in (
    'role="tablist"',
    'id="papers-tab"',
    'id="stats-tab"',
    'id="papers-panel"',
    'id="stats-panel"',
    'role="tabpanel"',
    "let ACTIVE_TOP_LEVEL_TAB = 'papers';",
    "function setTopLevelTab(tab, options)",
    "function applyTopLevelTab()",
):
    self.assertIn(snippet, html)
```

Also assert that existing `Category view` and `Table view` controls remain present inside the Papers experience.

**Step 2: Record the expected failing command**

```bash
python3 -m unittest tests.test_build.<class-name>.test_papers_and_stats_tab_shell_exists
```

Expected before implementation: failure because the Stats tab markup is absent.

**Step 3: Add the semantic tab shell**

In `index.html`:

- add a compact `.content-tabs` control at the top of `<main>`;
- wrap the existing disclaimer, mobile directory, sections container, and table shell in `#papers-panel`;
- add an initially hidden `#stats-panel` after it;
- keep `#no-results` inside the Papers panel so Stats never displays paper-filter empty states;
- add `aria-controls`, `aria-selected`, and matching `aria-labelledby` relationships.

The default markup must select Papers and hide Stats.

**Step 4: Add the top-level state transition**

Implement:

```javascript
let ACTIVE_TOP_LEVEL_TAB = 'papers';

function normalizeTopLevelTab(tab) {
  return tab === 'stats' ? 'stats' : 'papers';
}

function applyTopLevelTab() {
  // Synchronize selected classes, aria-selected, tabindex, and panel.hidden.
}

function setTopLevelTab(tab, options) {
  // Normalize, apply, lazy-render Stats, and update location.hash unless disabled.
}
```

Do not modify `CURRENT_VIEW`; it continues to mean only `category | table` within Papers.

**Step 5: Add responsive theme-aware styles**

Use existing CSS variables for borders, surface, text, and accent colors. Add visible `:focus-visible` treatment and ensure the control fits without horizontal page overflow at 320 CSS pixels.

**Step 6: Perform lightweight inspection and commit**

```bash
rg -n 'content-tabs|papers-tab|stats-tab|papers-panel|stats-panel|ACTIVE_TOP_LEVEL_TAB' index.html
git diff --check -- index.html tests/test_build.py
git add index.html tests/test_build.py
git commit -m "feat: add papers and stats tabs"
```

### Task 3: Implement deterministic stats-series helpers

**Files:**
- Modify: `tests/test_build.py`
- Modify: `index.html`

**Step 1: Write failing helper-contract assertions**

Require named, side-effect-free helpers:

```python
for signature in (
    "function parseIsoDate(value)",
    "function formatIsoDateUtc(date)",
    "function buildDailyPaperSeries(papers)",
    "function buildMonthlyPublicationSeries(papers)",
    "function buildStatsSummary(dailySeries, totalPapers)",
):
    self.assertIn(signature, html)
```

Require source markers showing that daily series reads `paper.added_date` and monthly series reads `paper.published_date`. Assert that daily aggregation does not fall back to `published_date`.

**Step 2: Record the expected failing command**

```bash
python3 -m unittest tests.test_build.<class-name>.test_stats_series_helpers_use_distinct_date_semantics
```

Expected before implementation: failure because the helpers are absent.

**Step 3: Implement strict UTC date helpers**

`parseIsoDate` must accept only real `YYYY-MM-DD` dates and return `null` for malformed values. All stepping and bucketing must use UTC methods to avoid DST gaps.

**Step 4: Implement daily intake aggregation**

`buildDailyPaperSeries(papers)` must:

- count only valid `added_date` values;
- return one entry for every calendar day between minimum and maximum dates;
- use `{ key, label, count, cumulative }` records;
- preserve a deterministic empty array for no dated papers.

The final cumulative value must equal the number of valid dated papers.

**Step 5: Implement monthly publication aggregation**

`buildMonthlyPublicationSeries(papers)` must:

- bucket valid `published_date` values into UTC `YYYY-MM` keys;
- fill missing months from the earliest through latest bucket;
- return the same `{ key, label, count, cumulative }` shape.

**Step 6: Implement KPI calculation**

`buildStatsSummary` must calculate:

- `totalPapers` from the supplied paper list;
- `datedPapers` from the final daily cumulative count;
- `lastSevenDays` from the final seven daily buckets, anchored to the latest recorded intake date;
- `peakDay` with stable earliest-date tie breaking.

**Step 7: Inspect and commit**

```bash
rg -n 'buildDailyPaperSeries|buildMonthlyPublicationSeries|buildStatsSummary|added_date|published_date' index.html
git diff --check -- index.html tests/test_build.py
git add index.html tests/test_build.py
git commit -m "feat: aggregate paper timeline statistics"
```

### Task 4: Render the KPI cards and both SVG timelines lazily

**Files:**
- Modify: `tests/test_build.py`
- Modify: `index.html`

**Step 1: Write failing rendering assertions**

Require:

```python
for snippet in (
    'id="stats-kpis"',
    'id="catalog-growth-chart"',
    'id="publication-trend-chart"',
    "function renderStatsPanel()",
    "function renderTimelineChart(container, series, options)",
    "let HAS_RENDERED_STATS = false;",
    "Catalog Growth",
    "Papers in this catalog by publication month",
):
    self.assertIn(snippet, html)
```

Assert that `renderStatsPanel()` is called from the Stats tab transition only when `HAS_RENDERED_STATS` is false.

**Step 2: Record the expected failing command**

```bash
python3 -m unittest tests.test_build.<class-name>.test_stats_panel_renders_two_timelines_lazily
```

Expected before implementation: failure because chart containers/renderers are absent.

**Step 3: Add Stats panel content**

Create semantic cards for:

- total papers;
- additions in the latest seven recorded days;
- intake-date coverage;
- peak intake day.

Add two chart cards with titles, scope copy, overflow containers, SVG mount points, and normal-HTML recent-period summaries.

**Step 4: Implement a shared inline-SVG renderer**

`renderTimelineChart(container, series, options)` must:

- create an SVG with `viewBox`, `<title>`, and `<desc>`;
- use bars for period counts and a line for cumulative counts;
- render sparse, collision-resistant x-axis ticks and separate labeled count scales;
- use DOM APIs or escaped controlled values so paper metadata never becomes executable markup;
- show a local empty state when `series.length === 0`;
- avoid transitions or animation.

Use CSS custom properties/classes for color rather than hard-coded light-theme-only fills.

**Step 5: Render summaries and set the lazy flag**

`renderStatsPanel()` builds both series from `ALL_PAPERS`, updates the KPI cards and recent-period text, renders both charts, then sets `HAS_RENDERED_STATS = true`.

**Step 6: Inspect and commit**

```bash
rg -n 'stats-kpi|timeline-chart|renderStatsPanel|renderTimelineChart|HAS_RENDERED_STATS' index.html
git diff --check -- index.html tests/test_build.py
git add index.html tests/test_build.py
git commit -m "feat: render paper statistics timelines"
```

### Task 5: Add URL restoration and keyboard navigation

**Files:**
- Modify: `tests/test_build.py`
- Modify: `index.html`

**Step 1: Write failing interaction assertions**

Require named handlers and wiring:

```python
for snippet in (
    "function getTopLevelTabFromHash()",
    "function handleTopLevelTabKeydown(event)",
    'window.addEventListener("hashchange"',
    'addEventListener("keydown", handleTopLevelTabKeydown)',
):
    self.assertIn(snippet, html)
```

Also require both `#papers` and `#stats` hash constants/branches and left/right arrow handling.

**Step 2: Record the expected failing command**

```bash
python3 -m unittest tests.test_build.<class-name>.test_stats_tabs_restore_hash_and_support_keyboard_navigation
```

Expected before implementation: failure because hash/keyboard handlers are absent.

**Step 3: Implement hash restoration**

- Treat `#stats` as Stats and all other/empty hashes as Papers.
- Apply the initial hash only after `papers.json` has populated `ALL_PAPERS`, so direct Stats URLs can render immediately.
- React to browser back/forward through `hashchange` without adding duplicate history entries.

**Step 4: Implement keyboard behavior**

- Left/Right arrows move to the adjacent tab, wrapping across two tabs.
- Home/End select the first/last tab.
- Selection moves focus to the activated tab.
- Pointer activation remains standard button behavior.

**Step 5: Inspect and commit**

```bash
rg -n 'getTopLevelTabFromHash|handleTopLevelTabKeydown|hashchange|ArrowLeft|ArrowRight|Home|End' index.html
git diff --check -- index.html tests/test_build.py
git add index.html tests/test_build.py
git commit -m "feat: restore and navigate stats tabs"
```

### Task 6: Review generated-data impact and verify the feature

**Files:**
- Modify only if review finds a defect: `index.html`, `tests/test_build.py`, `papers/*.yaml`
- Generated by CI/approved build: `papers.json`, `README.md`, `TAGS.md`, `submission-meta.json`

**Step 1: Perform source-only verification allowed on the shared machine**

```bash
git diff --check
rg -L '^added_date:' papers/*.yaml
git status --short
```

Inspect the diff for unrelated generated artifacts or user files. Do not stage `figures/` or `loop_transformers_baseline_backbone_report.md`.

**Step 2: Perform focused review passes**

Review separately for:

- correctness of UTC day/month filling and cumulative totals;
- accessibility and semantic tab behavior;
- responsive layout, dark theme, and visual clarity;
- preservation of existing search/filter and Category/Table behavior;
- simplicity and zero-dependency constraints.

Fix confirmed issues with focused commits.

**Step 3: Run browser verification only with approval**

Serve through HTTP because `file://` cannot fetch `papers.json`:

```bash
python3 -m http.server 8000
```

Check desktop and mobile widths, both color schemes where available, direct `#stats` loading, back/forward navigation, arrow-key tabs, both charts, and Papers search/filter/table regressions.

**Step 4: Run canonical build/tests through CI or approved Slurm execution**

```bash
python3 scripts/build.py
python3 -m unittest discover -s tests -t . -p 'test_*.py'
git diff --check
```

Expected: build succeeds, full suite reports `OK`, all paper records in regenerated `papers.json` include `added_date`, and generated cumulative totals equal `.meta.paper_total`.

**Step 5: Commit any generated artifacts produced by the approved canonical build**

```bash
git add README.md TAGS.md papers.json submission-meta.json
git commit -m "chore: regenerate catalog artifacts"
```

Skip this commit when CI owns generated-artifact refresh.
