# Publication signals implementation plan

> **For Codex:** Use executing-plans to implement this plan task by task.

**Goal:** Show verified publication venues, a Peer-reviewed filter, and an explained High influence badge.

**Architecture:** Keep canonical paper YAML and the static browser payload. Verify publication metadata against official proceedings or accepted OpenReview records; unknown results do not erase saved evidence. Reuse the existing daily update workflow, filter state, metrics renderer and date parser.

**Tech Stack:** Existing Python/PyYAML, standard-library HTTP/HTML/JSON parsing, vanilla JavaScript and CSS.

## Approved rules

- Publication evidence and citation influence are independent. Blogs get neither signal.
- Peer-reviewed includes curated conference/workshop/journal venues already recorded in the catalog, plus newly verified publications. Explicit boolean status takes precedence; missing crawler evidence must not exclude existing publication records (user correction: EqR/ICML). Submission pages alone do not count. Unresolved preprints remain arXiv.
- High influence means citations strictly exceed completed calendar months since first public release (`published_date`), with a minimum of one month. UTC date boundaries, month-end anniversaries clamped to the last day of the month. Missing/invalid/future dates or citation counts yield no badge.
- The badge appears beside citation counts in cards, detail and table views. Hover and keyboard focus reveal the raw count, start date, as-of date and exact threshold; it is a citation-rate heuristic, not a quality judgment.
- Venue labels share one formatter across cards, details, and tables: append the recorded publication `year`, leave arXiv/blog labels unchanged, and avoid duplicate years. Correct cross-year venue metadata from official sources without changing `published_date` or influence calculations.

## Task 1: Browser signals

Modify `index.html`, `assets/reading-desk.css`, `tests/test_build.py`, `tests/reading-desk-check.cjs`. Add regression cases first for strict comparison, month ends, invalid data and explicit peer-review status. Reuse Accepted only's wiring and shared metrics rendering; cover table view separately.

## Task 2: Verified publication metadata

Add `scripts/fetch_publication.py` and `tests/test_publication.py`. Reuse existing HTTP/paper-loading utilities, bound requests and keep a dry-run default. Store `peer_reviewed`, `venue_source` and `venue` only with evidence. Extend `scripts/build.py`, `scripts/audit_catalog.py` and their tests for the new metadata, preserving curated records on fetch failures. Add the refresh step to the existing metrics workflow.

## Task 3: Backfill and verification

Only after the user's requested local-execution approval, run:

```sh
/opt/anaconda3/bin/python3.12 -m unittest tests.test_publication tests.test_build tests.test_audit_catalog
node tests/reading-desk-check.cjs
/opt/anaconda3/bin/python3.12 scripts/fetch_publication.py --write
/opt/anaconda3/bin/python3.12 scripts/build.py
```

Inspect the generated metadata, review the focused diff, run `git diff --check` and manually verify the served page in light/dark and narrow layouts. Do not push this feature without a new publishing request. Local test restrictions take precedence over the test-first execution workflow; pending permission must be reported honestly.
