# Paper Stats Tab Design

## Goal

Add a prominent `Papers | Stats` navigation layer to the catalog so readers can see how many papers enter the collection each day, how the collection grows cumulatively, and how the catalog's papers are distributed by publication month.

## Product Structure

The main content area will gain a persistent two-tab navigation:

- `Papers` remains the default and contains all existing category, table, search, and filter behavior.
- `Stats` presents catalog-wide statistics that do not change with the current search query, tag selection, publication-date filter, or paper view mode.

The selected top-level tab is reflected in the URL as `#papers` or `#stats`. Refreshing or sharing a Stats URL restores the Stats panel. The tabs use standard `tablist`, `tab`, and `tabpanel` semantics and support left/right keyboard navigation.

The existing `Category view | Table view` control remains a Papers-only presentation choice. It is not expanded into a third Stats view.

## Data Semantics

`added_date` and `published_date` describe different events and must remain separate:

- `added_date` is the repository intake date and is the only source for catalog-growth statistics.
- `published_date` is the source paper's release date and is used only for the publication timeline.

All current papers have a `published_date`. Thirty-nine papers currently lack `added_date`, but Git history provides an exact first-add date for every one of them: 37 were first added on 2026-04-24, one on 2026-04-26, and one on 2026-05-11. These dates will be written into the canonical paper YAML files. No release date will be substituted for an intake date.

After the backfill, every paper has a durable, explicit intake date. Future statistics continue to read the same generated `papers.json` fields without adding a second stats payload or build-time chart artifact.

Blogs are excluded from both timelines because the feature is explicitly about papers.

## Stats Content

### Summary metrics

The Stats panel begins with compact KPI cards:

- total catalog papers;
- papers added in the most recent seven calendar days represented by the catalog data;
- intake-date coverage;
- peak intake day and its paper count.

The calculation uses the latest recorded `added_date` as the data anchor rather than the viewer's wall-clock date. This keeps historical snapshots meaningful when a daily update has not run recently.

### Catalog Growth

The primary timeline uses daily granularity from the earliest through the latest `added_date`, including zero-addition dates:

- bars show papers added on each date;
- a line shows the cumulative number of catalog papers;
- axes and labels identify repository intake dates and paper counts;
- a readable summary below the chart lists recent non-zero intake dates.

Because all missing dates are backfilled from Git history, the cumulative line starts from the first actual repository intake and ends at the current paper total. There is no synthetic legacy baseline.

### Publication Trend

The secondary timeline groups `published_date` values by calendar month across the catalog's full 2015–2026 range:

- bars show papers in the current catalog released during each month;
- the cumulative line shows how the current catalog is distributed over publication time;
- copy labels the chart as “Papers in this catalog by publication month” so it is not mistaken for a comprehensive measure of the entire research field.

## Rendering Architecture

The page remains a zero-framework, zero-third-party-dependency static site. `index.html` will aggregate dates from the already-loaded `papers.json` and render responsive inline SVG charts.

Stats rendering is lazy: the SVG markup is constructed on the first switch to `Stats` and reused afterward. Default Papers loading therefore avoids chart-render work. The implementation adds no Chart.js, D3, CDN request, new JSON artifact, or generated SVG file.

Both charts share a small internal data-series and SVG-rendering path. CSS uses the existing color variables and dark-theme media query. Charts have a minimum readable width inside an overflow container on small screens. The first version does not animate, so it respects reduced-motion needs by construction.

## Accessibility

- Top-level navigation uses ARIA tab semantics with selected state, focus management, and left/right arrow-key behavior.
- Each SVG has a descriptive title and text summary.
- Daily/monthly counts are not conveyed only by color or pointer hover.
- Recent non-zero periods are exposed as normal HTML text below the visualizations.
- Chart colors maintain usable contrast in both existing themes.

## Error Handling

- Invalid dates are already rejected by the canonical Python build; browser aggregation still ignores a malformed record instead of failing the page.
- If no usable intake dates exist, the total KPI remains visible and Catalog Growth shows an explanatory empty state.
- If no publication dates exist, Publication Trend shows its own empty state without affecting Catalog Growth.
- A `papers.json` fetch failure continues to use the catalog's existing page-level failure state.

## Verification

Automated coverage should verify:

- all canonical paper YAML files have `added_date` after the Git-history backfill;
- daily aggregation fills zero-count dates and computes the correct cumulative totals;
- monthly publication aggregation crosses year boundaries correctly;
- seven-day and peak-day KPIs use deterministic date anchors;
- `#papers` and `#stats` restore the correct panel;
- keyboard tab navigation and lazy Stats rendering are wired correctly;
- empty and partially malformed date inputs produce readable fallbacks.

Local work follows the repository's shared-cluster policy: use lightweight source inspection, focused static assertions, `git diff --check`, and browser interaction checks. Do not run the build or unit-test suite locally without explicit approval. CI or an approved Slurm execution should run:

```bash
python3 scripts/build.py
python3 -m unittest discover -s tests -t . -p 'test_*.py'
```

## Scope Boundaries

The first release does not add date-range controls, chart animations, downloads, framework dependencies, server-side analytics, or search/filter-aware charts. Those can be considered after the two timelines establish a stable and understandable Stats surface.
