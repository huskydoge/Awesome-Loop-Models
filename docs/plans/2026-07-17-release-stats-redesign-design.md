# Release Stats Redesign

## Goal

Turn Stats into a memorable, useful top-level mode of the site. The experience should answer when the papers represented in the catalog were released and whether the release cadence is accelerating, without exposing repository-maintenance intake data.

## Product Position

`Papers` and `Stats` are global site modes, not presentation options inside the paper browser. A persistent site masthead will contain:

- the compact Awesome Loop Models brand;
- a prominent `Papers / Stats` mode switch;
- GitHub and Submit actions.

The mode switch sits at the top of the site and remains visible in both modes.

### Papers mode

Papers preserves the existing catalog experience: daily report, refresh countdown, search, filters, taxonomy sidebar, category cards, and table view.

### Stats mode

Stats removes all paper-browsing chrome:

- no daily report or repository refresh countdown;
- no search or filter controls;
- no taxonomy sidebar;
- no category/table view controls;
- no catalog-intake metrics.

The main canvas expands to a full-width editorial analytics page. The shared masthead and footer remain, so switching modes feels like moving between two parts of one product rather than navigating to a detached microsite.

## Statistical Semantics

Every Stats calculation uses `papers[].published_date`. `added_date` remains valid catalog-maintenance metadata but is not shown or used in Stats.

The page describes the release distribution of papers represented in this curated catalog. Copy must not claim to measure every paper in the broader research field.

Time-relative metrics anchor to the latest valid publication date in the dataset, not the viewer's wall-clock date. This keeps a static snapshot internally consistent when the daily collection process has not run recently.

## Information Architecture

### Release intelligence hero

The Stats page opens with an editorial hero:

- eyebrow: `Release intelligence`;
- title: `The rhythm of loop-model research`;
- short scope sentence that explains the catalog-backed nature of the data;
- four integrated metrics separated by rules rather than floating dashboard cards:
  - total papers;
  - releases in the latest 30 recorded days;
  - latest paper release date;
  - peak release month and count.

### Release Pulse

The primary visualization answers the user's daily-release question.

- `90D`: daily paper-release bars over the latest 90 recorded days;
- `1Y`: daily paper-release bars over the latest 365 recorded days and the default view;
- `ALL`: monthly release bars across the complete catalog history.

The overlaid trend line is a trailing average:

- 14-day average for `90D`;
- 30-day average for `1Y`;
- 6-month average for `ALL`.

The chart explains both encodings in text and exposes the chosen range through an accessible segmented control. Zero-release periods are preserved so cadence remains honest.

### Annual volume

A compact horizontal bar ranking shows the number of catalog papers released in each year. This provides a legible long-term trend without compressing thousands of daily buckets into one chart.

### Latest releases

A practical list presents the newest papers by `published_date`, including date, title, venue, and the best available paper link. This converts the analytical view back into reader action.

### Long arc

A restrained cumulative line summarizes how the current catalog is distributed across publication time. It is secondary to Release Pulse and should not dominate the page.

## Visual Direction

The page will use a research-observatory / editorial-data aesthetic rather than a generic SaaS dashboard:

- large STIX-based editorial typography paired with the site's existing sans-serif body stack;
- generous negative space and strong horizontal rules;
- cool blue “data ink,” deep green or warm vermilion for trend emphasis, and neutral grid lines;
- small uppercase labels and tabular numerals;
- an understated dot/grid atmosphere inside the Stats canvas;
- no glassmorphism, purple gradients, decorative animation, or multicolored KPI-card grid.

The visual signature should be the relationship between a strong editorial headline and one generous, information-dense timeline—not visual effects.

## Responsive Behavior

- Desktop uses the full main width with no sidebar in Stats mode.
- The mode switch remains prominent at tablet and mobile sizes.
- KPI metrics collapse from four columns to two and then one/two compact rows.
- Release Pulse keeps readable geometry inside a local horizontal-scroll container.
- Annual volume and Latest releases stack vertically on narrow screens.
- Stats mode must not inherit the catalog header's large vertical footprint.

## Interaction and URL State

- `#papers` and `#stats` remain shareable URLs.
- Switching Stats range does not alter the top-level hash.
- Keyboard semantics remain standard ARIA tabs for the global mode switch.
- Range buttons use `aria-pressed` and are keyboard-operable native buttons.
- Returning to Papers restores the catalog and category-hash behavior already implemented.

## Loading, Errors, and Empty Data

- A direct `#stats` URL shows the Stats shell immediately, then a local loading state until `papers.json` resolves.
- Fetch failure produces a Stats-specific error state.
- Invalid publication dates are skipped defensively; the canonical build remains the main validation boundary.
- An empty catalog keeps the hero but replaces visualizations and latest releases with explanatory empty states.

## Accessibility

- The global mode switch keeps `tablist`, `tab`, and `tabpanel` semantics.
- Every SVG includes a meaningful title and description.
- Visible chart summaries communicate recent non-zero periods without hover.
- Latest releases are real links with descriptive titles.
- Text and data colors must meet WCAG AA contrast.
- The design uses no motion, so reduced-motion behavior is satisfied by construction.

## Scope Boundaries

This redesign does not introduce a framework, chart library, external font, analytics backend, or additional JSON payload. It does not alter paper taxonomy, search behavior, or the canonical YAML schema. Repository intake history is removed from Stats but retained in source data for maintenance workflows.

## Verification

Source and behavior regressions should cover:

- absence of `added_date` from Stats aggregation/rendering;
- daily and monthly `published_date` aggregation;
- range windows and trailing averages;
- KPI calculations and latest-release ordering;
- global mode chrome visibility;
- range-button behavior;
- URL/hash and category navigation preservation;
- empty/error states;
- responsive and accessible markup contracts.

The authorized canonical build may be rerun when generated data changes. Full unittest and browser interaction validation remain subject to the repository's shared-machine execution policy.
