# Catalog Intelligence Dashboard and Taxonomy Cleanup

## Goal

Turn the existing editorial Stats page into a compact catalog dashboard while cleaning demonstrably inconsistent paper metadata. The dashboard should let a reader answer, above the fold, how large the catalog is, whether releases are accelerating, when papers were published, and how the catalog is composed.

## Scope

- Keep the static, zero-dependency site and the existing `papers.json` payload.
- Keep `#papers` / `#stats`, ARIA tab behavior, lazy rendering, safe DOM construction, and the existing loading, empty, and fetch-error states.
- Use `published_date` for release statistics. Do not introduce `added_date` into Stats.
- Edit canonical paper YAML only when taxonomy evidence supports the change, then regenerate checked-in artifacts through `scripts/build.py`.
- Preserve unrelated untracked files and stage only exact task files.

## Dashboard Information Architecture

### Compact header and metric rail

Replace the oversized editorial hero and duplicated latest-release signal with:

- `Catalog Intelligence` title;
- one-sentence catalog scope;
- catalog snapshot timestamp from existing repository metadata when available;
- four metrics: total papers, releases in the latest 30 recorded days, change versus the prior 30 days, and latest publication date.

### Primary grid

Use a 12-column desktop grid:

- Release Pulse spans eight columns and remains the dominant visualization.
- Catalog Composition spans four columns and contains compact horizontal distributions for primary category and Loop Mechanism.

Release Pulse keeps `90D`, `1Y`, and `ALL`. Bars and their trailing average share one y-scale because both represent papers per period. Zero-release periods remain visible.

Loop Mechanism is multi-label, so its panel explicitly states that counts can exceed the paper total and percentages can exceed 100% in aggregate.

### Secondary grid

- Annual Volume occupies four columns and clearly marks the latest year as partial when the catalog does not contain a complete calendar year.
- Latest Releases occupies eight columns and becomes a compact list containing date, title, category, and mechanism. Remove abstracts, repeated calls to action, and dossier-style cards.

### Progressive taxonomy detail

Place Focus and Domain distributions in a native collapsed `details` section below the main dashboard. This keeps long-tail metadata available without turning the primary view into a tag wall.

Remove the Long Arc chart because the `ALL` Release Pulse already communicates full-history publication volume.

## Visual Direction

Use one shared visual grammar with two deliberately tuned themes selected through `prefers-color-scheme`:

- light: warm neutral canvas, dark ink, cobalt data color, restrained green comparison accent;
- dark: deep blue-black canvas, cool neutral panels, bright blue data color, clear green comparison accent;
- tabular numerals, compact labels, strong alignment, restrained borders, and shallow elevation;
- no gradient spectacle, glassmorphism, decorative animation, external fonts, or theme toggle.

The page should feel like a research instrument: dense enough to scan, calm enough to read, and visually distinct from a generic SaaS card grid.

## Responsive Behavior

- Desktop: 12-column dashboard grid.
- Tablet: KPI rail becomes two columns; Release Pulse and composition stack.
- Mobile: KPI, Pulse, composition, latest releases, annual volume, then taxonomy detail.
- Keep local horizontal scrolling only where the existing SVG needs it; do not make the page itself scroll sideways.
- Preserve native buttons, visible focus indicators, and useful text summaries outside SVG hover states.

## Data Flow

`papers/*.yaml` remains the source of truth. `scripts/build.py` produces `papers.json`, which the existing page fetches into `ALL_PAPERS`. Dashboard helpers derive:

- publication series and rolling comparisons from `published_date`;
- primary category counts from `category`;
- mechanism counts from `mechanism_tags`;
- secondary Focus and Domain counts from `focus_tags` and `domain_tags`;
- latest rows from the existing stable date/title ordering.

Reuse current date parsing, series builders, safe URL handling, SVG helpers, and DOM construction. Add no framework, chart library, backend, or second data payload.

## Taxonomy Cleanup Policy

Use three evidence levels:

1. Mechanical normalization: fix case-only or exact vocabulary collisions without changing meaning.
2. Evidence-backed semantic correction: inspect the primary paper source before changing category, mechanism, Focus, or Domain fields.
3. No frequency-only rewrites: a common tag is not wrong merely because it is broad, and a multi-mechanism paper is not reduced to one mechanism without paper evidence.

Update the matching audit ledger for semantic changes when the repository workflow requires it. Regenerate `README.md`, `TAGS.md`, `papers.json`, and `submission-meta.json` only after canonical YAML changes are final.

## Loading, Errors, and Empty Data

- Keep the Stats shell visible while `papers.json` loads.
- Keep a Stats-specific fetch failure message.
- Ignore malformed dates defensively in browser aggregation; canonical build validation remains authoritative.
- Show compact empty states per panel so one missing dimension does not blank the entire dashboard.

## Verification

Lightweight local checks:

- inspect exact diffs and generated-file scope;
- `git diff --check`;
- static source assertions for required dashboard landmarks and removed obsolete sections;
- browser verification for desktop/mobile, light/dark, direct `#stats`, range switching, focus order, and overflow.

The shared-cluster policy prohibits running builds and test suites without explicit confirmation. Provide these commands for the user or an approved Slurm run:

```bash
python3 scripts/build.py
python3 scripts/audit_catalog.py --format human
python3 scripts/check_asset_budgets.py
python3 -m unittest discover -s tests -t . -p 'test_*.py'
```

## Scope Boundaries

Do not add a theme toggle, tooltip framework, chart library, separate dashboard page, backend analytics, taxonomy schema, or speculative tag-quality score. Add any of those only after the static dashboard demonstrates a concrete need.
