# Research Landscape Stats Redesign Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current Stats view with a responsive Scientific Atlas for publication activity, category composition, structural relationships, and active research directions.

**Architecture:** Keep the static `index.html` application, existing `papers.json`, and URL-backed Papers drill-down. Reuse the current date, release-summary, taxonomy-distribution, lazy-render, and safe DOM/SVG helpers; replace only the Stats view layer and add two small pure aggregations.

**Tech Stack:** Static HTML, scoped CSS, browser JavaScript, inline SVG/CSS gradients, existing Python `unittest` contracts; no new dependency.

---

### Task 1: Lock the new aggregation contracts

**Files:**
- Modify: `tests/test_build.py`
- Modify: `index.html`

**Step 1: Add focused contracts**

Add Node-backed assertions for:

```javascript
buildCategoryMechanismMatrix(papers)
buildRecentTagDirections(papers, 'focus_tags', 90, 6)
```

The matrix must preserve the canonical category order, count one paper once per mechanism, expose exact cell counts, and compute a deterministic maximum. Recent directions must anchor to the latest valid publication date, deduplicate repeated tags within one paper, sort by count then label, and return at most six rows.

**Step 2: Record the blocked test command**

Do not execute under the current cluster policy. Leave this exact command for an approved run:

```bash
/opt/homebrew/bin/python3.13 -m unittest \
  tests.test_build.BuildTest.test_stats_category_mechanism_matrix_runtime \
  tests.test_build.BuildTest.test_stats_recent_directions_runtime
```

**Step 3: Implement the smallest pure helpers**

Reuse `parseIsoDate()`, category metadata, and `buildStatsDistribution()`. Do not create a generic analytics framework or cache layer.

**Step 4: Static check and commit**

```bash
git diff --check -- index.html tests/test_build.py
git add index.html tests/test_build.py
git commit -m "feat: model research landscape statistics"
```

### Task 2: Replace the Stats information architecture

**Files:**
- Modify: `index.html`
- Modify: `tests/test_build.py`

**Step 1: Replace old markup contracts**

Require:

```text
stats-atlas-header
stats-indicator-strip
publication-trend-chart
stats-category-donut
stats-category-legend
stats-structure-matrix
stats-active-directions
stats-direction-tabs
stats-tag-explorer
stats-tag-search
stats-tag-results
```

Assert that `annual-release-volume`, `latest-releases-list`, the old narrow taxonomy details, and the old dark primary-chart class are absent.

**Step 2: Replace the Stats DOM**

Build the compact header, indicator strip, 8/4 primary row, 7/5 secondary row, and independent full-width tag explorer. Preserve `#stats-panel`, `#stats-status`, lazy loading, and existing KPI IDs where reuse avoids churn.

**Step 3: Remove obsolete render paths**

Delete Annual Volume and Latest Releases markup and render calls. Delete their view-only renderers when they have no remaining callers.

**Step 4: Static check and commit**

```bash
rg -n "stats-atlas-header|stats-structure-matrix|stats-tag-explorer" index.html
rg -n "annual-release-volume|latest-releases-list|stats-primary-chart" index.html
git diff --check -- index.html tests/test_build.py
git add index.html tests/test_build.py
git commit -m "feat: restructure stats as a research atlas"
```

### Task 3: Build the Scientific Atlas visual system

**Files:**
- Modify: `index.html`
- Modify: `tests/test_build.py`

**Step 1: Replace the Stats CSS block**

Use one Stats-scoped token set for canvas, panel, rule, ink, muted text, cobalt, teal, amber, and matrix cells. Add:

- fixed-height analytical panels with `align-items: start`;
- 12-column 8/4 and 7/5 rows;
- a responsive 2×2 indicator strip;
- a viewport-fitting chart;
- donut/legend, matrix, ranked directions, and independent explorer styling;
- tablet/mobile stacking and dark-mode token overrides.

**Step 2: Remove dead selectors**

Do not append overrides below the old dashboard. Delete old hero-card, annual, latest-release, and narrow taxonomy selectors.

**Step 3: Preserve accessibility**

Keep 44px controls, `:focus-visible`, readable text, tabular numerals, non-color exact values, `prefers-reduced-motion`, and no hover-only data.

**Step 4: Static check and commit**

```bash
rg -n "stats-atlas|stats-matrix|stats-direction|stats-tag-explorer" index.html
git diff --check -- index.html tests/test_build.py
git add index.html tests/test_build.py
git commit -m "feat: style scientific atlas dashboard"
```

### Task 4: Render the trend, donut, and structural matrix

**Files:**
- Modify: `index.html`
- Modify: `tests/test_build.py`

**Step 1: Update range behavior**

Use `6m`, `24m`, and `all`. Monthly buckets power 6M/24M; annual buckets power All. Default to 24M. Keep one range listener binding and the existing visible summary.

**Step 2: Adapt the existing SVG renderer**

Keep safe SVG helpers and accessible title/description. Fit the SVG to its container rather than forcing a 760px minimum. Use bars and one restrained trend line only when the view model provides a meaningful average.

**Step 3: Add the category donut**

Use a CSS `conic-gradient` plus an external semantic list. Put total papers in the center. Link each legend row to `#section-<category>`.

**Step 4: Render the matrix**

Render visible row/column headers and exact counts. Use cell opacity against the matrix maximum. Build each nonzero cell link with the existing tag URL and category section hash; render zero cells as plain text.

**Step 5: Static check and commit**

```bash
git diff --check -- index.html tests/test_build.py
git add index.html tests/test_build.py
git commit -m "feat: visualize catalog structure"
```

### Task 5: Render Top 6 directions and the tag explorer

**Files:**
- Modify: `index.html`
- Modify: `tests/test_build.py`

**Step 1: Add the Focus/Domain direction control**

Use native buttons with `aria-pressed`, one state variable, and one shared renderer. Show exactly the six recent rows returned by the pure helper and link them through the existing tag route.

**Step 2: Add the independent explorer**

Use native `details`, Focus/Domain buttons, a search input, and a responsive link grid. Search filters labels from the full `ALL_PAPERS` distributions. Show a compact empty state for no matches.

**Step 3: Keep interaction state local**

Do not add URL state for atlas tabs or tag search. Only the destination paper filters belong in the URL.

**Step 4: Static check and commit**

```bash
git diff --check -- index.html tests/test_build.py
git add index.html tests/test_build.py
git commit -m "feat: add active direction explorer"
```

### Task 6: Browser verification and review

**Files:**
- Modify only for verified defects: `index.html`, `tests/test_build.py`

**Step 1: Serve the isolated worktree**

```bash
/opt/homebrew/bin/python3.13 -m http.server 8766 --bind 127.0.0.1
```

**Step 2: Verify desktop behavior**

Check direct `#stats`, 6M/24M/All, donut links, nonzero matrix links, Focus/Domain Top 6, explorer search, tag drill-down, loading/error behavior, and console errors.

**Step 3: Verify responsive behavior**

Check 390×844 and a tablet breakpoint. Confirm no page-level horizontal overflow, no stretched cards, readable labels, and correct 2×2 indicator layout.

**Step 4: Request read-only review**

Ask one reviewer for spec/UX compliance and one for code quality/accessibility. Fix only concrete findings.

**Step 5: Leave exact tests for the user**

Under the current policy, do not run them locally. Report:

```bash
/opt/homebrew/bin/python3.13 -m unittest discover -s tests -t . -p 'test_*.py'
```

**Step 6: Final static check and commit**

```bash
git status --short
git diff --check origin/main..HEAD
git log --oneline origin/main..HEAD
```
