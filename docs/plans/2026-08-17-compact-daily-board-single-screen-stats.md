# Compact Daily Board and Single-Screen Stats Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the overlapping briefing card with a truthful two-signal daily strip and fit the core Stats charts into a desktop viewport without nested scrollbars.

**Architecture:** Keep the static single-page application and current `papers.json` schema. Reuse `ALL_PAPERS`, `REPO_TODAY`, `must_read`, the existing release aggregation, distribution renderers, and URL-backed tag links; delete obsolete briefing-detail and secondary Stats-feed UI instead of adding state or dependencies.

**Tech Stack:** Static HTML, CSS, and JavaScript in `index.html`; existing Python `unittest` source/runtime contracts in `tests/test_build.py`.

---

### Task 1: Replace the daily briefing overlay with an in-flow status strip

**Files:**
- Modify: `index.html` near the daily briefing CSS, toolbar markup, state variables, and `updateDailyBriefingNotice`
- Modify: `tests/test_build.py` in the daily briefing frontend contracts

**Step 1: Update the focused contract**

Replace the old assertions for title lists, Details, detail scrollbars, and absolute `left: 32px` positioning with assertions requiring:

```python
self.assertIn('class="daily-briefing-notice"', html)
self.assertIn('id="daily-briefing-today-count"', html)
self.assertIn('id="daily-briefing-recommended"', html)
self.assertIn("paper._addedDate === today", html)
self.assertIn("paper.must_read === true", html)
self.assertIn("position: static;", daily_notice_css)
self.assertNotIn('daily-briefing-notice-toggle', html)
self.assertNotIn('daily-briefing-notice-detail', html)
```

Do not run the unit test locally without explicit approval. Prepared focused command:

```bash
/opt/homebrew/bin/python3.13 -m unittest \
  tests.test_build.FrontendTests.test_daily_briefing_notice_exists_in_frontend \
  tests.test_build.FrontendTests.test_papers_side_widgets_reflow_before_they_can_overlap_masthead_tools
```

Expected before implementation: FAIL because the old briefing card is still absolute and exposes the removed detail UI.

**Step 2: Replace the markup and renderer**

Keep the existing aside identity but reduce its contents to:

```html
<aside class="daily-briefing-notice" id="daily-briefing-notice" aria-label="Today's catalog update" hidden>
  <span class="daily-briefing-notice-label">Today</span>
  <strong id="daily-briefing-today-count">— papers</strong>
  <span class="daily-briefing-notice-separator" aria-hidden="true">·</span>
  <span id="daily-briefing-recommended">Husky recommended: —</span>
</aside>
```

Replace the briefing-driven renderer with one data pass:

```js
function updateDailyBriefingNotice() {
  const notice = document.getElementById('daily-briefing-notice');
  if (!notice) return;
  const today = getRepoTodayString();
  const todayPapers = ALL_PAPERS.filter(function(paper) {
    return paper._addedDate === today;
  });
  const recommendedCount = todayPapers.filter(function(paper) {
    return paper.must_read === true;
  }).length;
  document.getElementById('daily-briefing-today-count').textContent =
    todayPapers.length + ' paper' + (todayPapers.length === 1 ? '' : 's');
  document.getElementById('daily-briefing-recommended').textContent =
    'Husky recommended: ' + (recommendedCount ? recommendedCount : 'No');
  notice.hidden = false;
}
```

Delete the obsolete briefing candidate/title/toggle functions and the now-unused `ALL_BRIEFINGS`/briefing display state only where no other caller remains.

**Step 3: Make the strip part of layout flow**

Give the notice a compact, single-line `position: static` treatment inside `.papers-only-tools`. Preserve wrapping at narrow widths and the existing visual language. Remove detail scrollbar selectors and obsolete expanded-state rules.

**Step 4: Static verification and commit**

```bash
rg -n "daily-briefing-(today-count|recommended)|updateDailyBriefingNotice|daily-briefing-notice-(toggle|detail|new-papers)" index.html tests/test_build.py
git diff --check
git status --short
git add index.html tests/test_build.py
git commit -m "fix: collapse daily catalog board"
```

### Task 2: Convert Stats to a two-row desktop dashboard

**Files:**
- Modify: `index.html` in Stats markup, final editorial CSS overrides, `renderReleasePulseChart`, and `renderStatsPanel`
- Modify: `tests/test_build.py` in Stats dashboard contracts

**Step 1: Update the focused contracts**

Require a desktop two-row grid, no nested scroll roots, no tag explorer/latest feed, and no 760px SVG floor:

```python
self.assertIn("body.stats-mode main {", stats_css)
self.assertIn("overflow: hidden;", desktop_stats_rule)
self.assertNotIn("scrollbar-gutter:", stats_css)
self.assertNotIn("body.stats-mode main::-webkit-scrollbar", stats_css)
self.assertNotIn('class="stats-tag-explorer"', html)
self.assertNotIn('class="stats-dashboard-card stats-latest-card"', html)
self.assertIn("grid-template-columns: repeat(12, minmax(0, 1fr));", stats_css)
self.assertIn("grid-template-rows: minmax(0, 1fr) minmax(0, .72fr);", stats_css)
self.assertIn("var chartWidth = Math.max(480,", html)
self.assertNotIn("container.scrollLeft =", html)
```

Require a normal document-scroll fallback at the responsive breakpoint:

```python
self.assertIn("body.stats-mode main {\n        overflow-y: auto;", mobile_css)
self.assertIn(".stats-dashboard-grid {\n        display: block;", mobile_css)
```

Do not run tests locally without explicit approval. Prepared focused command:

```bash
/opt/homebrew/bin/python3.13 -m unittest \
  tests.test_build.StatsTabTests.test_stats_dashboard_uses_twelve_column_information_grid \
  tests.test_build.StatsTabTests.test_stats_mobile_stacks_landscape_without_order_hacks \
  tests.test_build.StatsTabTests.test_stats_scrollbar_is_subtle_and_does_not_cover_content
```

Expected before implementation: FAIL because the current contract preserves nested scrolling and the removed modules.

**Step 2: Remove secondary non-dashboard content**

Delete the full tag explorer and latest-publications article from the Stats markup. Remove their renderer calls from `renderStatsPanel`; retain any shared helpers still used by Papers or other tests.

**Step 3: Fit the desktop dashboard**

At desktop widths:

- make `.stats-panel` a viewport-filling grid with compact header, KPI rail, and two analytical rows;
- reduce header, KPI, card-header, and inter-card spacing;
- use 7/5 columns for Release trend and Category mix;
- use 5/7 columns for Loop mechanisms and Active directions;
- render active-direction Top 6 as a compact two-column list where space permits;
- set `body.stats-mode main { overflow: hidden; }` and remove every custom Stats scrollbar/gutter rule.

Keep existing tag anchors and `aria-*` semantics in category/mechanism/direction renderers.

**Step 4: Remove release-chart horizontal scrolling**

Use a compact responsive SVG viewport:

```js
var chartWidth = Math.max(480, Math.round(container.clientWidth || 760));
var chartHeight = 250;
```

Remove the `container.scrollLeft` assignment and CSS `overflow-x:auto`; use `overflow:hidden` and `min-width:0`. Keep SVG title/description, shared y-scale, range buttons, and tick selection.

**Step 5: Preserve responsive readability**

At `max-width: 1179px` or `max-height: 760px`, allow `body.stats-mode main` to scroll normally and let the analytical cards wrap/stack. At `max-width: 768px`, use one column, 44px controls, and no horizontal chart scrolling.

**Step 6: Static verification and commit**

```bash
rg -n "stats-tag-explorer|stats-latest-card|scrollbar-gutter|body\.stats-mode main::-webkit-scrollbar|container\.scrollLeft|Math\.max\(760|stats-landscape-(primary|secondary)" index.html tests/test_build.py
git diff --check
git status --short
git add index.html tests/test_build.py
git commit -m "feat: fit stats dashboard to desktop viewport"
```

### Task 3: Review and browser verification handoff

**Files:**
- Review: `index.html`
- Review: `tests/test_build.py`

**Step 1: Review the complete diff**

Confirm the implementation preserves tab/hash behavior, loading/error/empty states, accessible SVG labels, clickable taxonomy links, and unrelated Papers behavior. Confirm only intended files plus the two plan documents are tracked in the worktree.

**Step 2: Run safe checks**

```bash
git diff --check origin/main...HEAD
git status --short --branch
rg -n "daily-briefing-(today-count|recommended)|body\.stats-mode main|stats-dashboard-grid|renderReleasePulseChart" index.html tests/test_build.py
```

**Step 3: Request approval for prohibited verification**

Ask before running either command:

```bash
/opt/homebrew/bin/python3.13 -m unittest discover -s tests -t . -p 'test_*.py'
/opt/homebrew/bin/python3.13 -m http.server 8767 --bind 127.0.0.1
```

With approval, check Papers and Stats at 1440×900, 1024×768, 768px, and 390px; verify no desktop inner scrollbar, no chart horizontal scroll, no board/TOC overlap, no console errors, and readable mobile stacking.
