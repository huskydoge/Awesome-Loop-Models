# Daily Briefing and Browser Payload Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a neutral expandable Today report and replace the false raw-size CI failure with a compact, browser-only catalog payload guarded by its transferred gzip size.

**Architecture:** Keep YAML records and Markdown briefings as the complete source of truth. Project only browser-consumed fields into compact JSON, render the latest briefing with native `<details>`, and retain the 60 KB deterministic-gzip gate as the trigger for future static sharding.

**Tech Stack:** Python standard library, static HTML/CSS/JavaScript, existing `unittest` contracts.

---

### Task 1: Project a compact browser catalog

**Files:**
- Modify: `scripts/build.py`
- Test: `tests/test_build.py`

**Steps:**

1. Update `DailyBriefingBuildTests.test_build_json_trims_briefings_for_browser_without_changing_catalog_entries` so fixtures contain source/provenance fields and the assertions require those fields to be absent from the emitted papers and blogs without mutating the input records.
2. Add one documented browser-entry serializer with an explicit allowlist of fields consumed by `index.html`.
3. Use that serializer for `payload["papers"]` and `payload["blogs"]` and serialize `papers.json` with compact JSON separators.
4. Leave README and submission metadata generation on the complete records.

### Task 2: Restore the neutral Today disclosure

**Files:**
- Modify: `index.html`
- Test: `tests/test_build.py`

**Steps:**

1. Replace the biased Today test assertions with contracts for native `<details>/<summary>`, briefing summary, `verdict === 'added'` membership, per-paper descriptions, and `must_read` stars.
2. Replace the status-only markup with a native disclosure whose collapsed label is `Today · N papers`.
3. Add focused CSS for the disclosure body and paper rows while preserving the existing in-flow responsive layout.
4. Change `updateDailyBriefingNotice` to accept the latest serialized briefing, join its added candidate IDs to `ALL_PAPERS`, render its summary plus descriptions, and prepend `🌟` only for `must_read` papers.
5. Remove all `Husky recommended` markup, styling, and logic. Do not connect this report to the publication-date Today filter.

### Task 3: Gate transferred size instead of pretty-print size

**Files:**
- Modify: `scripts/check_asset_budgets.py`
- Test: `tests/test_asset_budgets.py`
- Modify: `CONTRIBUTING.md`

**Steps:**

1. Remove the `papers.json` raw-byte constant, measurement, and raw-limit contract test.
2. Keep the deterministic 60 KB gzip check and all JSON/schema/briefing checks.
3. Document that the gzip limit must trigger manifest plus bounded static shards, not another limit increase.

### Task 4: Verify and hand off

**Files:**
- Regenerate: `papers.json`, `submission-meta.json`, `README.md`, `TAGS.md`

**Prepared commands (do not run locally without explicit cluster-policy approval):**

```bash
/opt/anaconda3/bin/python3.12 scripts/build.py
/opt/anaconda3/bin/python3.12 scripts/check_asset_budgets.py
/opt/anaconda3/bin/python3.12 -m unittest \
  tests.test_build.DailyBriefingBuildTests.test_build_json_trims_briefings_for_browser_without_changing_catalog_entries \
  tests.test_build.TagFilterUiTests.test_daily_briefing_notice_is_a_neutral_expandable_report_in_document_flow \
  tests.test_asset_budgets.AssetBudgetContractTests
```

**Safe local checks:**

```bash
rg -n "Husky recommended|daily-briefing-recommended|verdict === 'added'|PAPERS_RAW_BYTES_LIMIT" index.html tests scripts CONTRIBUTING.md
git diff --check
git status --short --branch
```
