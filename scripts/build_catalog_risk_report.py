#!/usr/bin/env python3
"""Build deterministic JSON and Markdown risk inventories for the paper catalog."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Collection, Sequence

import yaml

try:
    from scripts.audit_catalog import Finding, audit_catalog
except ModuleNotFoundError:  # Support ``python scripts/build_catalog_risk_report.py``.
    from audit_catalog import Finding, audit_catalog


REPO_ROOT = Path(__file__).resolve().parents[1]
PRIORITIES = ("P0", "P1", "P2", "P3")
MANUAL_SCOPE_REVIEW_SEEDS = frozenset(
    {"2510.03206", "2601.21582", "2604.27981", "2605.17811", "2606.20325"}
)
UNSAFE_FINDING_CODES = frozenset(
    {"duplicate-yaml-key", "missing-papers-directory", "top-level-type", "yaml-parse"}
)
COMMIT_RE = re.compile(r"[0-9a-fA-F]{40}")


class CatalogRiskReportError(ValueError):
    """Raised when raw catalog data cannot produce a trustworthy risk report."""


def _validate_generated_on(value: str) -> str:
    """Return a valid ISO date or raise a report error."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise CatalogRiskReportError("generated-on must use YYYY-MM-DD")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise CatalogRiskReportError("generated-on must be a valid calendar date") from exc
    return value


def _validate_catalog_commit(value: str) -> str:
    """Return a 40-hex catalog commit or raise a report error."""
    if COMMIT_RE.fullmatch(value) is None:
        raise CatalogRiskReportError("catalog-commit must be exactly 40 hexadecimal characters")
    return value


def _string_tags(record: dict, field: str) -> tuple[str, ...]:
    """Return string tag items without inventing values for malformed lists."""
    value = record.get(field)
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _finding_sort_key(finding: Finding) -> tuple[str, str, int, str, str]:
    """Mirror the canonical auditor ordering for deterministic serialization."""
    return (
        finding.source,
        finding.field,
        0 if finding.severity == "error" else 1,
        finding.code,
        finding.message,
    )


def _load_raw_papers(root: Path, findings: Sequence[Finding]) -> list[tuple[Path, dict]]:
    """Load classifiable raw mappings and fail clearly on unsafe YAML input."""
    papers_dir = root / "papers"
    if not papers_dir.is_dir():
        raise CatalogRiskReportError("papers: canonical papers directory is missing")
    unsafe = [finding for finding in findings if finding.code in UNSAFE_FINDING_CODES]
    if unsafe:
        details = ", ".join(f"{item.source} ({item.code})" for item in unsafe)
        raise CatalogRiskReportError(f"raw YAML cannot be classified safely: {details}")
    paths = sorted(
        path for path in papers_dir.glob("*.yaml") if not path.name.startswith("_template")
    )
    if not paths:
        raise CatalogRiskReportError("papers: canonical catalog is empty")
    records: list[tuple[Path, dict]] = []
    for path in paths:
        source = f"papers/{path.name}"
        try:
            record = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise CatalogRiskReportError(f"{source}: YAML could not be parsed") from exc
        if not isinstance(record, dict):
            raise CatalogRiskReportError(f"{source}: expected a top-level mapping")
        records.append((path, record))
    return records


def _assert_report_parity(report: dict, canonical_ids: Sequence[str]) -> None:
    """Reject duplicate, missing, overlapping, or misassigned report IDs."""
    row_ids = [row["paper_id"] for row in report["papers"]]
    batches = report["batches"]
    if tuple(batches) != PRIORITIES:
        raise CatalogRiskReportError("batch keys must be exactly P0, P1, P2, and P3")
    batch_ids = [paper_id for priority in PRIORITIES for paper_id in batches[priority]]
    expected = set(canonical_ids)
    if len(row_ids) != len(set(row_ids)) or set(row_ids) != expected:
        raise CatalogRiskReportError("paper rows do not match unique canonical paper IDs")
    if len(batch_ids) != len(set(batch_ids)) or set(batch_ids) != expected:
        raise CatalogRiskReportError("priority batches overlap or do not cover the catalog")
    if report["paper_count"] != len(expected):
        raise CatalogRiskReportError("paper_count does not match canonical paper IDs")
    for row in report["papers"]:
        if row["paper_id"] not in batches[row["priority"]]:
            raise CatalogRiskReportError(f"{row['paper_id']}: row priority disagrees with batches")
        if row["reasons"] != sorted(set(row["reasons"])):
            raise CatalogRiskReportError(f"{row['paper_id']}: reasons are not unique and sorted")


def build_catalog_risk_report(
    root: Path,
    findings: Sequence[Finding],
    generated_on: str,
    catalog_commit: str,
    manual_scope_review_seeds: Collection[str] = MANUAL_SCOPE_REVIEW_SEEDS,
) -> dict:
    """Build one deterministic report dict from raw papers, findings, and snapshot constants."""
    root = Path(root)
    generated_on = _validate_generated_on(generated_on)
    catalog_commit = _validate_catalog_commit(catalog_commit)
    ordered_findings = sorted(findings, key=_finding_sort_key)
    records = _load_raw_papers(root, ordered_findings)
    findings_by_id: dict[str, list[Finding]] = defaultdict(list)
    for finding in ordered_findings:
        findings_by_id[Path(finding.source).stem].append(finding)
    tag_frequency = Counter(
        tag
        for _, record in records
        for field in ("domain_tags", "tags")
        for tag in _string_tags(record, field)
    )
    seeds = frozenset(manual_scope_review_seeds)
    batches = {priority: [] for priority in PRIORITIES}
    rows = []
    for path, record in records:
        paper_id = path.stem
        paper_findings = findings_by_id[paper_id]
        mechanisms = _string_tags(record, "mechanism_tags")
        reasons = [f"auditor:{finding.code}" for finding in paper_findings]
        if paper_id in seeds:
            reasons.append("manual-scope-review-seed")
        if len(mechanisms) > 1:
            reasons.append("multiple-mechanism-tags")
        reasons.extend(
            f"singleton-domain-tag:{tag}"
            for tag in _string_tags(record, "domain_tags")
            if tag_frequency[tag] == 1
        )
        reasons.extend(
            f"singleton-alias-tag:{tag}"
            for tag in _string_tags(record, "tags")
            if tag_frequency[tag] == 1
        )
        reasons = sorted(set(reasons))
        if any(finding.severity == "error" for finding in paper_findings):
            priority = "P0"
        elif paper_id in seeds or len(mechanisms) > 1:
            priority = "P1"
        elif any(finding.severity == "warning" for finding in paper_findings) or any(
            reason.startswith("singleton-") for reason in reasons
        ):
            priority = "P2"
        else:
            priority = "P3"
        batches[priority].append(paper_id)
        rows.append(
            {
                "paper_id": paper_id,
                "source_path": f"papers/{path.name}",
                "priority": priority,
                "reasons": reasons,
            }
        )
    paper_count = len(rows)
    report = {
        "schema_version": 1,
        "generated_on": generated_on,
        "catalog_commit": catalog_commit,
        "paper_count": paper_count,
        "finding_counts": {
            "error": sum(item.severity == "error" for item in ordered_findings),
            "warning": sum(item.severity == "warning" for item in ordered_findings),
        },
        "auditor_findings": [asdict(item) for item in ordered_findings],
        "priority_rules": {
            "P0": "Paper has at least one auditor finding with severity error.",
            "P1": "Paper is not P0 and either has more than one mechanism_tags value or is in the manual scope-review seed set.",
            "P2": "Paper is not P0 or P1 and either has an auditor warning or uses a domain_tags or tags value whose exact full-catalog frequency is one.",
            "P3": "Paper does not match P0, P1, or P2.",
            "manual_scope_review_seeds": sorted(seeds),
            "singleton_frequency": f"Exact, case-sensitive tag values counted in one combined domain_tags plus tags frequency table across all {paper_count} canonical paper records.",
            "reason_order": "Reasons are unique and sorted lexicographically.",
        },
        "batches": batches,
        "papers": rows,
    }
    _assert_report_parity(report, [path.stem for path, _ in records])
    return report


def render_catalog_risk_markdown(report: dict) -> str:
    """Render Markdown solely from a completed report dict."""
    counts = report["finding_counts"]
    batches = report["batches"]
    paper_count = report["paper_count"]
    findings_by_id: dict[str, list[dict]] = defaultdict(list)
    for finding in report["auditor_findings"]:
        findings_by_id[Path(finding["source"]).stem].append(finding)
    seeds = report["priority_rules"]["manual_scope_review_seeds"]
    lines = [
        "# Catalog risk inventory",
        "",
        f"Generated on: {report['generated_on']}",
        f"Catalog snapshot: {report['catalog_commit']}",
        f"Canonical papers: {paper_count}",
        "",
        "## What this report establishes",
        "",
        "This is a deterministic review queue for the canonical papers/*.yaml catalog. It combines the read-only structural auditor with explicit risk heuristics; it does not establish that a paper is in scope, that its description is faithful, or that its taxonomy is semantically correct.",
        "",
        f"At this snapshot, scripts/audit_catalog.py reports **{counts['error']} errors / {counts['warning']} warnings**. Every semantic conclusion still requires manual review against the primary paper source. This inventory does not auto-fix YAML and must not be used as evidence for automatic tag or content changes.",
        "",
        "## Priority rules",
        "",
        "- **P0:** at least one auditor error.",
        "- **P1:** not P0, and either more than one mechanism_tags value or membership in the manual scope-review seed set.",
        "- **P2:** not P0/P1, and either an auditor warning or an exact domain_tags/tags value that occurs once in the full catalog.",
        "- **P3:** all remaining papers.",
        f"- Reasons are deduplicated and sorted lexicographically. Singleton frequency uses one combined domain_tags plus tags table and is exact and case-sensitive across all {paper_count} canonical records; the two axes are not counted separately.",
        "",
        f"Batch sizes: **P0 {len(batches['P0'])} / P1 {len(batches['P1'])} / P2 {len(batches['P2'])} / P3 {len(batches['P3'])}**.",
        "",
        "The manual scope-review seeds are scheduling inputs only, not findings or conclusions: "
        + ", ".join(seeds)
        + ". A seed paper may be accurate and in scope; the label only says to check the primary source early.",
        "",
        "A publication year/date warning is also not an automatic correction. The catalog year may intentionally represent a venue year while published_date records an earlier preprint date, so venue and primary-source evidence must be checked before editing either field.",
        "",
        "## P0 — structural blockers",
        "",
        "| Paper | Auditor findings | Required review |",
        "| --- | --- | --- |",
    ]
    for row in report["papers"]:
        if row["priority"] != "P0":
            continue
        text = "<br>".join(
            f"{item['code']}: {item['field']} — {item['message']}"
            for item in findings_by_id[row["paper_id"]]
        )
        lines.append(
            f"| {row['paper_id']} | {text} | Check the canonical primary source before adding domain tags or changing the arXiv link. |"
        )
    lines.extend(["", "## P1 — early semantic review", "", "| Paper | Reasons |", "| --- | --- |"])
    lines.extend(
        f"| {row['paper_id']} | {'<br>'.join(row['reasons'])} |"
        for row in report["papers"]
        if row["priority"] == "P1"
    )
    lines.extend(
        [
            "",
            "P1 reasons are review triggers, not evidence of an error. In particular, multiple mechanism tags can be legitimate when the paper genuinely combines mechanisms.",
            "",
            "## P2 and P3 coverage",
            "",
            f"### P2 — {len(batches['P2'])} papers",
            "",
            "Warnings and singleton vocabulary require human judgment. A singleton tag can be precise and valid; frequency alone is never a reason to rename or remove it.",
            "",
        ]
    )
    for start in range(0, len(batches["P2"]), 12):
        lines.append("- " + ", ".join(batches["P2"][start : start + 12]))
    lines.extend(
        [
            "",
            f"### P3 — {len(batches['P3'])} papers",
            "",
            "P3 is lower heuristic risk, not verified accuracy. These papers still need primary-source content and taxonomy review.",
            "",
        ]
    )
    for start in range(0, len(batches["P3"]), 12):
        lines.append("- " + ", ".join(batches["P3"][start : start + 12]))
    lines.extend(
        [
            "",
            "## Review order and evidence requirement",
            "",
            "1. **P0:** resolve structural blockers only after checking the primary source and recording evidence.",
            "2. **P1:** review manual scope seeds and multi-mechanism classifications against the paper method, equations, and experiments.",
            "3. **P2:** adjudicate auditor warnings and singleton vocabulary; preserve intentional venue-year differences and precise rare tags.",
            "4. **P3:** complete the remaining paper-by-paper content and taxonomy review.",
            "",
            "For every paper, use the canonical primary paper rather than a title, search snippet, run name, or this heuristic report. Record source version, locator, scope evidence, taxonomy rationale, and content checks in audits/papers before changing canonical metadata. No item in this report authorizes an automatic fix.",
        ]
    )
    return "\n".join(lines) + "\n"


def _arg_generated_on(value: str) -> str:
    """Adapt generated-on validation to argparse's error contract."""
    try:
        return _validate_generated_on(value)
    except CatalogRiskReportError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _arg_catalog_commit(value: str) -> str:
    """Adapt catalog-commit validation to argparse's error contract."""
    try:
        return _validate_catalog_commit(value)
    except CatalogRiskReportError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def build_parser() -> argparse.ArgumentParser:
    """Build the report-writing CLI parser."""
    parser = argparse.ArgumentParser(
        description="Build and write catalog risk reports without modifying papers/*.yaml."
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Repository root.")
    parser.add_argument("--generated-on", type=_arg_generated_on, required=True, help="Snapshot date in YYYY-MM-DD form.")
    parser.add_argument("--catalog-commit", type=_arg_catalog_commit, required=True, help="Snapshot commit as exactly 40 hex characters.")
    parser.add_argument("--json-output", type=Path, default=Path("audits/catalog-risk-report.json"), help="JSON output path, relative to root by default.")
    parser.add_argument("--markdown-output", type=Path, default=Path("audits/catalog-risk-report.md"), help="Markdown output path, relative to root by default.")
    return parser


def _output_path(root: Path, value: Path) -> Path:
    """Resolve one output below root unless the caller supplied an absolute path."""
    return value if value.is_absolute() else root / value


def main(argv: Sequence[str] | None = None) -> int:
    """Audit the snapshot and write both reports, returning nonzero on unsafe input."""
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        report = build_catalog_risk_report(
            root=root,
            findings=audit_catalog(root),
            generated_on=args.generated_on,
            catalog_commit=args.catalog_commit,
        )
        outputs = (
            (_output_path(root, args.json_output), json.dumps(report, indent=2, ensure_ascii=False) + "\n"),
            (_output_path(root, args.markdown_output), render_catalog_risk_markdown(report)),
        )
        papers_dir = (root / "papers").resolve()
        for path, _ in outputs:
            if path.resolve().is_relative_to(papers_dir):
                raise CatalogRiskReportError(f"refusing to write report inside papers/: {path}")
        for path, content in outputs:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    except (CatalogRiskReportError, OSError) as exc:
        print(f"Catalog risk report generation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
