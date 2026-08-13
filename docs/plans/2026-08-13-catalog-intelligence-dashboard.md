# Catalog Intelligence Dashboard Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the editorial Stats view with a responsive catalog dashboard and correct only paper taxonomy inconsistencies supported by primary-source evidence.

**Architecture:** Keep the static `index.html` application and existing `papers.json` payload. Reuse publication-series, safe DOM, SVG, tab/hash, and loading helpers; add small pure aggregation helpers for release comparison and taxonomy distributions. Treat `papers/*.yaml` as canonical metadata and regenerate checked-in artifacts only through the existing build.

**Tech Stack:** Static HTML/CSS, browser JavaScript, inline SVG, YAML, Python `unittest`, existing repository build scripts.

---

### Task 1: Audit suspicious taxonomy against primary sources

**Files:**
- Inspect: `papers/*.yaml`
- Inspect: `audits/papers/*.yaml`
- Modify only when supported: `papers/<paper-id>.yaml`
- Modify when semantic evidence changes: `audits/papers/<paper-id>.yaml`

**Step 1: Separate mechanical and semantic candidates**

Record the case-only `Looped-Transformer` alias collision as mechanical. Treat `RL`, `graphs`, broad Focus tags, category placement, and the 21 papers without verified audit records as semantic candidates.

**Step 2: Read primary evidence**

Use the linked arXiv/OpenReview paper pages and PDFs. For each semantic candidate, verify the model's repeated computation is inside one forward pass and decide category, mechanism, Focus, and Domain from the paper's main contribution rather than title keywords.

**Step 3: Apply the smallest supported YAML corrections**

Normalize exact vocabulary collisions. Do not rename official aliases, collapse multi-mechanism records, or delete common tags based only on frequency.

**Step 4: Update audit evidence**

For any semantic correction, add or update the matching audit ledger with the primary-source rationale. New audit files must follow the existing template and begin with the repository's normal top-level YAML fields.

**Step 5: Inspect the diff**

```bash
git diff -- papers audits/papers
git diff --check -- papers audits/papers
```

Expected: only evidence-backed paper fields and their audit records change.

### Task 2: Define dashboard aggregation contracts

**Files:**
- Modify: `tests/test_build.py`
- Modify: `index.html`

**Step 1: Update the existing Stats helper regression**

Extend the Node-backed Stats fixture to require:

```javascript
const summary = buildReleaseStatsSummary(papers, daily, monthly);
const category = buildStatsDistribution(papers, 'category');
const mechanism = buildStatsDistribution(papers, 'mechanism_tags');
```

Assert that the summary contains the latest and prior 30-day counts plus a deterministic comparison percentage, distributions sort by descending count then label, and multi-label mechanism counts are not deduplicated across papers.

**Step 2: Do not run the test locally yet**

The shared-node policy requires explicit approval before running the suite. Expected authorized command:

```bash
python3 -m unittest tests.test_build.BuildTest.test_stats_helpers_execute_date_series_and_summary_boundaries
```

**Step 3: Extend the pure summary helper**

Update `buildReleaseStatsSummary()` to return:

```javascript
{
  totalPapers,
  releasesLast30Days,
  releasesPrior30Days,
  releaseChangePercent,
  latestReleaseDate,
  peakMonth
}
```

Use `null` for percentage change when the prior window is zero, avoiding a fake infinity value.

**Step 4: Add one reusable distribution helper**

Implement:

```javascript
function buildStatsDistribution(papers, field) {
  // Return [{ key, count, share }] with one count per paper/value.
}
```

Normalize only empty values and duplicate values within the same paper. Preserve canonical labels and sort by count descending, then label ascending.

### Task 3: Replace the Stats shell with the dashboard layout

**Files:**
- Modify: `tests/test_build.py`
- Modify: `index.html`

**Step 1: Rewrite markup assertions**

Require these landmarks:

```text
stats-dashboard-header
stats-total-papers
stats-latest-thirty
stats-window-change
stats-latest-release
release-pulse-chart
stats-category-distribution
stats-mechanism-distribution
annual-release-volume
latest-releases-list
stats-taxonomy-details
stats-focus-distribution
stats-domain-distribution
```

Assert that obsolete hero signal and Long Arc ids are absent.

**Step 2: Replace the Stats DOM**

Build a compact header, four-cell metric rail, primary 8/4 dashboard grid, secondary 4/8 grid, and native collapsed taxonomy detail. Keep `aria-live`, chart summaries, range buttons, semantic headings, and the existing panel/tab relationship.

**Step 3: Remove obsolete render paths**

Delete hero-latest population, dossier-only nodes, `renderLongArcChart()`, and Long Arc summary code.

### Task 4: Implement the dual-theme dashboard visual system

**Files:**
- Modify: `index.html`
- Modify: `tests/test_build.py`

**Step 1: Replace obsolete Stats CSS**

Use Stats-scoped custom properties in the existing light and dark theme blocks. Implement the 12-column grids, compact metric cells, dense distribution bars, concise latest-release rows, responsive stacking, and visible native `details` state.

**Step 2: Keep accessibility constraints**

Preserve at least 44px touch targets where controls need them, visible `:focus-visible`, text summaries outside SVG, readable muted text, and no hover-only information.

**Step 3: Remove dead styles**

Delete selectors used only by the old hero signal, dossier metadata, and Long Arc. Do not append a second override system below dead CSS.

**Step 4: Perform lightweight source checks**

```bash
rg -n "stats-dashboard-header|stats-primary-grid|stats-taxonomy-details|prefers-color-scheme" index.html
rg -n "stats-hero-latest|long-arc|latest-release-desc|latest-release-authors" index.html
git diff --check -- index.html tests/test_build.py
```

Expected: required dashboard selectors exist; obsolete selectors return no matches; diff check is clean.

### Task 5: Render composition and compact latest releases

**Files:**
- Modify: `index.html`
- Modify: `tests/test_build.py`

**Step 1: Add a safe distribution renderer**

Implement `renderStatsDistribution(container, items, options)` with `createElement`, `textContent`, and CSS width custom properties or a child fill element. Show label, count, and percentage; include a compact empty state.

**Step 2: Simplify latest release rendering**

Keep safe URLs, date, title, category, and Loop Mechanism. Remove authors, abstracts, citation/star footer, duplicate read link, and mixed-axis tag chips.

**Step 3: Use one Release Pulse y-scale**

In `renderReleasePulseChart()`, derive a single maximum from both counts and averages, then use it for bar height, line position, and axis labels.

**Step 4: Wire the complete dashboard once**

`renderStatsPanel()` derives summary and distributions from `ALL_PAPERS`, renders all panels, hides the loading state, and sets `HAS_RENDERED_STATS = true`. Existing range listeners remain bound once.

### Task 6: Regenerate catalog artifacts after approved metadata changes

**Files:**
- Generated: `papers.json`
- Generated: `submission-meta.json`
- Generated: `README.md`
- Generated: `TAGS.md`
- Possibly regenerated with no semantic drift: `assets/repo-meta.js`, `.github/ISSUE_TEMPLATE/config.yml`

**Step 1: Request explicit local-run approval or use Slurm**

Do not run the build without confirmation. Exact local command:

```bash
python3 scripts/build.py
```

Preferred Slurm shape when this checkout is on a cluster:

```bash
sbatch --wait --wrap='cd /Users/husky/Awesome-Loop-Models && python3 scripts/build.py'
```

**Step 2: Inspect generated scope**

```bash
git status --short
git diff --stat
git diff --check
```

Expected: unrelated `figures/` and `loop_transformers_baseline_backbone_report.md` remain untracked and unstaged.

### Task 7: Verify and review

**Files:**
- Modify only for confirmed defects: `index.html`, `tests/test_build.py`, affected metadata files

**Step 1: Request approval for the canonical checks**

```bash
python3 scripts/audit_catalog.py --format human
python3 scripts/check_asset_budgets.py
python3 -m unittest discover -s tests -t . -p 'test_*.py'
```

Run via Slurm when appropriate under the shared-node policy.

**Step 2: Browser verification after approval to start a local server**

Check direct `#stats`, Papers/Stats switching, `90D`/`1Y`/`ALL`, desktop/mobile, light/dark, keyboard focus, empty/error states, page overflow, and console errors.

**Step 3: Independent review**

Review taxonomy evidence and frontend code separately. Fix Critical/Important findings only; avoid unrelated refactors.

**Step 4: Commit exact task files**

```bash
git add index.html tests/test_build.py papers/<changed-id>.yaml audits/papers/<changed-id>.yaml papers.json submission-meta.json README.md TAGS.md
git commit -m "feat: build catalog intelligence dashboard"
```

Do not stage unrelated untracked files.
