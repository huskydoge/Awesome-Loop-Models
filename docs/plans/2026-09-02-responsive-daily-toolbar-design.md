# Responsive Daily Toolbar Design

## Problem

The toolbar treats the small Today disclosure and the large refresh card as equal tablet columns, while wide screens absolutely position the refresh card. On phones, Today appears after search and filters and the refresh card consumes too much vertical space.

## Approved design

- Group the existing Today disclosure and refresh countdown into one status region.
- Keep that region in normal document flow at every width.
- Use a balanced two-column row on desktop and tablet; switch to one column on phones.
- Keep Today before search and filters on phones, and reduce the countdown to one readable line below 480px.
- Preserve native `<details>/<summary>`, give its summary a 44px touch target, and stop announcing the ticking countdown every second.

## Scope

Change only `index.html` and its narrow static contract checks. Add no dependency, backend, database, or new JavaScript state.

## Verification

Inspect the live local page at 1440, 1024, 768, and 390 CSS pixels, both collapsed and expanded. Confirm no horizontal overflow, sensible source order, a 44px Today target, and no console errors.
