# Responsive Daily Toolbar Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Keep the Today report and refresh countdown compact, balanced, and usable from desktop through phone widths.

**Architecture:** Wrap the existing native disclosure and countdown in one wrapping status row. CSS keeps the collapsed disclosure intrinsic-width, expands only the open report, and draws a decorative rotating clock beside the unchanged digital countdown; the existing data and JavaScript flow remains authoritative.

**Tech Stack:** Static HTML, CSS Flexbox, existing vanilla JavaScript, Python `unittest` source-contract checks.

---

### Task 1: Lock the responsive contract

**Files:**
- Modify: `tests/test_build.py:1580-1680`

**Step 1: Update the static contract check**

Require a wrapping, top-aligned `.daily-status-row`, intrinsic-width collapsed Today control, expanded-report rule, 44px summary target, decorative clock, reduced-motion fallback, and absence of `aria-live` on the ticking value.

**Step 2: Verify the check would exercise the old layout**

CI command: `/opt/anaconda3/bin/python3.12 -m unittest tests.test_build.BuildTests.test_daily_briefing_notice_is_a_neutral_expandable_report_in_document_flow`

Expected before implementation: FAIL because the wrapper and final responsive rules do not exist. Do not run locally under the active execution policy.

### Task 2: Implement the shared status region

**Files:**
- Modify: `index.html:2251-2444`
- Modify: `index.html:3535-3569`
- Modify: `index.html:3960-3991`
- Modify: `index.html:5092-5107`

**Step 1: Group existing markup**

Wrap the Today `<details>` and refresh countdown in `<div class="daily-status-row">`; keep their IDs and data hooks, remove `aria-live="polite"` from the ticking value, and add an `aria-hidden` clock plus a small copy wrapper.

**Step 2: Replace detached layouts**

Make `.daily-status-row` a centered, wrapping flex row with `align-items: flex-start`. Remove the countdown's absolute-position ticket styling and the `769-1344px` equal-column toolbar layout.

**Step 3: Add the phone treatment**

Keep collapsed Today and the countdown at their content width, expand only `.daily-briefing-notice[open]`, and visually omit the verbose schedule copy. At `max-width: 768px`, order the toolbar as subtitle, daily status, search, filters; only the open report becomes full width.

**Step 4: Preserve interaction quality**

Give the Today summary a 44px minimum height, allow long briefing titles/descriptions to wrap, and animate the CSS clock hand with `steps(60)` while disabling it under `prefers-reduced-motion`.

### Task 3: Verify locally without a heavy test run

**Files:**
- Verify: `index.html`

**Step 1: Static checks**

Run: `git diff --check`

Expected: no output.

**Step 2: Browser checks**

Reload `http://127.0.0.1:8123/index.html` and inspect 1440x900, 1024x768, 768x900, 390x844, and 320x700. At every width confirm `scrollWidth <= innerWidth`; confirm the collapsed controls stay compact, the countdown remains at the report's top edge while both fit and wraps below it on narrow screens, and the phone report expands to the full content width.

**Step 3: Defer canonical tests**

GitHub Actions command: `/opt/anaconda3/bin/python3.12 -m unittest discover -s tests -t . -p 'test_*.py'`

Expected: PASS. Do not run locally under the active execution policy.

### Task 4: Commit the focused change

**Files:**
- Modify: `index.html`
- Modify: `tests/test_build.py`
- Add: `docs/plans/2026-09-02-responsive-daily-toolbar-design.md`
- Add: `docs/plans/2026-09-02-responsive-daily-toolbar.md`

**Step 1: Commit**

```bash
git add index.html tests/test_build.py docs/plans/2026-09-02-responsive-daily-toolbar-design.md docs/plans/2026-09-02-responsive-daily-toolbar.md
git commit -m "fix: make daily toolbar responsive"
```
