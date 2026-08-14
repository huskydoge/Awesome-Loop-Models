# Compact Tag Filter Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Keep paper content above the fold when a Stats tag route opens Filters, while still making the active tag immediately visible.

**Architecture:** Reuse the existing outer `FILTER_SIDEBAR_OPEN` and inner `TAG_FILTER_OPEN` disclosure states. A route opens the outer Filters panel, keeps the full taxonomy collapsed, and derives a compact active-tag summary from `ACTIVE_TAG_FILTERS` plus `TAG_FILTER_LOOKUP`; no new state, component, or dependency is needed.

**Tech Stack:** Vanilla HTML/CSS/JavaScript in `index.html`, Python `unittest` source/runtime contracts in `tests/test_build.py`, and the existing in-app browser preview at port 8766.

---

### Task 1: Collapse taxonomy while exposing the active route tag

**Files:**
- Modify: `tests/test_build.py` in `TagFilterUiTests`
- Modify: `index.html` near `restoreTagDrilldownFromUrl`, `formatActiveTagSummary`, `updateTagFilterUI`, and tag-filter summary styles

**Step 1: Write the failing contract**

Update the focused drill-down tests to require the outer panel open and inner taxonomy closed:

```python
self.assertIn("setFilterSidebarOpen(true);", restore_source)
self.assertIn("setTagFilterOpen(false);", restore_source)
self.assertNotIn("setTagFilterOpen(true);", restore_source)
```

The runtime navigation expectation becomes:

```python
"panels": [True, False],
"tagOpenCalls": [False],
```

Add source contracts showing `formatActiveTagSummary()` reads `TAG_FILTER_LOOKUP` and the summary receives an active visual class.

**Step 2: Verify RED**

Under the repository execution policy, do not run the test locally without explicit approval. The exact focused command for the user or CI is:

```bash
/opt/homebrew/bin/python3.13 -m unittest \
  tests.test_build.TagFilterUiTests.test_tag_drilldown_opens_filters_without_a_search_prefix \
  tests.test_build.TagFilterUiTests.test_tag_navigation_expands_active_filter_without_search_prefix
```

Expected before implementation: FAIL because route restoration still calls `setTagFilterOpen(true)` and the summary only renders `1 active`.

**Step 3: Implement the minimum production change**

Restore a route with the existing outer panel open and inner panel closed:

```js
if (LOCKED_TAG_FILTER_KEY) {
  setFilterSidebarOpen(true);
  setTagFilterOpen(false);
} else {
  updateTagFilterUI();
}
```

Reuse `formatActiveTagSummary()` for the compact pill. For one active tag, resolve its existing display label and count; for multiple active tags, keep the existing count summary:

```js
function formatActiveTagSummary() {
  if (ACTIVE_TAG_FILTERS.size === 0) return TAG_FILTER_OPEN ? '0 active' : 'hidden';
  if (ACTIVE_TAG_FILTERS.size > 1) return ACTIVE_TAG_FILTERS.size + ' active';
  const tagKey = Array.from(ACTIVE_TAG_FILTERS)[0];
  const entry = TAG_FILTER_LOOKUP[tagKey];
  if (!entry) return '1 active';
  const count = tagKey === LOCKED_TAG_FILTER_KEY ? getPaperCountForTagKey(tagKey) : entry.count;
  return (entry.displayLabel || entry.label) + ' · ' + count;
}
```

In `updateTagFilterUI()`, toggle one active class on `#tag-filter-summary`. Style that existing span as a compact pill with truncation; do not add another button or state variable.

**Step 4: Verify interaction in the existing preview**

At `http://127.0.0.1:8766/#stats`:

1. Select a mechanism, focus, or domain tag.
2. Confirm Papers opens with outer Filters visible, taxonomy collapsed, and a label/count pill beside `Tags filter`.
3. Confirm paper content begins directly below the compact controls.
4. Select `Tags filter`, confirm the full taxonomy expands and the corresponding chip remains active.
5. Select the active chip again, confirm the URL tag and summary clear while free text remains.
6. Repeat at a 390px viewport, then reset the viewport override.

**Step 5: Verify static quality and commit after approval**

Run the safe checks:

```bash
rg -n "setTagFilterOpen\\((true|false)\\)|formatActiveTagSummary|tag-filter-summary" index.html tests/test_build.py
git diff --check
git status --short
```

After the user approves the preview, stage only `index.html` and `tests/test_build.py` with the rest of the redesign changes and commit at the agreed integration point.
