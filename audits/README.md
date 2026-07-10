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
