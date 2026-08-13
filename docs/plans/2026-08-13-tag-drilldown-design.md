# Tag Drill-down Design

## Goal

Make the mechanism, focus, and domain distributions in Stats actionable. A reader can open the matching Papers result set, keep searching within that tag, share the URL, and use browser Back/Forward without hidden filter state leaking between views.

## Chosen approach

Reuse the existing Papers renderer, `ACTIVE_TAG_FILTERS`, and text search. Do not create another page, result renderer, data file, or dependency.

The route is a normal URL such as:

```text
?tag=mechanism%3A%3Aflat-loop#papers
```

The tag value uses the existing stable `group::label` key. Stats distribution rows for mechanism, focus, and domain become native links. Primary category remains non-clickable because it is not a tag.

## Interaction

- Following a Stats tag link switches to Papers and shows paper-only results for that tag.
- The search control displays a non-editable prefix token such as `Loop mechanism: flat-loop ×`.
- Free text remains in the existing input and combines with the locked tag using AND.
- Clearing the token removes only the tag and preserves the free-text query.
- Existing advanced tag filters remain available; the route tag cannot be silently removed while its URL is active.
- Paper-card tag clicks use the same drill-down route.

## State and navigation

URL state is authoritative for the locked drill-down tag. Parsing validates the decoded key against the paper-only tag lookup and fails closed for malformed or unknown values. `popstate` and `hashchange` restore or clear the locked tag so Back/Forward never leaves an invisible filter active.

The current free-text query is stored as `q` with `history.replaceState`, avoiding one history entry per keystroke. Tag navigation uses normal link/history behavior.

## Data consistency

Stats distributions count `ALL_PAPERS`, while the general filter inventory also includes blogs. Drill-down lookup and results therefore use paper-only tag counts and exclude blogs, ensuring a Stats count such as `111` opens exactly 111 papers before free-text filtering.

## Accessibility and responsive behavior

Distribution links have native keyboard behavior, visible focus, a minimum 44px target, and an accessible label containing tag type, label, and count. The prefix clear control has a specific accessible name. The existing live result count announces changes. The prefix wraps or truncates safely on mobile without shrinking the text input below a usable width.

## Error and empty states

Malformed or unknown tag URLs clear the drill-down state and render the normal Papers view rather than a mysterious empty result. A valid tag plus an unmatched text query uses the existing no-results surface, which includes both active filters.

## Verification

- Unit/static contracts for URL parsing, paper-only filtering, prefix rendering, and Stats link semantics.
- Browser checks for Stats → Papers, search-within-tag, clear, reload, Back/Forward, keyboard focus, mobile, and light/dark themes.
- Existing complete unit suite and `git diff --check`.
