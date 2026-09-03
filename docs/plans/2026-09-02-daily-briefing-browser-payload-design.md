# Daily Briefing and Browser Payload Design

## Goal

Restore a neutral, expandable Today report and make the catalog's performance gate track the bytes users actually download.

## Design

- Keep one YAML file per paper or blog as the version-controlled source of truth. A checked-in database would make reviews and merges opaque, while a hosted database would add an unnecessary backend to GitHub Pages.
- Render the existing Today strip as native `<details>`. Its collapsed summary shows only `Today · N papers`; the expanded body shows the latest briefing summary and its `verdict: added` papers. A paper gets `🌟` only when its existing `must_read` flag is true.
- Build `papers.json` as a compact browser projection. Exclude source, provenance, and generator-only fields that `index.html` does not consume; keep the complete in-memory records for README and submission metadata generation.
- Remove the uncompressed JSON hard limit. GitHub Pages serves the asset with gzip, so retain the deterministic 60 KB gzip limit as the user-facing performance gate. If that limit is reached, split the catalog into a manifest and bounded lazy-loaded chunks instead of increasing the limit.

## Boundaries

- No database, framework, WASM runtime, backend service, or new dependency.
- Do not change paper YAML, briefing content, Today filter semantics, or the existing `must_read` data model.
- Preserve the user's unrelated primary-worktree files by implementing from `origin/main` in an isolated worktree.

## Verification

Use focused source-contract tests for the disclosure and browser projection, the asset-budget tests, the canonical build, the offline budget checker, and `git diff --check`. Under the active cluster policy, prepare these commands but do not run builds or tests locally without explicit authorization.
