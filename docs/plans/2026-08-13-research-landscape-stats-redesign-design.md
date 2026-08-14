# Personal-Site-Aligned Catalog Redesign

## Goal

Align the complete Awesome Loop Models interface with the editorial academic visual language of `huskydoge.github.io`, while preserving the catalog-specific search, filtering, tag drill-down, table, submission, and statistics behavior.

## Brand System

The personal site is the visual source of truth:

- Charter/Georgia-style editorial typography;
- white paper canvas, near-black ink, muted gray copy, and restrained blue links;
- thin rules, low radii, no decorative shadows, gradients, or oversized dark cards;
- a centered 1180px shell with a 52px translucent desktop header; mobile keeps its 58px shell and 44px tap targets;
- publication lists built from whitespace and separators rather than boxed cards.

System dark mode remains available as a quiet inverse using the same rules and hierarchy.

## Shared Shell

Use a small square `LM` brand mark plus `Awesome Loop Models`, text navigation for Papers and Stats, and restrained outline actions for Research Prompt, GitHub, and Submit. The active section is underlined, matching the personal site navigation.

On desktop, keep the masthead deliberately compact: 52px overall, a 28px brand mark, and 32px visual action buttons. Do not compress or restructure the catalog toolbar in this pass.

Search and primary catalog actions stay visible. Secondary sort, date, view, and tag controls remain behind the existing Filters disclosure.

## Papers

- Keep the current category tree, search, URL-backed tag routes, compact/comfortable density, and table view.
- Render paper entries like the personal site's research archive: transparent rows separated by fine rules, serif titles, muted metadata, small inline tags, and quiet text links.
- Restyle the desktop directory as a light editorial index instead of a card sidebar.
- Preserve the `Adjacent` scope warning and accessibility semantics.

## Stats Research Landscape

Use a natural-height white analytical grid:

1. compact title, scope, snapshot, and four aligned metrics;
2. publication trend with existing 90D/1Y/All behavior;
3. a Primary Category donut, because category is mutually exclusive;
4. ranked Loop Mechanism bars, because mechanism is multi-label;
5. Focus/Domain active-direction tabs showing Top 6 values;
6. an independent searchable full-tag explorer;
7. a compact latest-publications list.

Multi-label fields are never shown as pie charts. Opening the complete explorer cannot stretch a neighboring chart.

## Submit

Reuse the same tokens, header, typography, field borders, and button language on `submit.html`. Submission behavior and generated tag metadata remain unchanged.

## Implementation Boundaries

- Modify only `index.html`, `submit.html`, and the existing focused contracts in `tests/test_build.py`.
- Reuse `papers.json`, current URL state, existing safe DOM/SVG helpers, and current aggregation functions.
- Add no framework, chart library, font download, schema, or data pipeline.
- Keep hash navigation, keyboard support, visible focus, error/loading states, and mobile targets.

## Verification

Use static source checks and `git diff --check` locally. Browser-check desktop and mobile layouts on an isolated static server after the user approves that exact local command. Leave the focused unit-test command ready for the user because repository policy prohibits running test suites locally without explicit approval.
