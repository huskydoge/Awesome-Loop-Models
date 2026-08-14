# Tag Drill-down Design

## Goal

Make the mechanism, focus, and domain distributions in Stats actionable. A reader can open the matching Papers result set, keep searching within that tag, share the URL, and use browser Back/Forward without hidden filter state leaking between views.

## Chosen approach

Reuse the existing Papers renderer, `ACTIVE_TAG_FILTERS`, and text search. Do not create another page, result renderer, data file, or dependency.

Reuse the existing two-level filter disclosure as well. A tag route opens the outer Filters panel but leaves the full taxonomy list collapsed. The `Tags filter` toggle shows the active tag as a compact pill; selecting the toggle reveals the complete taxonomy only when the reader wants to change tags.

The route is a normal URL such as:

```text
?tag=mechanism%3A%3Aflat-loop#papers
```

The tag value uses the existing stable `group::label` key. Stats distribution rows for mechanism, focus, and domain become native links. Primary category remains non-clickable because it is not a tag.

## Interaction

- Following a Stats tag link switches to Papers and shows paper-only results for that tag.
- The outer Filters panel opens automatically, while the full tag taxonomy stays collapsed so paper content remains above the fold.
- The `Tags filter` toggle shows the active tag label and paper count in a compact pill.
- Selecting `Tags filter` expands the existing taxonomy; selecting the active tag again removes only the route tag and preserves the free-text query.
- Free text stays in the normal search input with no tag prefix and combines with active tags using AND.
- Existing advanced tag filters remain available and can be combined with the route tag.
- Paper-card tag clicks use the same drill-down route.

## State and navigation

URL state is authoritative for the route-owned drill-down tag. Parsing validates the decoded key against the paper-only tag lookup and fails closed for malformed or unknown values. `popstate` and `hashchange` restore or clear the route tag so Back/Forward never leaves an invisible filter active.

The current free-text query is stored as `q` with `history.replaceState`, avoiding one history entry per keystroke. Tag navigation uses normal link/history behavior.

## Data consistency

Stats distributions count `ALL_PAPERS`, while the general filter inventory also includes blogs. Drill-down lookup and results therefore use paper-only tag counts and exclude blogs, ensuring a Stats count such as `111` opens exactly 111 papers before free-text filtering.

## Accessibility and responsive behavior

Distribution links have native keyboard behavior, visible focus, a minimum 44px target, and an accessible label containing tag type, label, and count. After navigation, focus moves to the existing `Tags filter` disclosure so its active summary is immediately discoverable. The compact summary truncates safely on mobile, and the existing live result count announces changes.

## Error and empty states

Malformed or unknown tag URLs clear the drill-down state and render the normal Papers view rather than a mysterious empty result. A valid tag plus an unmatched text query uses the existing no-results surface, which includes both active filters.

## Verification

- Unit/static contracts for URL parsing, paper-only filtering, compact active-tag summary, collapsed taxonomy restoration, and Stats link semantics.
- Browser checks for Stats → Papers, active summary, optional taxonomy expansion, search-within-tag, clear, reload, Back/Forward, keyboard focus, mobile, and light/dark themes.
- Existing complete unit suite and `git diff --check`.
