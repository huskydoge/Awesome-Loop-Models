# Catalog Refresh Automation Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refresh paper metrics daily through one safe repository writer, keep filter metadata under evidence-reviewed automation, and replace `Today` with a newest-intake `Newly Arrived` filter.

**Architecture:** Keep the existing metrics fetcher and workflows. Add a strict pre-write guard and fail-soft provenance retention to `scripts/fetch_metrics.py`; make `update-metrics.yml` the only metrics writer; derive `Newly Arrived` directly from the greatest valid paper `added_date`; and extend the existing Codex daily watch with one deterministic metadata-audit shard per run.

**Tech Stack:** Python 3.11, PyYAML, GitHub Actions, vanilla JavaScript, Python `unittest`, Codex local automation.

---

> **Execution constraint:** Do not run builds or test suites on the current machine under the repository's shared-cluster policy. Add tests before implementation, use the commands below in GitHub Actions, and limit local verification to source inspection and `git diff --check` unless the user explicitly authorizes an exact command.

### Task 1: Make metrics refresh fail safely

**Files:**
- Modify: `tests/test_fetch_metrics.py`
- Modify: `scripts/fetch_metrics.py:1406-1684`

**Step 1: Add focused failure-mode tests**

Add tests beside the existing `fetch_all` provenance tests:

```python
def test_fetch_all_preserves_prior_metrics_and_provenance_on_source_failure(self):
    """A partial or total outage must not erase last-known metric evidence."""
    # Seed citations/stars, both source maps, best-source fields, and
    # metrics_updated in one temporary paper YAML.
    # Return one fresh citation source and no fresh star result.
    # Assert the fresh source is merged, failed-source provenance survives,
    # and the star fields plus their old metrics_updated value are retained.

def test_fetch_all_strict_failure_happens_before_any_write(self):
    """Strict mode must reject missing refresh coverage before persistence."""
    # Seed citations: 0 and github_stars: 0 so zero is treated as known.
    # Mock every citation/star fetch as empty and patch both report writers.
    # Assert RuntimeError names both fields, the YAML is byte-identical,
    # and neither cache/report writer was called.
```

In the strict test, also call `fetch_all(strict=True)` for a second paper with no prior metric fields and assert it does not fail merely because the new paper has no result.

**Step 2: Record the expected pre-implementation failures**

CI command; do not run locally:

```bash
python3 -m unittest tests.test_fetch_metrics
```

Expected before implementation: `fetch_all()` rejects the `strict` keyword, and outage provenance is removed.

**Step 3: Add strict mode before the first write**

Add `strict: bool = False` to `fetch_all`. Immediately after `fetch_stars_parallel(...)` and before the YAML loop, cache save, or link-report save, add:

```python
if strict:
    missing_fresh_metrics = []
    for paper in papers:
        stem = paper["stem"]
        if paper.get("citations") is not None and not citation_source_maps.get(stem):
            missing_fresh_metrics.append(f"{stem}: citations")
        if paper.get("github_stars") is not None and not star_source_maps.get(stem):
            missing_fresh_metrics.append(f"{stem}: github_stars")
    if missing_fresh_metrics:
        raise RuntimeError(
            "Strict metrics refresh failed before write; no fresh value for:\n  - "
            + "\n  - ".join(missing_fresh_metrics)
        )
```

This deliberately guards known fields only. A newly added paper without an established metric remains eligible for the next refresh.

**Step 4: Retain citation evidence and trust the fresh GitHub transport**

Inside the per-paper loop, replace the destructive empty-result branches. Reuse ordinary dictionaries; do not add a provenance class or new file:

```python
old_citation_sources = p.get("citation_sources")
old_citation_sources = old_citation_sources if isinstance(old_citation_sources, dict) else {}
new_citation_sources = {
    **old_citation_sources,
    **citation_source_maps.get(stem, {}),
}
new_citations = max(new_citation_sources.values(), default=p.get("citations"))
best_citation_source = _best_citation_source(new_citation_sources)

fresh_star_sources = star_source_maps.get(stem, {})
if fresh_star_sources:
    best_star_source, new_stars = next(iter(fresh_star_sources.items()))
    new_star_sources = fresh_star_sources
```

Citation indexes are independent evidence, so failed-source citation provenance may be retained while a fresh value corrects the same source. GitHub API and HTML are instead primary/fallback transports for one star counter: the transport that succeeds in the current run is authoritative for the aggregate, provenance, and best source. Keep the existing field-by-field change detection and `metrics_updated` behavior. When no GitHub transport returns, preserve the old star fields byte-for-byte and do not advance freshness.

**Step 5: Expose strict mode in the existing CLI**

```python
parser.add_argument(
    "--strict",
    action="store_true",
    help="Fail before writing when a previously known metric has no fresh value.",
)
```

Pass `strict=args.strict` to `fetch_all(...)`.

**Step 6: Verify in CI and commit**

CI command; do not run locally:

```bash
python3 -m unittest tests.test_fetch_metrics
```

```bash
git add scripts/fetch_metrics.py tests/test_fetch_metrics.py
git commit -m "fix: preserve metrics across source outages"
```

### Task 2: Make the metrics workflow the sole writer

**Files:**
- Modify: `tests/test_asset_budgets.py:359-400`
- Modify: `.github/workflows/build-papers.yml`
- Modify: `.github/workflows/update-metrics.yml`

**Step 1: Rewrite workflow contract tests**

Keep one test for each workflow:

```python
def test_build_workflow_is_read_only_pull_request_validation(self):
    """Catalog CI must validate PRs without network metric fetches or writes."""
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    triggers = workflow[True]
    steps = workflow["jobs"]["build"]["steps"]
    names = {step["name"] for step in steps}

    self.assertEqual(set(triggers), {"pull_request", "workflow_dispatch"})
    self.assertEqual(workflow["jobs"]["build"]["permissions"]["contents"], "read")
    self.assertNotIn("Require Semantic Scholar API key", names)
    self.assertNotIn("Fetch citation counts and GitHub stars", names)
    self.assertFalse(any(name.startswith("Commit ") for name in names))

def test_metric_workflow_is_daily_serialized_main_writer(self):
    """One guarded workflow must own every metric write to main."""
    workflow = yaml.safe_load(UPDATE_METRICS_WORKFLOW_PATH.read_text(encoding="utf-8"))
    triggers = workflow[True]
    job = workflow["jobs"]["update-metrics"]
    steps = {step["name"]: step for step in job["steps"]}

    self.assertEqual(triggers["schedule"], [{"cron": "17 5 * * *"}])
    self.assertEqual(triggers["push"]["branches"], ["main"])
    self.assertIn("workflow_dispatch", triggers)
    self.assertEqual(workflow["concurrency"], {
        "group": "update-paper-metrics-${{ github.ref }}",
        "cancel-in-progress": True,
    })
    self.assertEqual(job["if"], "github.ref == 'refs/heads/main'")
    self.assertIn("--strict", steps["Fetch citation counts and GitHub stars"]["run"])
    self.assertIn("git rev-parse origin/main", steps["Commit updated metrics"]["run"])
    self.assertIn("git push origin HEAD:main", steps["Commit updated metrics"]["run"])
```

Also retain assertions that both workflows run `scripts/build.py`, asset budgets, and the full unittest command, and that the writer stages `papers.json`, `submission-meta.json`, `README.md`, and `TAGS.md`.

**Step 2: Record expected workflow-test failures**

CI command; do not run locally:

```bash
python3 -m unittest tests.test_asset_budgets
```

Expected before implementation: the build workflow still writes, the metrics cron is weekly, strict mode is absent, and concurrency does not cancel stale runs.

**Step 3: Reduce `build-papers.yml` to validation**

- Keep only `pull_request` on `main` and `workflow_dispatch` triggers.
- Change `permissions.contents` from `write` to `read`; retain `pull-requests: read`.
- Keep YAML validation, new-tag review, offline build, asset budgets, and unit tests.
- Delete the API-key requirement, metrics fetch, and commit/push steps.

**Step 4: Promote `update-metrics.yml` to the only writer**

Use the existing workflow and steps; do not create another workflow:

```yaml
on:
  push:
    branches: [main]
  schedule:
    - cron: "17 5 * * *"
  workflow_dispatch:

concurrency:
  group: update-paper-metrics-${{ github.ref }}
  cancel-in-progress: true

jobs:
  update-metrics:
    if: github.ref == 'refs/heads/main'
```

Change the fetch command to `python3 scripts/fetch_metrics.py --strict`. After rebuild, run the existing asset-budget command and full unittest discovery command before staging.

**Step 5: Guard the write against an advanced `main`**

Replace the unconditional commit/push tail with:

```bash
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git add papers
git add -f papers.json submission-meta.json README.md TAGS.md
git diff --cached --quiet && exit 0

base_sha="$(git rev-parse HEAD)"
git fetch --no-tags origin '+refs/heads/main:refs/remotes/origin/main'
if [ "$(git rev-parse origin/main)" != "${base_sha}" ]; then
  echo "::notice::main advanced; a newer push run owns this refresh."
  exit 0
fi

git commit -m "chore: update paper metrics [skip ci]"
if git push origin HEAD:main; then
  exit 0
fi

git fetch --no-tags origin '+refs/heads/main:refs/remotes/origin/main'
if [ "$(git rev-parse origin/main)" != "${base_sha}" ]; then
  echo "::notice::main advanced during push; skipping stale refresh."
  exit 0
fi
exit 1
```

Do not add a rebase loop or Actions cache. A true network/auth failure must remain visible; a superseded run exits cleanly.

**Step 6: Verify in CI and commit**

CI command; do not run locally:

```bash
python3 -m unittest tests.test_asset_budgets
```

```bash
git add .github/workflows/build-papers.yml .github/workflows/update-metrics.yml tests/test_asset_budgets.py
git commit -m "ci: centralize catalog metric refreshes"
```

### Task 3: Replace `Today` with `Newly Arrived`

**Files:**
- Modify: `tests/test_build.py:850-900,1580-1640,1708-1725,3043-3072,3193-3202`
- Modify: `index.html:5161,6327-6336,6581-6620,6960-6970,7443-7525,7580-7710,7845-7860,8117-8125`
- Modify: `papers/_template.yaml.example:47-50`
- Modify: `blogs/_template.yaml.example:58-61`
- Modify: `CONTRIBUTING.md:210-220`

**Step 1: Replace the old date-filter test with one executable behavior check**

Extract `normalizeDateInputValue`, the new latest-date helper, and the matcher into the existing Node subprocess pattern. Assert:

```python
self.assertEqual(json.loads(output), {
    "latest": "2026-09-03",
    "active": [False, False, True, False],
    "inactive": True,
})
```

The fixture should contain an older paper, an invalid-date paper, a newest paper, and a newest-date blog. With the filter active, only the newest paper matches; with it inactive, the blog is not filtered out by this matcher.

Update markup/state assertions to require `newly-arrived-only-toggle`, `NEWLY_ARRIVED_ONLY`, `matchNewlyArrivedOnly`, `toggleNewlyArrivedOnly`, and the label `Newly Arrived`. Add one obsolete-name guard covering `TODAY_ONLY`, `today-only-toggle`, `matchTodayOnly`, and `toggleTodayOnly`. Do not change the separate daily-briefing label `Today`.

**Step 2: Record expected UI-test failures**

CI command; do not run locally:

```bash
python3 -m unittest tests.test_build
```

Expected before implementation: the new control/helper is absent and all old quick-filter names remain.

**Step 3: Derive the newest intake batch from existing paper data**

Replace the control with:

```html
<button type="button" class="sort-btn" id="newly-arrived-only-toggle" aria-pressed="false" onclick="toggleNewlyArrivedOnly()">Newly Arrived</button>
```

Replace the quick-filter state with:

```javascript
let NEWLY_ARRIVED_ONLY = false;
let LATEST_ADDED_DATE = '';
```

Place one helper immediately after `normalizeDateInputValue` so the Node test can reuse the existing source slice:

```javascript
/** Return the greatest valid paper intake date, or an empty string. */
function getLatestAddedDateValue(papers) {
  return papers.reduce(function(latest, paper) {
    const addedDate = normalizeDateInputValue(paper && paper.added_date) || '';
    return addedDate > latest ? addedDate : latest;
  }, '');
}
```

Use it in the renamed matcher:

```javascript
/** Match papers in the newest catalog intake batch. */
function matchNewlyArrivedOnly(paper) {
  return !NEWLY_ARRIVED_ONLY || (
    paper.entry_type !== 'blog'
    && Boolean(LATEST_ADDED_DATE)
    && normalizeDateInputValue(paper.added_date) === LATEST_ADDED_DATE
  );
}
```

After `ALL_PAPERS` is prepared in `buildDOM`, assign:

```javascript
LATEST_ADDED_DATE = getLatestAddedDateValue(ALL_PAPERS);
```

Thread the renamed state through reset, matching, active-count, button-state, toggle, active-label (`newly arrived`), and active-filter checks. Delete the quick-filter-only `REPO_TODAY`, `getBrowserTodayString()`, `getRepoTodayString()`, and the `generated_local_date` assignment. Leave `getCurrentDailyWatchDateString()` intact for the daily briefing.

**Step 4: Document the one canonical meaning of `added_date`**

- Paper template: say `added_date` is the repo intake date and the greatest valid paper value defines the `Newly Arrived` batch.
- Blog template: say `added_date` serves the daily feed; blogs do not participate in `Newly Arrived`.
- `CONTRIBUTING.md`: repeat those semantics once under the existing date guidance.

Do not add a manifest, per-paper refresh timestamp, or new generated field.

**Step 5: Verify in CI and commit**

CI command; do not run locally:

```bash
python3 -m unittest tests.test_build
```

```bash
git add index.html tests/test_build.py papers/_template.yaml.example blogs/_template.yaml.example CONTRIBUTING.md
git commit -m "feat: filter the newest catalog intake"
```

### Task 4: Align the public paper-watch countdown

**Files:**
- Modify: `tests/test_build.py:3073-3082,3256-3290`
- Modify: `assets/daily-watch-countdown.js:5-6,139-151`
- Modify: `index.html:5113-5115`

**Step 1: Update schedule expectations first**

Change the three Node-helper expectations to:

```text
2026-04-24T00:15:00.000Z / Thu 20:15 ET
2026-04-27T00:15:00.000Z / Sun 20:15 ET
2026-01-06T01:15:00.000Z / Mon 20:15 ET
```

Require `Next paper watch` and `20:15 ET Sunday–Thursday` in the markup test.

**Step 2: Change the existing constant and copy**

- Set `DAILY_WATCH_SCHEDULE.minute` to `15`.
- Change the static label to `Next paper watch`.
- Change fallback copy to `20:15 ET Sunday–Thursday · about 15 minutes after arXiv's daily announcement.`
- Change dynamic copy from `next fetch` to `next paper watch`, keeping the existing computed run label.

This countdown describes discovery/metadata review only; do not mention the separate metrics workflow.

**Step 3: Verify in CI and commit**

CI command; do not run locally:

```bash
python3 -m unittest tests.test_build.DailyWatchCountdownLogicTests
```

```bash
git add assets/daily-watch-countdown.js index.html tests/test_build.py
git commit -m "fix: align the paper watch countdown"
```

### Task 5: Extend the existing semantic-review automation

**State:**
- Update through Codex automation tooling: `hermes-daily-awesome-loop-models-watch`
- Do not edit `/Users/husky/.codex/automations/.../automation.toml` directly

**Step 1: Re-read the live automation**

Use automation view immediately before the update. Preserve its name, active status, schedule (`20:15 ET`, Sunday-Thursday), model, reasoning effort, project, destination, and unrelated prompt rules.

**Step 2: Update only the prompt's responsibilities**

- Remove metrics fetching for newly added papers. The repository metrics workflow now owns all citation/star writes and its `main` push trigger handles newly merged papers.
- Add a metadata audit goal for exactly one deterministic shard per run.
- Assign `papers/*.yaml` by `int(hashlib.sha256(relative_path.encode("utf-8")).hexdigest(), 16) % 5`; map Sunday through Thursday to shards `0` through `4`.
- For each selected paper, check only: verified venue/acceptance, official GitHub or Hugging Face code link, and concrete public community-comment URL.
- Require exact primary/first-party evidence. Ambiguous matches, inaccessible evidence, and search snippets are reported but skipped.
- Put verified changes on the existing daily review branch/PR. A no-op audit creates no commit or PR churn. Never push to `main`, merge, or auto-merge.
- Keep the offline build/test instructions and add final-report counts for shard, audited papers, verified changes, and skipped uncertain candidates.

Do not add a second automation or modify the recurrence rule.

**Step 3: Verify persisted state**

View the automation again and confirm:

- status remains active;
- recurrence remains Sunday-Thursday at 20:15 ET;
- the prompt contains the five-shard metadata audit;
- the prompt no longer tells the daily watch to call `fetch_metrics.py`.

This task changes app state, not git; no repository commit is expected.

### Task 6: Final integration verification

**Files:**
- Inspect all files changed in Tasks 1-4

**Step 1: Run lightweight local checks only**

```bash
git diff --check origin/main...HEAD
rg -n "TODAY_ONLY|today-only-toggle|matchTodayOnly|toggleTodayOnly|20:05 ET|minute: 5" index.html assets
git status --short --branch
git diff --stat origin/main...HEAD
```

Expected: `git diff --check` is clean; the obsolete-name search returns no matches; only intended files are changed. Negative assertions in tests may still spell the removed names, and the daily briefing's separate reader-facing `Today` text remains.

**Step 2: Let the pull-request workflows run the heavy checks**

GitHub Actions commands represented by the workflows; do not run locally:

```bash
python3 scripts/build.py
python3 scripts/check_asset_budgets.py
python3 -m unittest discover -s tests -t . -p 'test_*.py'
```

Require the PR checks to pass before merge. After merge, confirm one push-triggered `Update paper metrics` run succeeds and that `Build generated repo artifacts` did not create a direct-main bot commit.
