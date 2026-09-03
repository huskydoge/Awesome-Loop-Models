# Responsive Daily Toolbar Design

## Problem

The toolbar treats the small Today disclosure and the refresh countdown as equal-width cards. The collapsed Today label therefore sits inside a long empty bar, and opening its report stretches the countdown to the report's height.

## Approved design

- Group the existing Today disclosure and refresh countdown into one status region.
- Keep that region in normal document flow at every width.
- Keep collapsed Today at its intrinsic content width; expand only the open report, to about 620px on larger screens and the available width on phones.
- Keep the countdown compact and top-aligned. Add a small CSS clock whose second hand rotates beside the existing exact digital countdown.
- Let the two compact controls wrap naturally when space is tight, and keep Today before search and filters on phones.
- Preserve native `<details>/<summary>`, give its summary a 44px touch target, and stop announcing the ticking countdown every second.
- Treat the clock as decoration and stop its animation under `prefers-reduced-motion`; the digital countdown remains the accessible source of truth.

## Scope

Change only `index.html` and its narrow static contract checks. Add no dependency, backend, database, or new JavaScript state; CSS owns the clock animation.

## Verification

Inspect the live local page at 1440, 1024, 768, 390, and 320 CSS pixels, both collapsed and expanded. Confirm the collapsed controls stay compact, the countdown remains top-aligned while it fits beside the open report and wraps below it on narrow screens, no horizontal overflow occurs, the Today target remains 44px tall, reduced motion stops the clock hand, and no console errors appear.
