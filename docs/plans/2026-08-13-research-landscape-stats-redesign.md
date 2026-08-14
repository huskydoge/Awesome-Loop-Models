# Personal-Site-Aligned Catalog Redesign Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Restyle the complete static catalog to share the personal site's editorial academic brand while retaining existing catalog behavior.

**Architecture:** Keep the single-file application and current data/rendering pipeline. Replace presentation at existing shared seams and add only the Stats view fragments required for the approved Research Landscape.

**Tech Stack:** Static HTML, CSS, and JavaScript with Python `unittest` source contracts.

---

## Task 1: Shared brand shell

**Files:** `index.html`, `submit.html`, `tests/test_build.py`

- Replace global color, type, spacing, header, navigation, button, and focus tokens.
- Use the `LM` mark, text navigation, and underlined active state on both pages.
- On desktop, use a 52px masthead, 28px `LM` mark, and 32px visual action buttons; keep the existing mobile 58px/44px interaction sizing.
- Keep existing targets and event wiring.

## Task 2: Editorial Papers surface

**Files:** `index.html`, `tests/test_build.py`

- Convert paper cards to separator-based publication rows.
- Restyle search, filters, directory, tags, links, table, and empty states.
- Preserve URL-backed tag filtering, search prefix, category navigation, and density modes.

## Task 3: Research Landscape Stats

**Files:** `index.html`, `tests/test_build.py`

- Replace the stretched dark dashboard with a natural-height white grid.
- Reuse the release aggregation for the trend and KPI strip.
- Render category as a donut; render mechanism, focus, and domain as multi-label ranked bars.
- Show Top 6 active directions and put the full tag inventory in an independent native `details` explorer with search.
- Keep a compact latest-publications list and remove redundant annual/long-arc content.

## Task 4: Tighten desktop masthead proportions

**Files:** `index.html`, `tests/test_build.py`

1. Add a focused source contract for the 52px desktop masthead, 28px brand mark, 32px action buttons, and unchanged 58px mobile masthead.
2. Confirm the new contract is absent with a narrow `rg` check; do not run the test suite without explicit permission.
3. Update only the final personal-site CSS override. Leave toolbar markup, status cards, search, and mobile sizing unchanged.
4. Reload `http://127.0.0.1:8766/#papers` and compare the header-to-toolbar proportion at desktop width.
5. Run `git diff --check` and retain the exact focused unit-test command for user execution.

## Task 5: Static and visual verification

- Run `git diff --check` and narrow `rg` contracts.
- With explicit permission, serve the isolated worktree using:

```bash
/opt/homebrew/bin/python3.13 -m http.server 8766 --bind 127.0.0.1
```

- Verify desktop and 390px mobile views, tag links/search, Stats ranges, focus order, dark mode, overflow, error state, and console errors.
- Do not run the test suite locally without explicit permission. Prepared command:

```bash
/opt/homebrew/bin/python3.13 -m unittest discover -s tests -t . -p 'test_*.py'
```
