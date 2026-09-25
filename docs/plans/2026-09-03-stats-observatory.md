# Stats Observatory Visual Refresh Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the existing Release trend into a focused dark research-observatory visualization while preserving the site's editorial shell and Stats behavior.

**Architecture:** Reuse the final Stats CSS override and native SVG renderer in `index.html`. Add one normalized SVG `pathLength` attribute for reliable line-draw motion, keep all aggregation and interaction code unchanged, and update the existing focused source contract to require the observatory treatment and reduced-motion fallback.

**Tech Stack:** Static HTML, CSS custom properties and keyframes, vanilla JavaScript, native SVG, Python `unittest` source contracts.

---

### Task 1: Specify the observatory contract

**Files:**
- Modify: `tests/test_build.py:2903-2932`

**Step 1: Replace the obsolete no-animation assertion**

Extend the compact dashboard contract to require:

```python
self.assertIn("--stats-observatory-bg:", stats_css)
self.assertIn("animation: stats-bar-rise", stats_css)
self.assertIn("animation: stats-line-draw", stats_css)
self.assertIn("@media (prefers-reduced-motion: reduce)", stats_css)
self.assertIn("animation: none;", stats_css)
```

Also require `'pathLength': 1` in the release renderer source so the line animation is independent of chart width.

**Step 2: Record the expected failing check**

Do not run the test suite locally without explicit permission. The narrow command for the user or Slurm runner is:

```bash
python3 -m unittest tests.test_build.TagFilterUiTests.test_stats_dashboard_uses_twelve_column_information_grid
```

Expected before implementation: FAIL because the observatory variables, animations, and normalized line length do not exist.

### Task 2: Implement the single dark data window

**Files:**
- Modify: `index.html:4411-4640`
- Modify: `index.html:5034-5051`
- Modify: `index.html:5928-5934`

**Step 1: Add local observatory tokens**

Add dark ink, border, text, muted, bar, trend, and grid variables to `.stats-panel` so the treatment remains isolated from Papers and other Stats cards.

**Step 2: Separate the primary chart from generic cards**

Keep `.stats-dashboard-card` transparent and editorial. Give `.stats-primary-chart` the deep ink background, restrained radial light, technical grid, thin border, low radius, and one controlled shadow.

**Step 3: Restyle chart-local typography and controls**

Use light chart text, blue section labels, muted supporting copy, a translucent segmented control, and the existing blue/sage data encoding. Do not change markup or interaction state.

**Step 4: Add meaningful one-shot motion**

Animate bars from the baseline and draw the average line once whenever the native SVG is rebuilt. Add `pathLength="1"` to the polyline and disable both animations under `prefers-reduced-motion: reduce`.

**Step 5: Preserve responsive and dark behavior**

Keep the current grid breakpoints, mobile stacking, 44px controls, and document scrolling. Ensure the final dark-mode override does not reset the observatory window to transparent.

### Task 3: Verify the focused diff

**Files:**
- Verify: `index.html`
- Verify: `tests/test_build.py`

**Step 1: Run lightweight source assertions**

Use `rg`/`sed` to confirm the observatory variables, data colors, `pathLength`, animation names, and reduced-motion override are present in the final cascade.

**Step 2: Check patch integrity**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors; only the design/plan documents, `index.html`, and the focused test file are changed.

**Step 3: Leave opt-in verification commands**

Do not execute these locally without explicit permission:

```bash
python3 -m unittest tests.test_build.TagFilterUiTests.test_stats_dashboard_uses_twelve_column_information_grid
python3 -m http.server 8123 --bind 127.0.0.1
```

Browser target: `http://127.0.0.1:8123/index.html#stats`, checked at desktop and 390px mobile widths with light, dark, and reduced-motion preferences.
