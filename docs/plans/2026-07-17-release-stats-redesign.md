# Release Stats Redesign Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace catalog-intake telemetry with a full-width, globally navigable release-intelligence experience based exclusively on paper publication dates.

**Architecture:** Keep the zero-framework static site and existing `papers.json` payload. Refactor the current Stats helpers into published-date series and range-aware derived metrics, promote the mode switch into the site masthead, and rebuild the Stats panel as a full-width editorial analytics canvas with native SVG and HTML views.

**Tech Stack:** Static HTML/CSS, browser JavaScript, inline SVG, canonical YAML-generated JSON, Python `unittest` source and Node behavior fixtures.

---

### Task 1: Replace intake statistics with publication-release helpers

**Files:**
- Modify: `index.html`
- Modify: `tests/test_build.py`

**Step 1: Write failing behavior regressions**

Add or update Node-backed tests that execute production helpers and verify:

- Stats helpers read `published_date` only and contain no `added_date` fallback;
- the latest valid publication date anchors rolling windows;
- `90D` and `1Y` preserve daily zero buckets;
- `ALL` preserves monthly zero buckets;
- 14-day, 30-day, and 6-month trailing averages use the correct denominator at the beginning of a series;
- KPIs return total papers, latest-30-day releases, latest release date, and earliest peak month on ties;
- annual volumes are sorted chronologically;
- newest papers sort by publication date, then stable title/id order.

Do not run the tests locally under the shared-machine policy.

**Step 2: Implement pure release helpers**

Replace the current intake-specific paths with documented functions such as:

```javascript
function buildDailyPublicationSeries(papers) {}
function buildMonthlyPublicationSeries(papers) {}
function slicePublicationRange(dailySeries, range) {}
function addTrailingAverage(series, windowSize) {}
function buildReleaseStatsSummary(papers, dailySeries, monthlySeries) {}
function buildAnnualReleaseSeries(papers) {}
function getLatestReleasedPapers(papers, limit) {}
```

Use strict UTC date handling. No Stats helper or copy may depend on `added_date`.

**Step 3: Keep range behavior deterministic**

- `90d`: final 90 daily buckets, 14-day average;
- `1y`: final 365 daily buckets, 30-day average;
- `all`: full monthly series, 6-month average.

The latest bucket in the source data is the window anchor.

**Step 4: Perform lightweight checks and commit**

```bash
rg -n "buildDailyPublicationSeries|buildReleaseStatsSummary|added_date" index.html tests/test_build.py
git diff --check -- index.html tests/test_build.py
git add index.html tests/test_build.py
git commit -m "refactor: derive stats from paper release dates"
```

### Task 2: Promote Papers and Stats into the global masthead

**Files:**
- Modify: `index.html`
- Modify: `tests/test_build.py`

**Step 1: Write failing shell regressions**

Tests must require:

- brand, global tablist, and GitHub/Submit actions in one masthead row;
- a dedicated Papers-only tools container around daily report, countdown, search, and filters;
- Stats mode body/layout classes;
- Stats mode hiding Papers tools and sidebar;
- full-width Stats main layout;
- existing `#papers`/`#stats`, keyboard, history, and category-navigation helpers remaining wired.

**Step 2: Restructure the masthead**

Move the existing mode tabs from `<main>` into the shared site masthead. Keep one brand and one action set. Wrap Papers-only header controls in an explicitly named container that can be hidden without affecting the masthead.

**Step 3: Synchronize global-mode classes**

`applyTopLevelTab()` must toggle a Stats mode class on `<body>` and/or `.layout`. CSS uses that class to:

- compact the header;
- hide Papers tools and taxonomy sidebar;
- remove catalog layout columns;
- expand Stats to the page's full content width;
- restore every Papers element when switching back.

Do not duplicate state or introduce a second navigation system.

**Step 4: Refine responsive behavior and commit**

Ensure the brand, tabs, and actions wrap deliberately on mobile. Use the current theme variables and visible focus styles.

```bash
git diff --check -- index.html tests/test_build.py
git add index.html tests/test_build.py
git commit -m "feat: promote stats to a global site mode"
```

### Task 3: Build the full release-intelligence canvas

**Files:**
- Modify: `index.html`
- Modify: `tests/test_build.py`

**Step 1: Write failing rendering and accessibility regressions**

Require semantic landmarks and rendering functions for:

- release-intelligence hero and four metric cells;
- range control with `90D`, `1Y`, and `ALL` native buttons and `aria-pressed`;
- Release Pulse chart;
- annual release-volume view;
- latest-release links;
- long-arc cumulative view;
- loading, error, and empty states;
- SVG title/description and non-hover text summaries.

Tests should scope CSS assertions to Stats selectors and execute range behavior through the Node fixture.

**Step 2: Replace current Stats markup**

Remove Catalog Growth, intake coverage, peak intake day, and intake summaries. Add:

- editorial hero copy;
- integrated metric rail;
- one generous primary chart card;
- a lower two-column annual-volume/latest-release section;
- a restrained cumulative release history.

**Step 3: Render range-aware Release Pulse**

Reuse a shared SVG path where sensible, but render bars plus `average` rather than catalog cumulative values. The range control changes only Stats state and re-renders the primary chart without rewriting the top-level hash.

**Step 4: Render annual volume, latest releases, and long arc**

- annual bars should include values and remain readable without color;
- latest rows show date, title, venue, and best available link;
- cumulative history uses monthly publication data and remains visually secondary.

All paper-derived strings must use text-safe DOM APIs or existing escaping helpers.

**Step 5: Apply the research-observatory visual system**

Use the existing STIX display face, tabular numerals, strong rules, blue data ink, restrained trend accent, and generous spacing. Avoid gradients, glass cards, decorative animation, and unrelated color.

**Step 6: Commit**

```bash
git diff --check -- index.html tests/test_build.py
git add index.html tests/test_build.py
git commit -m "feat: build release intelligence dashboard"
```

### Task 4: Remove obsolete intake contracts and review the combined state machine

**Files:**
- Modify: `index.html`
- Modify: `tests/test_build.py`

**Step 1: Remove obsolete Stats-only intake code**

Delete unused intake-series helpers, copy, CSS selectors, DOM ids, fixtures, and source assertions. Keep canonical `added_date` validation and YAML data because other repository workflows still use it.

**Step 2: Review combined transitions**

Verify by inspection and behavior fixtures:

- direct `#stats` loading and fetch error;
- Papers ↔ Stats clicks and keyboard transitions;
- Stats range changes;
- browser history;
- category sidebar return to Papers;
- repeated mode switches do not duplicate listeners or SVG nodes.

**Step 3: Run focused independent reviews**

Request separate specification and code-quality reviews. Fix every Critical/Important issue and re-review.

**Step 4: Commit cleanup**

```bash
git diff --check -- index.html tests/test_build.py
git add index.html tests/test_build.py
git commit -m "refactor: remove obsolete intake stats UI"
```

### Task 5: Browser visual verification and handoff

**Files:**
- Modify only for confirmed defects: `index.html`, `tests/test_build.py`

**Step 1: Reload the existing local preview**

Use the already-running `http://127.0.0.1:8000/#stats` server. Verify a desktop viewport first, then representative tablet/mobile widths.

**Step 2: Inspect the visual hierarchy**

Confirm:

- global tabs are visible before any Papers-only controls;
- Stats has no search, filters, daily report, countdown, or sidebar;
- Stats content uses the full width;
- Release Pulse is the dominant visual;
- range controls visibly update selected state and chart content;
- Annual volume and Latest releases are useful and legible;
- dark theme has sufficient contrast.

**Step 3: Inspect behavior and console**

Check Papers restoration, direct hashes, keyboard tabs, category navigation, range buttons, latest links, and browser console errors.

**Step 4: Source verification**

```bash
git status --short
git diff --check
rg -n "added_date" index.html
```

The `added_date` search may find Papers-specific behavior, but it must find no Stats aggregation, KPI, chart, or copy usage.

**Step 5: Provide the unrun canonical test command**

Under the shared-machine policy, do not run the full suite without new explicit approval. Report:

```bash
python3.12 -m unittest discover -s tests -t . -p 'test_*.py'
```
