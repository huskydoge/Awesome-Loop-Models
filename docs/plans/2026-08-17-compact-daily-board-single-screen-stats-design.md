# Compact Daily Board and Single-Screen Stats

## Goal

Prevent the Papers daily board from covering the collection directory and turn Stats into a true desktop dashboard without an inner scrolling pane.

## Daily Board

Replace the absolute-positioned briefing card with a compact in-flow status strip below the masthead. The strip exposes only two facts:

- papers added on the catalog build date;
- whether any of those papers has the maintainer-only `must_read: true` flag.

The date source is `data.meta.generated_local_date`; the paper source is `ALL_PAPERS`; membership uses `added_date`, not publication date or the latest briefing date. The strip therefore remains truthful when the newest briefing is older than the current build. Remove the paper-title list, Details disclosure, and briefing-detail scroll area.

## Stats Dashboard

On desktop, remove the `main` scrolling pane and fit the primary analysis into one viewport below the masthead:

1. a compact title/snapshot row;
2. a shallow four-metric rail;
3. a two-row analytical grid containing Release trend, Category mix, Loop mechanisms, and Top 6 active directions.

Reuse the existing aggregation and safe SVG/DOM renderers. Release trend remains the primary 7-column chart; Category mix occupies the remaining 5 columns. Mechanisms and active directions share the second row. Remove the full tag explorer and latest-publications feed from Stats because they duplicate the Papers filter surface and the latest-release KPI. Chart labels remain clickable links to the existing URL-backed Papers tag route.

The release SVG must size to its container instead of enforcing a 760px minimum, and Stats must not create horizontal or vertical inner scrollbars.

## Responsive Behavior

- At desktop widths and ordinary laptop heights, Stats uses the two-row single-screen grid with no inner scrolling.
- At narrower widths or short viewports, the document may scroll naturally; cards stack without introducing a nested scroll region.
- Mobile preserves readable labels and tap targets. Zero-scroll is a desktop dashboard goal, not a reason to shrink mobile content below usable sizes.

## Accessibility and Failure States

Keep the existing Papers/Stats tab semantics, keyboard behavior, SVG titles/descriptions, loading state, empty state, and catalog-load error message. The compact daily strip is plain status content and does not add a disclosure control.

## Implementation Boundaries

- Modify only `index.html` and focused contracts in `tests/test_build.py`.
- Add no framework, chart library, schema, or data pipeline.
- Reuse `ALL_PAPERS`, `REPO_TODAY`, `must_read`, existing tag links, and existing aggregation helpers.
- Delete obsolete daily-briefing and Stats-scroll presentation code instead of adding another layout layer.

## Verification

Use `git diff --check` and narrow source-contract inspection locally. Repository policy requires explicit approval before running unit tests, the build, or a long-running local static server; retain exact commands for user approval and browser verification.
