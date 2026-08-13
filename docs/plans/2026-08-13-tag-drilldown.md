# Tag Drill-down Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Let readers click Stats taxonomy tags, open an exact paper-only result set, and continue searching within a visible locked tag prefix.

**Architecture:** Extend the existing static single-page UI. Native links encode the existing `group::label` key as `?tag=…#papers`; one locked tag is restored from the URL into the existing `ACTIVE_TAG_FILTERS` set, while the existing text search supplies the AND query. No new page, payload, renderer, or dependency.

**Tech Stack:** Vanilla HTML/CSS/JavaScript in `index.html`, Python `unittest` contracts in `tests/test_build.py`, native `URL`, `URLSearchParams`, and History APIs.

---

### Task 1: Lock URL-backed paper-only tag state

**Files:**
- Modify: `tests/test_build.py`
- Modify: `index.html` near state declarations, tag helpers, `getFilteredPapers`, and catalog initialization

**Step 1: Write the failing tests**

Add contracts proving:

```python
self.assertIn("let LOCKED_TAG_FILTER_KEY = '';", html)
self.assertIn("function getTagDrilldownKeyFromUrl() {", html)
self.assertIn("function restoreTagDrilldownFromUrl() {", html)
self.assertIn("LOCKED_TAG_FILTER_KEY ? ALL_PAPERS : ALL_RESOURCES", html)
self.assertIn("window.addEventListener('popstate'", html)
```

Add a small Node harness that supplies `URL`, `history`, `ALL_PAPERS`, `TAG_FILTER_LOOKUP`, and the tag state, then verifies valid, malformed, and unknown `tag` values plus Back/Forward restoration.

**Step 2: Run the focused test and verify RED**

Run:

```bash
/opt/homebrew/bin/python3.13 -m unittest tests.test_build.FrontendFeatureTests.test_tag_drilldown_uses_validated_url_state
```

Expected: FAIL because the route helpers do not exist.

**Step 3: Implement the minimum state helpers**

Add documented helpers equivalent to:

```js
function getTagDrilldownKeyFromUrl() {
  if (window.location.hash !== '#papers') return '';
  var key = new URL(window.location.href).searchParams.get('tag') || '';
  return Object.prototype.hasOwnProperty.call(TAG_FILTER_LOOKUP, key)
    && ALL_PAPERS.some(function(paper) { return paper._tagKeySet.has(key); })
    ? key : '';
}

function getFilteredPapers(query, publicationDateFilter) {
  var resources = LOCKED_TAG_FILTER_KEY ? ALL_PAPERS : ALL_RESOURCES;
  return resources.filter(function(paper) {
    return paperMatchesActiveFilters(paper, query, publicationDateFilter);
  });
}
```

`restoreTagDrilldownFromUrl()` removes the previous locked key, validates the new one, adds it to `ACTIVE_TAG_FILTERS`, restores `q` into the existing input, updates the prefix/filter UI, and reruns search. Bind it to `popstate`, `hashchange`, and the post-build restore point.

**Step 4: Run the focused tests and verify GREEN**

Run the focused `FrontendFeatureTests` methods. Expected: PASS.

**Step 5: Commit**

```bash
git add index.html tests/test_build.py
git commit -m "feat: add URL-backed tag drill-down state"
```

### Task 2: Add clickable Stats rows and the search prefix

**Files:**
- Modify: `tests/test_build.py`
- Modify: `index.html` near search markup/styles, Stats distribution renderer, and tag interactions

**Step 1: Write the failing tests**

Require:

```python
self.assertIn('id="search-tag-scope"', html)
self.assertIn('id="search-tag-scope-clear"', html)
self.assertIn("options.tagGroup", html)
self.assertIn("data-tag-key", stats_renderer)
self.assertIn("{ tagGroup: 'mechanism' }", html)
self.assertIn("{ tagGroup: 'focus' }", html)
self.assertIn("{ tagGroup: 'domain' }", html)
```

The runtime test must assert the generated Stats anchor contains the encoded `group::label`, a count-specific accessible label, and that clearing the prefix preserves the input query.

**Step 2: Run the focused test and verify RED**

Expected: FAIL because Stats rows are non-interactive and the prefix is absent.

**Step 3: Implement the minimum UI**

- Wrap the current search icon/input/count in `.search-field` and prepend one hidden `.search-tag-scope` token with a clear button.
- Add only the CSS needed for the token, focus state, Stats link hover/focus, and mobile wrapping.
- Let `renderStatsDistribution` create a native `<a>` only when `options.tagGroup` is supplied. Category rows remain plain.
- Use `?tag=${encodeURIComponent(tagKey)}#papers` as the real `href`; intercept ordinary same-tab clicks for a no-reload transition while retaining native new-tab/copy-link behavior.
- Change paper-card tag clicks to the same navigation helper.
- Add `aria-pressed` to advanced filter chips and disable the locked chip.
- Update `q` using `history.replaceState`; tag navigation and clear use `pushState`.

**Step 4: Run focused and full tests**

Run:

```bash
/opt/homebrew/bin/python3.13 -m unittest tests.test_build
/opt/homebrew/bin/python3.13 -m unittest discover -s tests -t . -p 'test_*.py'
```

Expected: PASS.

**Step 5: Commit**

```bash
git add index.html tests/test_build.py
git commit -m "feat: make taxonomy tags searchable"
```

### Task 3: Browser verification and review

**Files:**
- Verify: `index.html`
- Verify: `tests/test_build.py`

**Step 1: Serve the worktree**

Run a local static server and open `#stats`.

**Step 2: Verify the interaction**

Check Stats → mechanism/focus/domain links, exact paper count, free-text AND search, clear preserving text, reload, Back/Forward, copied URL, unknown tag fallback, keyboard focus, mobile, and light/dark.

**Step 3: Run final static checks**

```bash
git diff --check
git status --short
```

**Step 4: Request two read-only reviews**

One reviewer checks URL/filter correctness and paper-only count consistency; one checks accessibility, responsive layout, and unnecessary complexity. Fix only actionable findings, then rerun the narrowest affected check.

**Step 5: Integrate**

Fast-forward the validated implementation branch into `codex/catalog-intelligence-dashboard`, preserving the unrelated untracked `figures/` and `loop_transformers_baseline_backbone_report.md`.
