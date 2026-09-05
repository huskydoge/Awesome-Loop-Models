# README Accordion Layout Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the README paper-list bullets with standalone expandable entries.

**Architecture:** Keep the existing shared README renderer and change only its outer wrapper. The YAML data model and all entry content remain unchanged.

**Tech Stack:** Python, GitHub-flavored Markdown, `unittest`

---

### Task 1: Render standalone details entries

**Files:**
- Modify: `scripts/build.py:1142`
- Test: `tests/test_build.py`
- Regenerate: `README.md`

**Step 1:** Extend the existing README rendering test to require output starting with `<details>` and reject `- <details>`.

**Step 2:** Change `_paper_to_md()` so `lines` starts with `"<details>"`.

**Step 3:** Regenerate only `README.md` through the canonical loader and `build_readme()` function.

**Step 4:** Inspect `git diff --check` and confirm no paper metadata or unrelated generated artifact changed.

**Step 5:** Let CI or the user run the focused test required by the login-node policy:

```bash
/opt/anaconda3/bin/python3.12 -m unittest tests.test_build.ReadmeRenderingTests
```
