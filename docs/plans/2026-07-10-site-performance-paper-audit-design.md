# Site Performance and Paper Audit Design

## Goal

Improve the public catalog's load and interaction performance while reviewing every canonical paper entry against primary-source evidence for scope, descriptive accuracy, classification, and tags.

The site must remain a zero-framework static site deployable directly through GitHub Pages. Paper and blog YAML files remain the content source of truth, and generated artifacts remain reproducible through `scripts/build.py`.

## Current State

- The catalog is a single static page whose CSS and JavaScript live in `index.html`.
- `index.html` fetches the generated `papers.json` payload and renders category cards plus an optional table view.
- The payload includes all historical briefing content even though the catalog only displays the newest briefing summary.
- Category sections render their cards during DOM construction and then render the same cards again through the initial search pass.
- The submission page fetches the full catalog payload for a much smaller metadata use case.
- Structural validation is strong for paper category, `mechanism_tags`, and `focus_tags`, but weak for required prose fields, link consistency, `domain_tags`, cross-axis semantics, and primary-source accuracy.
- Paper source review is not recorded durably, so later maintainers cannot distinguish verified claims from unreviewed metadata.

## Design Principles

1. Preserve static hosting and browser compatibility; do not introduce a framework or package-manager build.
2. Reduce transferred and rendered work before attempting complex pagination or virtualization.
3. Keep source YAML human-readable and keep audit evidence out of the public browser payload.
4. Treat automated semantic checks as review routing, not authority to rewrite research metadata.
5. Require primary-source evidence before changing scope, category, mechanism, focus, domain, or descriptive claims.
6. Preserve existing user changes and unrelated untracked reports and figures.

## Performance Architecture

### Catalog payload

`scripts/build.py` will continue loading complete paper, blog, and briefing records for README generation. The browser-facing JSON representation will be narrowed separately:

- include all paper and blog fields used by the catalog;
- include only the latest briefing and only the fields rendered by `index.html`;
- exclude historical briefing bodies from the public catalog payload;
- generate a small submission metadata artifact containing only source paths and tag inventories used by `submit.html`.

This keeps the Python build model complete while avoiding accidental data loss in generated documentation.

### Rendering

Category construction will create section shells and empty grids. One initial call to the existing filter/render pipeline will populate cards. Table rows will remain lazy and will only exist while table view is active.

Search and filter behavior remains unchanged. Caching, pagination, and virtualized lists are deferred until browser measurements show they are needed after eliminating duplicated work.

### Static resources

- Replace the oversized favicon with an appropriately sized asset while retaining the same visual identity.
- Remove the Google Fonts critical request chain in favor of the existing system font stack unless visual inspection shows unacceptable regression.
- Add deterministic byte-size checks for generated payloads and unusually large critical assets.

Extracting all inline CSS and JavaScript is not part of the first pass: the gzipped HTML is already relatively small, and extraction would create broad test and cache-versioning churn before the larger payload and rendering wins are realized.

## Paper Audit Architecture

### Structural catalog auditor

A new documented Python command will read canonical YAML without mutating it and report:

- missing, empty, incorrectly typed, or unknown fields;
- malformed URLs and paper-ID/link mismatches;
- duplicate titles, canonical paper links, or source paths;
- inconsistent dates requiring manual review;
- invalid controlled tags and duplicate values;
- domain/alias cross-axis collisions and deprecated spellings;
- description style issues such as excessive length or multiple claims packed into one sentence.

Hard schema violations will fail. Evidence-dependent or taxonomy-dependent findings will be warnings.

### Audit ledger

Each canonical paper will receive a separate review record under `audits/papers/`. Records will not be emitted into `papers.json`. A record will contain:

- paper ID and canonical source URL;
- source version or revision date;
- verification date and review status;
- scope evidence showing reuse of a learned internal module within one forward process;
- evidence and rationale for category, mechanism, focus, and domain tags;
- checks for title, authors, venue, description claims, and link ownership;
- confidence plus unresolved questions.

The initial ledger may mark entries `needs-review`; an entry becomes `verified` only after primary-source inspection. The goal is complete only when all canonical paper entries have a verified record or an explicit removal decision.

### Review order and corrections

Review will proceed in risk-ranked batches:

1. suspected scope violations and standard recurrence/diffusion ambiguities;
2. papers with multiple mechanism tags or mechanism/description tension;
3. domain/alias axis collisions and singleton tags;
4. missing metadata and date/venue inconsistencies;
5. the remaining catalog.

Corrections will be applied to paper YAML only after evidence is recorded. Generated README, TAGS, and JSON files will be refreshed from the corrected sources.

## Data Flow

```text
papers/*.yaml + blogs/*.yaml + briefings/**/*.md
                |
                v
          scripts/build.py
          /       |       \
         v        v        v
    README.md  papers.json  submission metadata

papers/*.yaml + audits/papers/*.yaml
                |
                v
       structural and evidence audit
                |
                v
      errors, warnings, review coverage
```

## Error Handling

- Build-time structural errors identify the exact source path and field.
- The catalog retains its existing user-facing fetch failure state.
- Submission metadata fetch failure reports a specific message rather than silently using incomplete tag data.
- Network or inaccessible-paper failures leave the audit record unresolved; they never produce speculative corrections.
- Venue-year versus preprint-year differences are warnings unless the source proves the stored value wrong.

## Verification

Lightweight checks performed locally:

- inspect generated byte sizes and briefing payload composition;
- parse generated JSON;
- run the catalog auditor in report-only mode;
- verify audit coverage and source/audit ID parity;
- run `git diff --check`;
- inspect the local site in a real browser for initial rendering, search, filters, table switching, and submission metadata loading.

The repository's build and unit-test suite will not be run automatically on this machine under the cluster execution policy. The exact commands will be provided for CI or an approved Slurm execution:

```bash
python3 scripts/build.py
python3 -m unittest discover -s tests -t . -p 'test_*.py'
```

Completion requires evidence for both halves of the goal: measurable payload/rendering improvement and primary-source-backed coverage of every canonical paper.
