# Research Landscape Stats Redesign

## Goal

Replace the current Stats dashboard with a compact Scientific Atlas that explains the size, publication activity, structural composition, and active research directions of the loop-model catalog.

## Design Direction

Use a light, precise research-atlas visual language:

- warm off-white canvas with faint coordinate-grid lines;
- white analytical panels with restrained borders and shallow elevation;
- cobalt as the primary data color, with teal and amber as categorical accents;
- existing display and body fonts, tabular numerals, and readable 12–14px supporting text;
- no dark hero card, decorative numbering, glass effects, external fonts, or chart dependency.

Dark mode remains supported as a quiet night-atlas variant, but every panel keeps the same visual grammar instead of mixing a single oversized dark card with light cards.

## Information Architecture

### Header and indicators

The compact header contains `Research Landscape`, one sentence describing the paper-only scope, and the catalog snapshot date.

A four-cell indicator strip shows:

1. total papers, with strict and adjacent counts as the note;
2. publications in the latest 30-day catalog window;
3. change versus the preceding 30-day window;
4. latest represented publication date.

The indicators are aligned observations, not four decorative SaaS cards.

### Publication trend and category composition

The first analytical row contains:

- an eight-column publication trend with `6M`, `24M`, and `All` controls;
- a four-column Primary Category donut with an external legend.

`6M` and `24M` use monthly buckets. `All` uses annual buckets so the full history remains legible without horizontal scrolling. The chart has a fixed visual height and a text summary; it never stretches to match another panel.

Primary Category is mutually exclusive, so a donut is semantically valid. Each legend row links to the corresponding Papers section.

### Structural matrix and active directions

The second analytical row contains:

- a seven-column `Category × Mechanism` matrix;
- a five-column `Active Directions` panel.

The matrix has three category rows and four mechanism columns. Cell intensity represents paper count, while the visible number preserves exactness. Each cell links to the existing paper-only route combining a mechanism tag query with a category section hash. No new router or filter model is introduced.

Active Directions provides `Focus` and `Domain` tabs. It ranks the six most frequent values among papers in the latest 90-day catalog window, anchored to the latest valid publication date. Rows show recent counts, use horizontal bars for comparison, and link to the existing tag drill-down route.

Mechanism, Focus, and Domain remain explicitly multi-label. They are never rendered as pie or donut charts.

### Complete tag explorer

A full-width native `details` block sits below both analysis rows. It is closed by default and contains:

- Focus / Domain selection;
- a search input;
- all matching tag links with paper-only counts.

Because the explorer is outside the analytical grid, opening it cannot stretch an adjacent chart. Search filters the already-loaded catalog data; no backend or new payload is required.

## Removed Content

- Remove Annual Volume because the `All` trend already covers publication history.
- Remove Latest Releases because the Papers view already provides the latest-paper list and search.
- Remove the expandable long-tail taxonomy from the narrow composition card.
- Remove daily 365-bucket rendering from the default chart.

## Data and Rendering

Keep the existing `papers.json` fetch, `ALL_PAPERS`, lazy Stats render, loading/error states, date parsing, publication aggregation, release comparison, taxonomy distribution, safe DOM/SVG construction, and URL-backed tag drill-down.

Add only two small pure aggregations:

- Category × Mechanism counts;
- recent Top-6 Focus or Domain distribution.

The view layer is replaced: Stats CSS, Stats DOM, chart composition, donut, matrix, active directions, and all-tags explorer. No generated data schema changes are needed.

## Responsive Behavior

- Desktop: 12-column analytical grid with 8/4 then 7/5 panels.
- Tablet: indicators become two columns; each analytical panel spans the full width.
- Mobile: indicators remain a compact 2×2 grid; all analysis panels stack; chart buckets fit the viewport; no page-level horizontal scroll.
- The all-tags explorer becomes a single-column list on narrow screens.

All native controls keep visible focus states and at least 44px interactive targets. Charts retain textual summaries, and color is never the only carrier of exact values.

## Verification

Static and browser checks cover:

- required Scientific Atlas landmarks and absence of removed sections;
- deterministic matrix and recent-direction aggregation;
- native category/tag links and paper-only counts;
- range switching and no page-level horizontal overflow;
- desktop and 390px mobile composition;
- light/dark readability, keyboard focus, loading/error states, and console errors.

The repository policy prohibits running the test suite locally without an exact approved command. The implementation will leave focused tests and the full-suite command ready for the user to run.
