# Blog and Star History README Design

## Goal

- Add “Towards Looped Models Done Right — Part I: Topology, Input Injection, Recurrent-State Design” to the generated flat Blogs section.
- Show the repository's star growth over time near the bottom of README.

## Design

Add one `blogs/*.yaml` source entry. Use the Notion page as `links.blog` and the X announcement as a community comment. Keep the classification focused on flat-loop language-model architecture.

Add the official Star History live SVG embed to `scripts/README_FOOTER.md`, after Citation and before the maintainer footer. Regenerate `README.md` through the existing build script.

## Alternatives considered

- A checked-in static chart would avoid a third-party runtime dependency, but it would become stale.
- A GitHub Action-generated chart would keep data local, but adds workflow and maintenance code for no current need.

## Verification

Run the existing README build, inspect the generated Blog and Star History sections, and run `git diff --check`. Do not run the repository test suite on the local machine.
