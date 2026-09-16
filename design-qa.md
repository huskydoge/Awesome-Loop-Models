# Reading desk design QA

final result: prior layout QA passed; subsequent list, detail, thumbnail and filter changes await browser verification

Scope: local visual and interaction QA, not a deployment or an automated test-suite result.

## Follow-up: categories in Filters

- Replaced the left-rail category directory and phone Browse Sections entry with a native Category selector at the top of Filters. Options use the canonical titles and catalog totals, with All categories restoring the full resource set.
- Category filtering shares the list/table filter predicate and composes with search, tags, dates and watch toggles. It contributes to the active-filter count and empty-result explanation; selecting a category does not hide other available options.
- Global tag drilldowns reset the category just like other advanced filters. Existing section hashes, including Blogs and Stats category links, clear an incompatible category before scrolling; clearing a tag alone preserves the category.
- Inline-script/check-file syntax and whitespace checks passed. Category matching, safe option rendering and control placement checks are prepared but unrun. Browser interaction verification remains pending the existing preview approval.

## Follow-up: sidebar order and loop identity

- Moved the bulletin directly below Papers/Stats/Blogs and above Categories, with tighter spacing. Removed the brand subtitle and its unused styles.
- Replaced the LM monogram with a lightweight inline infinity-loop SVG. The text remains Awesome Loop Models in the original font; removing its 150px cap lets it use the resized sidebar naturally while still wrapping on narrow screens.
- Whitespace and regression-script syntax checks passed. Ordering, icon and subtitle assertions were prepared but not run; visual verification remains pending the existing preview approval.

## Follow-up: resizable navigation and title removal

- Added an accessible drag separator on the navigation's right border. It reuses the existing pointer-capture handling, supports arrow keys/Home/End, and resets to the current responsive default on double-click.
- Navigation clamps to 200–420px, with the upper limit reduced on narrower two-column layouts to reserve 360px for content. It never collapses; changing its width only reclamps the existing list/detail split without allowing collapse. The separator is absent from the stacked phone layout.
- Removed the visible Catalog watch heading and its redundant spacing while keeping the bulletin's accessible name, updates and countdown.
- JavaScript syntax and whitespace checks passed. Sidebar bounds, mobile no-op, ARIA values and no-collapse checks are prepared but were not run. Browser interaction verification still awaits the existing preview approval.

## Follow-up: bulletin readability

- Kept the existing Charter/Georgia font and theme tokens. The heading is 17px, update copy 14px, paper descriptions 13px, and schedule notes 12px with 1.6 line spacing; mobile no longer reduces the bulletin to 11px.
- Removed the nested update-card border, separated the Today label and count, increased article spacing, and placed the next-watch information in its own quiet surface. The 20px countdown can wrap rather than overflow on longer weekend intervals.
- Whitespace and regression-script syntax checks passed. Typography assertions are prepared but unrun; browser appearance remains unverified pending local-preview approval.

## Follow-up: always-visible catalog bulletin

- Catalog watch is now a labeled, non-collapsible section. Today's report, when available, is also non-collapsible; the existing countdown and stale-report hiding behavior remain. On phones the bulletin spans the sidebar's full width.
- Removed the About the classification disclosure and its unused page styles/rendering code. Canonical classification metadata and paper-level status labels are unchanged.
- Syntax and whitespace checks passed. Updated the prepared markup checks for the bulletin and removed disclosure; tests and browser verification remain unrun pending the existing approvals.

## Follow-up: filter heading and removable active tags

- The Filters header explicitly uses left alignment instead of inheriting the legacy toolbar's centered text.
- Each active filter appears as an individually removable pill with a top-right ×. These native buttons sit outside the disclosure button, so removing a tag does not toggle the tag panel. Keyboard focus moves to a remaining pill or the disclosure after removal.
- Removal reuses the existing toggle and URL-clearing path, preserving the query and other filters. Explicitly removing a URL tag also clears a matching filter selected before entering that route.
- JavaScript/inline-script syntax and whitespace checks passed. Active-chip rendering, escaping, counts, removal and non-nested markup checks were added to the existing single-file regression check but were not run. Browser verification still awaits the existing preview approval.

## Follow-up: explicit detail closing

- A labeled × button is visible at the top right of both desktop and narrow-screen details. Desktop closing uses the same collapse path as dragging, restoring full cards; mobile closes its native dialog.
- Clicking the currently displayed paper again closes its details. Selecting another paper switches content; selecting a title after closing reopens the details. Source links, tag controls and comment disclosures remain excluded from this toggle.
- Paper buttons expose `aria-expanded` alongside the retained selection state; native dialog closing also refreshes this state.
- Syntax/whitespace checks passed. The prepared single-file regression check now covers same-paper close/reopen, different-paper switching and desktop/mobile close behavior; it was not run. Browser interaction verification still awaits the existing preview approval.

## Follow-up: alphaXiv thumbnails

- Full cards show a 144px-wide paper preview on the left. Split-mode rows, mobile rows and blog entries keep the text-only layout.
- Image URLs use validated arXiv identifiers; explicit source versions are retained, otherwise the implementation tries v1. This best-effort external resource is not a guaranteed alphaXiv API, and coverage is not assumed for every paper.
- Native lazy loading and asynchronous decoding avoid eagerly fetching the full catalog. Requests omit the referrer. On image failure, the preview link is removed and the text fills the available width without an empty placeholder.
- The sample endpoint `https://thumbnails.assets.alphaxiv.org/2301.13196v1.png` returned HTTP 200 with `image/png` during this change. No bulk image downloads, PDF rendering, catalog metadata edits or dependency additions were performed.
- JavaScript/inline-script syntax and whitespace checks passed. Identifier/version validation and fallback-markup assertions were added to the existing single-file check but not executed. Browser layout, lazy loading and error fallback still await the existing localhost-preview approval.

## Follow-up: link-first list and resizable detail column

- Split-mode rows reuse the catalog's complete source/discussion links; summaries remain in the detail pane. Dragging until the right pane reaches 220px collapses it and expands the list to fill the space.
- List-only mode shows the reference's full card hierarchy: title and venue, authors and date, citations/stars, four tags with an accessible +N disclosure, full summary and source links. Existing scope/status labels are preserved. Show details or selecting a title restores the split; clicking or selecting body text does not.
- The desktop separator uses native pointer capture and keyboard Left/Right, Home/End controls. End collapses details; double-click resets the split. The list retains a 360px minimum. Table, Stats and narrow layouts hide the separator without forgetting the explicit collapsed choice; window resizing alone never triggers collapse.
- Clicking a source link or expanding community comments does not select the card or open the narrow-screen detail modal.
- JavaScript syntax and whitespace checks passed. Split/collapse-boundary and dual-card-markup regression checks were added but not run, pending the existing test-execution approval.
- Browser interaction verification is pending: browser tooling blocks the current file URL and the previous localhost preview server is no longer running. Permission to restart the localhost-only preview was requested.

## Target and intentional differences

- Selected direction: alphaXiv-inspired three-column reading desk, with the original Charter / Georgia font stack and System / Light / Dark controls.
- Compared the revised light-theme reference and the running page together at 1487 × 1060. The implementation retains the three-column hierarchy, fine dividers, green selection and restrained light/dark surfaces.
- Real catalog records replace illustrative paper text. Categories retain their canonical names; full classification, source links, scope boundaries and community comments live in the detail pane. There is no fabricated PDF preview or abstract.
- Existing identity and source-link icons are reused. No new UI framework, font download or illustration dependency was introduced.

## Previously verified in the browser (before the follow-up above)

- Desktop: 1280 × 720, 1440 × 900, 1487 × 1060; tablet: 1024 × 768; phones: 390 × 844 and 320 × 740.
- Three-column desktop layout and two-column tablet layout; narrow screens open details in a native modal. No horizontal page overflow at 320, 390 or 1024 pixels.
- The computed body font remains `Charter, Georgia, "Times New Roman", "Songti SC", STSong, serif`.
- Light and Dark controls change the entire surface, including filters and Stats. Dark selection survives reload. System remains an explicit third choice.
- Search for DeepLoop returns one result with the correct detail and primary source. An unmatched search shows zero results and an empty detail state. Clearing via the keyboard restores 219 resources.
- Paper and blog selection updates the detail pane from the catalog. Blog details retain the summary, all taxonomy groups, original source and community comments.
- Table mode renders 219 rows and preserves expandable details. Selecting Blogs from Table returns to List; its heading is positioned below the sticky toolbar (156px vs 142px toolbar bottom in the checked viewport).
- Code-only filter returns 93 resources. Combining flat-loop and objective-loss leaves both controls pressed and returns 25 resources. Closing filters returns keyboard focus to the Filters button; new results start at the top of the list.
- Stats renders the catalog's 211 papers and existing charts, with the detail pane closed.
- Mobile detail uses the native modal focus trap. Escape closes it and restores focus to the selected paper button. Resizing an open tablet modal to desktop restores a nonmodal detail column.
- Phone navigation keeps Research prompt, GitHub, Submit, classification and catalog-watch disclosures reachable. Theme buttons have 44px height.
- No browser console errors were reported during the inspected flow.

## Corrections made during QA

- Prevented sidebar tabs from shrinking to zero height.
- Restored mobile secondary actions and watch/classification disclosures.
- Adjusted category scrolling for the sticky toolbar and returned category navigation from Table to List.
- Restored filter headings, focus return, date-field labels and top-of-results positioning.

## Follow-up: independent Blogs view

- Blogs is now a third top-level tab with its own heading, selected state and `#blogs` route; legacy `#section-blogs` links open that view without scrolling the paper catalog.
- Papers and Blogs reuse the list/table/detail renderer but source records exclusively from their own collection. Empty sections from the other collection stay hidden, and switching tabs refreshes results and selected details.
- Category, Accepted only and Newly Arrived remain saved for Papers but are hidden and ignored in Blogs, including filter counts and empty-state labels. Search, dates, tags, code and comment filters remain shared. Keyboard navigation covers all three tabs, and the shared panel's accessible name tracks its active view.
- JavaScript and inline-script syntax checks plus `git diff --check` passed. Updated the existing single-file scope checks and tab-routing regressions; neither automated check was executed under the user's execution policy.
- Attempting the supplied `http://127.0.0.1:8766/` preview returned `ERR_CONNECTION_REFUSED`. This follow-up's visual and browser-history interaction checks remain unverified; no server was started. Existing preview/test approval reminders remain the same human actions, with no duplicate tasks created.

## Follow-up: stable cards and separate discussion

- Supersedes the earlier compact/full-card mode: card content no longer depends on whether details are open. Thumbnails, authors/date, venue, metrics, tags, complete summary, scope notes and links use one markup path. Removed the duplicate compact footer.
- The paper-list container width controls layout. Wide cards use a 144px preview beside text; at 640px or less the 80px preview floats beside a wrapping header. Authors and summaries remain untruncated; badges and link rows wrap. The container rules follow viewport overrides so dragging a narrow column on a wide screen uses the same layout.
- Sources and Discussion are separate, named sections within the existing detail column. Sources excludes the community-comments disclosure; Discussion lists those links directly, preserving their labels, with an explicit empty state. No new discussion content is fetched or fabricated. The optional fourth-column interpretation remains a user choice, not implemented by default.
- JavaScript/inline-script syntax checks and `git diff --check` passed. The existing regression check now covers equal card markup across open/closed state, non-duplicated source/discussion links, expanded comments and empty discussion. Checks were authored but not executed under the user's command policy.
- Browser verification is still pending the existing localhost-preview approval; the latest user page is a file URL, and the last HTTP preview attempt was refused. No server, test suite, publish or deployment was started.

## Follow-up: centered popup and single Code source

- Removed the duplicate Code shortcut beside Open paper/Open blog; the original code link remains in Sources. No catalog links or metadata were removed.
- The narrow-screen native detail dialog is centered using inset zero and automatic margins, with a bounded content height, internal scrolling, border and rounded corners. Tablet popups leave at least 16px horizontal and 24px vertical margins; phone popups leave 12px. Wide-screen draggable columns remain unchanged.
- JavaScript syntax and whitespace checks passed. Added regression assertions for a single Code source and centered-popup rules; the automated checks were not executed under the user's execution policy.
- The current file preview tab was found, but browser inspection was blocked by the file-URL policy. Actual popup layout remains unverified; the existing localhost-preview authorization is still the same outstanding action. No duplicate audit task, server or deployment was created.

## Follow-up: fixed detail header and body-only scrolling

- The detail renderer now separates title/authors/venue/date/Open paper into a fixed header, with Summary, Classification, Sources and Discussion in a keyboard-focusable scrolling body. The outer dialog clips overflow instead of drawing a full-height scrollbar; its close button stays outside both content regions.
- Desktop detail columns and centered narrow-screen popups share this structure. Popups use a definite viewport-bounded height so the body reliably receives the remaining space. Initial, unavailable and empty-result states use the same wrappers. Replacing the resource replaces the body node and naturally resets its scroll position.
- An unusually long header is capped at 65% with its own overflow fallback, preserving access to the remaining body on short screens without truncating the title/authors.
- JavaScript/inline-script syntax and whitespace checks passed. The existing single-file regression check now asserts the header/body boundary, Summary-first content, keyboard access and scroll ownership; it was not executed under the user's command policy. Browser verification remains blocked by the current file preview policy and the existing localhost-preview authorization; no new audit action or deployment was introduced.

## Follow-up: keep the thumbnail in details

- Detail headers now include the same validated alphaXiv thumbnail used by the corresponding list card, beside the title and outside the scrolling Summary/body. Preview width adapts from 64px to 128px; clicking opens the primary paper source. Existing typography and header/body scroll behavior remain unchanged.
- The selected preview loads eagerly and asynchronously without a referrer. Reuses the list's image-failure removal so missing images do not leave an empty frame. Blogs and records without supported arXiv identifiers do not fabricate a preview.
- JavaScript syntax and whitespace checks passed. Added unrun assertions for matching list/detail URLs, fixed-header placement, fallback markup and unsupported records. Browser verification remains pending the existing localhost-preview authorization; no new human action or dependency was introduced.

## Follow-up: metrics below the detail thumbnail

- Citation and GitHub-star badges now sit vertically beneath the detail thumbnail in the fixed header, using the existing metric formatter. Removed their duplicate from Sources; list cards are unchanged.
- Metrics remain in the header when a preview is unavailable or fails. Missing metrics are omitted, zero values remain visible, and a failed preview with no metrics leaves no empty visual column.
- JavaScript syntax and whitespace checks passed. The prepared single-file check now uses the real metric renderer and covers header placement, no duplication, missing thumbnails, zero/missing metrics and empty-column styling. Automated/browser verification remains unrun under the existing execution and preview constraints.

## Follow-up: metrics below list thumbnails too

- List cards now group citation and GitHub-star badges vertically beneath their thumbnail, matching details. Tags and status badges remain beside the paper text; metrics appear only once.
- The whole thumbnail/metrics group reflows together in narrow lists. Missing previews retain the metrics, zero counts remain visible, and records with neither preview nor metrics leave no empty column.
- Added placement, no-duplication and fallback assertions to the existing single-file check. Automated and browser verification remain pending the existing execution/preview approval; no new dependency or human action was introduced.

## Verification limits

- JavaScript syntax and `git diff --check` passed. A dependency-free check is available at `tests/reading-desk-check.cjs`; source assertions in `tests/test_build.py` were updated for the new layout.
- Neither automated check nor the Python test suite was run. Execution of `node tests/reading-desk-check.cjs` was denied pending explicit user approval under the user's test-execution policy.
- Live OS-theme change events and network-failure simulation were not exercised. The System resolution and unavailable-storage paths are covered by the prepared, unrun check.
- This is a local preview only. No push, PR, deployment or merge was performed for this redesign.
