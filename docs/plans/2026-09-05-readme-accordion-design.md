# README Accordion Layout Design

## Goal

Remove the redundant list bullet from every paper and blog entry while preserving the complete expandable metadata.

## Design

- Render each entry as a standalone `<details>` block instead of a list item containing `<details>`.
- Keep the existing summary, badges, metadata, ordering, and expanded content unchanged.
- Apply the format to papers and blogs through the shared `_paper_to_md()` renderer.
- Add a focused rendering assertion and regenerate only `README.md`.

## Non-goals

- No table layout, year grouping, badge reordering, metadata changes, or website changes.
