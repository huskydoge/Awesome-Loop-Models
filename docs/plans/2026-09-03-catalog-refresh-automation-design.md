# Catalog Refresh Automation Design

## Goal

Keep quantitative paper metrics and the metadata behind the catalog's quick
filters current without treating uncertain web evidence as canonical data.
Replace the date-bound `Today` filter with `Newly Arrived`, meaning the papers
from the catalog's newest intake batch.

## Current Problems

- `Update paper metrics` runs only weekly, while ordinary `main` pushes run a
  second copy of the same fetch-and-write path.
- Both workflows can write directly to `main`; concurrent merges have already
  produced a non-fast-forward bot push.
- Citation-source outages are fail-soft. Old metric values survive, but partial
  results can erase provenance and still make a run look fresh.
- The four quick filters read curated YAML metadata, not citation/star metrics:
  `venue`, `published_date`, `links.github` / `links.hf`, and comments.
- `Today` is anchored to the last build date and paper publication date, so its
  name does not describe a stable catalog-intake concept.
- The public countdown says `20:05 ET`, while the active daily watch runs at
  `20:15 ET` Sunday through Thursday.

## Selected Architecture

Use two deliberately different automation paths.

### Objective metrics: one repository writer

Make the existing metrics workflow the only workflow that fetches and writes
citations, GitHub stars, and generated catalog artifacts. It runs:

- once per day;
- after a push to `main`, so newly merged papers do not wait for the next day;
- on manual dispatch.

Runs share one cancel-in-progress concurrency group. A newer `main` snapshot
supersedes an older run, and the writer checks that `main` has not advanced
before committing. The ordinary build workflow remains validation-only and no
longer fetches metrics or pushes a bot commit.

The metrics fetch keeps old values and old source provenance when a source is
temporarily unavailable. CI strict mode fails before writing when a paper with
a previously known citation or star value receives no fresh value from any
eligible source. A successful generated timestamp therefore represents a
completed metric check rather than merely a completed static build.

No persistent Actions cache is added. The current cache TTLs would make a
daily job reuse citation data for seven days and star data for three days,
which conflicts with the requested daily freshness.

### Curated status metadata: evidence-reviewed PRs

Extend the existing daily Awesome Loop Models watch instead of adding a second
semantic crawler. Each Sunday-through-Thursday run still discovers new papers
and additionally audits one stable weekday shard of existing papers. Across
one active week, every paper is reconsidered for:

- a verified venue/acceptance change;
- an official GitHub or Hugging Face code link;
- a concrete public community-comment URL.

Only exact primary or first-party evidence can change canonical YAML. Ambiguous
matches, inaccessible sources, and search-only guesses are reported and
skipped. Verified metadata changes join the daily review branch and pull
request; they never write directly to `main` or merge automatically. A no-op
audit creates no repository churn.

### Newly Arrived filter

Rename `Today` to `Newly Arrived`. At catalog load time, compute the greatest
valid `added_date` among papers. The filter includes only papers whose
`added_date` equals that value.

This reuses existing canonical data and needs no new flag, manifest, timestamp,
or time-zone logic. It means "the newest batch present in this catalog," even
when a scheduled watch or human review finishes late. Blogs remain excluded.

The countdown is updated to the actual `20:15 ET` daily-watch schedule. It
describes paper discovery, not the separate metrics refresh.

## Data Flow

```text
Semantic Scholar / OpenAlex / OpenCitations / Crossref / GitHub
    -> daily repository metrics workflow
    -> strict freshness guard
    -> papers/*.yaml + generated artifacts
    -> bot commit on current main

Daily research watch
    -> new-paper discovery + one stable metadata-audit shard
    -> exact-source verification
    -> review branch and PR when canonical metadata changes

papers/*.yaml added_date
    -> scripts/build.py
    -> papers.json
    -> max added_date
    -> Newly Arrived filter
```

## Failure Handling

- A transient metrics-source failure preserves the last known value and
  provenance.
- Missing fresh coverage for previously known metrics fails the writer before
  commit; the old published snapshot stays intact and GitHub Actions reports
  the failure.
- If `main` advances during a refresh, the stale run exits without pushing and
  the newer push-triggered run owns the refresh.
- An uncertain venue, code, or comment match never changes YAML.
- A failed or no-op semantic audit does not change the `Newly Arrived` batch.

## Verification

Add focused coverage for:

- latest-`added_date` selection and `Newly Arrived` filter behavior;
- the renamed control, active-filter label, and removal of `Today` state;
- preservation of old values/provenance on partial source failure;
- strict-mode failure when a previously known metric has no fresh result;
- workflow triggers, single-writer behavior, concurrency, and the stale-HEAD
  guard;
- the countdown's `20:15 ET` schedule.

Local work is limited to lightweight source inspection and `git diff --check`.
The full build and unit suite run in GitHub Actions under the repository's
shared-cluster execution policy.

## Scope Boundaries

- Do not auto-infer acceptance from a generic API venue string.
- Do not scrape Google Scholar or fabricate comment links.
- Do not add a database, service, dependency, third metrics workflow, or
  per-paper audit timestamp.
- Do not auto-merge semantic metadata updates.
