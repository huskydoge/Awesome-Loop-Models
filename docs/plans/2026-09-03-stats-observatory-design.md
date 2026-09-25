# Stats Observatory Visual Refresh

## Goal

Make the Stats page more memorable without turning the editorial research catalog into a generic dashboard.

## Visual Direction

Keep the existing white-paper canvas, Charter/Georgia typography, restrained blue links, compact KPI rail, and two-row desktop layout. Make `Release trend` the single visual focal point: a deep ink-blue observatory window with a faint technical grid, cool-blue bars, a sage trailing-average line, and quiet corner registration marks.

The remaining category, mechanism, and direction views stay light and editorial so the dark chart reads as deliberate emphasis rather than a site-wide theme change.

## Motion

When the chart first appears or its range changes, bars rise once and the average line draws once. Motion remains brief, communicates the data encoding, and is disabled under `prefers-reduced-motion: reduce`. There is no looping glow, parallax, cursor effect, or decorative animation.

## Architecture and Data

- Reuse the current native SVG renderer and CSS variables in `index.html`.
- Add no framework, chart library, external font, schema, or data pipeline.
- Preserve all calculations based on `published_date`, including the latest-data anchor and the 90D/1Y/ALL trailing-average windows.
- Preserve the existing URL hash, ARIA tabs, native range buttons, loading/error states, category links, and taxonomy drill-down links.

## Responsive and Accessible Behavior

- Keep the 7/5 and 5/7 desktop grid and natural stacked mobile layout.
- Preserve 44px mobile targets and avoid nested scrolling.
- Retain SVG title and description content.
- Keep the chart readable in both system themes; the observatory window remains dark in light mode and uses adjusted contrast in dark mode.
- Ensure the visual line color matches its accessible description.

## Scope

Modify only `index.html` and the focused Stats source contracts in `tests/test_build.py`. Do not restore removed feeds or explorers, and do not alter catalog data or unrelated site surfaces.

## Verification

Run lightweight source checks and `git diff --check`. Leave the exact focused unit-test and local browser-preview commands for explicit approval under the repository execution policy.
