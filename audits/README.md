# Paper catalog audits

`scripts/audit_catalog.py` is a read-only structural audit of the canonical
`papers/*.yaml` files. It reads the raw YAML rather than the normalized browser
catalog, skips `_template*`, never edits paper records, and does not use the
network.

Findings have two severities:

- `error` means the catalog has an invalid structure, identity, URL, or
  controlled tag. Any error makes the command exit with status 1.
- `warning` marks a year/date discrepancy, cross-axis tag collision, or prose
  soft-limit issue that needs human judgment. A warning-only run exits with
  status 0.

The auditor deliberately has no auto-fix mode. In particular, it does not
decide whether a paper is in scope, verify claims in `desc`, or infer semantic
categories and tags. Those decisions require checking the primary paper source
and recording the evidence separately.

Run it from the repository root:

```bash
python3 scripts/audit_catalog.py
python3 scripts/audit_catalog.py --format json
```

To audit a separate checkout, pass its repository root explicitly:

```bash
python3 scripts/audit_catalog.py --root /path/to/Awesome-Loop-Models --format human
```

## Reproducible risk inventory

`scripts/build_catalog_risk_report.py` turns the raw canonical catalog and the
auditor findings into `audits/catalog-risk-report.json` and
`audits/catalog-risk-report.md`. It writes those reports but never modifies
`papers/*.yaml`. Reproduce the checked-in 2026-07-10 snapshot with:

```bash
python3 scripts/build_catalog_risk_report.py --generated-on 2026-07-10 --catalog-commit 6b460f1cbd8d033fe0d356b9125bc40b18d1083f
```

Both snapshot arguments are required provenance: `--generated-on` must be an
ISO calendar date and `--catalog-commit` must be a valid full 40-hex commit in
the repository at `--root`. Before writing, the CLI verifies that tracked
`papers/` content exactly matches that commit and that `papers/` has no
untracked files. This prevents a report from claiming a stale or unrelated
snapshot. The report records generator path and version metadata so future
format or rule changes remain identifiable.

Output overrides passed with `--json-output` and `--markdown-output` must be
relative paths that resolve below `--root`. Absolute paths, `..` traversal,
and every destination inside `papers/` are rejected.

The priority queue is deterministic. P0 contains auditor errors; P1 contains
non-P0 manual scope-review seeds or papers with multiple mechanism tags; P2
contains remaining auditor warnings or singleton vocabulary; and P3 contains
the rest. Singleton frequency is exact and case-sensitive in one combined
`domain_tags` plus `tags` table, not separate per-axis tables. The generator
checks that every canonical ID occurs exactly once in both the paper rows and
the disjoint priority batches. Auditor findings are retained, including P0
errors, but malformed or non-mapping raw YAML fails generation because it
cannot be classified safely.

This inventory is a review order, not a semantic verdict or auto-fix. Paper
scope, descriptions, and taxonomy still require primary-source evidence.

## Per-paper evidence records

`audits/papers/*.yaml` is a review ledger kept separate from canonical
`papers/*.yaml`. Copy `audits/papers/_template.yaml.example` to start a record.
The audit filename stem, `paper_id`, and canonical paper filename stem must be
identical. `source.url` must identify one of the canonical primary paper links.

Each record contains only these top-level fields:

- `paper_id` and `status` (`needs-review`, `verified`, or `remove`);
- `source.url`, `source.version`, and ISO `source.verified_on`;
- non-empty `reviewer` provenance and `confidence` (`low`, `medium`, or `high`);
- a `scope` verdict, written evidence, and a locator pointing to a section,
  page, figure, table, or equation;
- `taxonomy` entries for `category`, `mechanism_tags`, `focus_tags`,
  `domain_tags`, and optional aliases in `tags`, each with a rationale;
- `content_checks` for `title_authors`, `publication`, `description`, and
  `links`, each with a status and evidence;
- a string list of `unresolved_questions`.

All mapping keys are strict, all evidence and rationales are required, URLs
must be absolute HTTP(S) URLs, and list values must be unique. A `verified`
record requires an `in-scope` verdict, medium or high confidence, verified
content checks, no unresolved questions, and taxonomy values that exactly
match the current canonical paper. Tag-array order is ignored during that
comparison; values are not normalized. A `remove` decision requires an
evidenced `out-of-scope` verdict.

Run the ledger validator from the repository root:

```bash
# Migration mode: missing records are reported in coverage but do not fail.
python3 scripts/validate_audits.py
python3 scripts/validate_audits.py --format json

# Final gate: every canonical paper needs one verified or remove decision.
python3 scripts/validate_audits.py --require-complete
```

Malformed, duplicate-key, mismatched, duplicate-ID, and orphan records always
fail in both modes. Output and findings are deterministic; an error exits with
status 1, while a valid partial or complete ledger exits with status 0.
Completion counts include only unique records whose own schema and decision
rules pass and whose corresponding canonical paper also validates successfully.
Complete mode also rejects a missing or empty canonical `papers/` directory.

The validator is read-only, has no auto-fix mode, and never uses the network.
Audit records are research provenance only: the build does not include them in
`papers.json` or any other frontend payload. Metadata changes belong in the
canonical paper YAML only after the recorded primary-source evidence supports
them.
