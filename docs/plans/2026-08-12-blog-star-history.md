# Blog and Star History README Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the IFM loop-model blog and a live Star History chart to the generated README.

**Architecture:** Store blog metadata in the existing flat `blogs/` catalog and put the official Star History embed in the existing README footer template. Run the existing generator once so every checked-in artifact stays synchronized.

**Tech Stack:** YAML, Markdown, Python README generator

---

### Task 1: Add the blog source entry

**Files:**
- Create: `blogs/2026-07-31-towards-looped-models-done-right.yaml`

Record the exact title, seven authors, July 31 publication date, flat-loop architecture tags, concise evidence-calibrated summary, Notion blog URL, and X announcement comment.

### Task 2: Add the live Star History chart

**Files:**
- Modify: `scripts/README_FOOTER.md`

After Citation, add:

```markdown
## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=huskydoge/Awesome-Loop-Models&type=Date)](https://star-history.com/#huskydoge/Awesome-Loop-Models&Date)
```

### Task 3: Regenerate and inspect the change

**Files:**
- Modify: `README.md`
- Modify: `papers.json`
- Modify: `submission-meta.json`
- Modify: `TAGS.md`
- Modify if regenerated: `assets/repo-meta.js`
- Modify if regenerated: `.github/ISSUE_TEMPLATE/config.yml`

**Step 1: Regenerate checked-in artifacts**

Run: `python3 scripts/build.py`

Expected: exit 0 and output reporting 8 blogs.

**Step 2: Inspect focused output**

Run: `rg -n "Towards Looped Models Done Right|Star History" README.md papers.json submission-meta.json TAGS.md`

Expected: the blog appears in generated catalog outputs and README contains the chart section.

**Step 3: Check patch formatting**

Run: `git diff --check`

Expected: exit 0 with no output.

**Step 4: Commit only task files**

```bash
git add blogs/2026-07-31-towards-looped-models-done-right.yaml scripts/README_FOOTER.md README.md papers.json submission-meta.json TAGS.md assets/repo-meta.js .github/ISSUE_TEMPLATE/config.yml docs/plans/2026-08-12-blog-star-history.md
git commit -m "docs: add loop-model blog and star history"
```
