#!/usr/bin/env python3
"""Enforce deterministic byte and schema budgets for generated site assets."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, TextIO


REPO_ROOT = Path(__file__).resolve().parents[1]
PAPERS_RAW_BYTES_LIMIT = 280_000
PAPERS_GZIP_BYTES_LIMIT = 60_000
PAPERS_BRIEFINGS_LIMIT = 1
BRIEFING_CONTENT_FIELDS_LIMIT = 0
SUBMISSION_META_BYTES_LIMIT = 20_000
FAVICON_BYTES_LIMIT = 10_000


@dataclass(frozen=True)
class Measurement:
    """Represent one measured asset value and its upper bound."""

    name: str
    measured: int | None
    limit: int
    unit: str

    @property
    def exceeded(self) -> bool:
        """Return whether the available measurement exceeds its budget."""
        return self.measured is not None and self.measured > self.limit


@dataclass(frozen=True)
class AssetBudgetReport:
    """Collect all budget measurements and validation violations."""

    measurements: tuple[Measurement, ...]
    violations: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """Return whether every asset and schema contract is satisfied."""
        return not self.violations


def read_required_file(path: Path, label: str, violations: list[str]) -> bytes | None:
    """Read a required file while recording a clear filesystem violation."""
    try:
        return path.read_bytes()
    except FileNotFoundError:
        violations.append(f"{label}: missing required file")
    except OSError as error:
        violations.append(f"{label}: could not be read: {error}")
    return None


def parse_json_object(raw: bytes, label: str, violations: list[str]) -> dict | None:
    """Parse a required JSON object and record syntax or top-level schema failures."""
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        violations.append(f"{label}: invalid JSON: {error}")
        return None
    if not isinstance(payload, dict):
        violations.append(f"{label}: top-level JSON value must be an object")
        return None
    return payload


def add_measurement(
    measurements: list[Measurement],
    violations: list[str],
    name: str,
    measured: int | None,
    limit: int,
    unit: str,
    failure_detail: str | None = None,
) -> None:
    """Record a measurement and append its violation without stopping later checks."""
    item = Measurement(name=name, measured=measured, limit=limit, unit=unit)
    measurements.append(item)
    if item.exceeded:
        detail = f"; {failure_detail}" if failure_detail else ""
        violations.append(f"{name}: measured={measured} {unit}, limit={limit} {unit}{detail}")


def count_nested_key(value: object, key: str) -> int:
    """Count occurrences of ``key`` recursively through JSON objects and arrays."""
    if isinstance(value, dict):
        return int(key in value) + sum(count_nested_key(item, key) for item in value.values())
    if isinstance(value, list):
        return sum(count_nested_key(item, key) for item in value)
    return 0


def validate_papers_schema(payload: dict, violations: list[str]) -> tuple[int | None, int | None]:
    """Validate the browser catalog schema and return its briefing measurements."""
    for field in ("meta", "categories"):
        if not isinstance(payload.get(field), dict):
            violations.append(f"papers.json.{field} must be an object")

    for field in ("mechanism_tags", "focus_tags", "papers", "blogs"):
        if not isinstance(payload.get(field), list):
            violations.append(f"papers.json.{field} must be an array")

    briefings = payload.get("briefings")
    if not isinstance(briefings, list):
        violations.append("papers.json.briefings must be an array")
        return None, None

    content_fields = sum(count_nested_key(briefing, "content") for briefing in briefings)
    string_fields = ("date", "title", "status", "summary", "source_path")
    for index, briefing in enumerate(briefings):
        label = f"papers.json.briefings[{index}]"
        if not isinstance(briefing, dict):
            violations.append(f"{label} must be an object")
            continue
        for field in string_fields:
            if not isinstance(briefing.get(field), str):
                violations.append(f"{label}.{field} must be a string")

        highlights = briefing.get("highlights")
        if not isinstance(highlights, list):
            violations.append(f"{label}.highlights must be an array")
        else:
            for highlight_index, highlight in enumerate(highlights):
                if not isinstance(highlight, str):
                    violations.append(f"{label}.highlights[{highlight_index}] must be a string")

        candidates = briefing.get("candidates")
        if not isinstance(candidates, list):
            violations.append(f"{label}.candidates must be an array")
        else:
            for candidate_index, candidate in enumerate(candidates):
                if not isinstance(candidate, dict):
                    violations.append(f"{label}.candidates[{candidate_index}] must be an object")
    return len(briefings), content_fields


def validate_submission_schema(payload: dict, violations: list[str]) -> None:
    """Validate the minimal path and tag inventory used by the submission page."""
    existing_paths = payload.get("existing_paths")
    if not isinstance(existing_paths, list):
        violations.append("submission-meta.json.existing_paths must be an array")
    else:
        for index, path in enumerate(existing_paths):
            if not isinstance(path, str):
                violations.append(f"submission-meta.json.existing_paths[{index}] must be a string")

    inventories = payload.get("tag_inventories")
    if not isinstance(inventories, dict):
        violations.append("submission-meta.json.tag_inventories must be an object")
        return

    for inventory_name in ("mechanism", "focus", "domain"):
        inventory = inventories.get(inventory_name)
        label = f"submission-meta.json.tag_inventories.{inventory_name}"
        if not isinstance(inventory, list):
            violations.append(f"{label} must be an array")
            continue
        for index, row in enumerate(inventory):
            row_label = f"{label}[{index}]"
            if not isinstance(row, dict):
                violations.append(f"{row_label} must be an object")
                continue
            if not isinstance(row.get("label"), str):
                violations.append(f"{row_label}.label must be a string")
            count = row.get("count")
            if type(count) is not int or count < 0:
                violations.append(f"{row_label}.count must be a non-negative integer")


def check_asset_budgets(root: Path) -> AssetBudgetReport:
    """Measure every required asset under ``root`` and aggregate all violations."""
    root = Path(root)
    measurements: list[Measurement] = []
    violations: list[str] = []

    papers_raw = read_required_file(root / "papers.json", "papers.json", violations)
    add_measurement(
        measurements,
        violations,
        "papers.json raw bytes",
        len(papers_raw) if papers_raw is not None else None,
        PAPERS_RAW_BYTES_LIMIT,
        "bytes",
    )
    add_measurement(
        measurements,
        violations,
        "papers.json deterministic gzip bytes",
        len(gzip.compress(papers_raw, mtime=0)) if papers_raw is not None else None,
        PAPERS_GZIP_BYTES_LIMIT,
        "bytes",
    )

    briefing_count: int | None = None
    content_fields: int | None = None
    if papers_raw is not None:
        papers_payload = parse_json_object(papers_raw, "papers.json", violations)
        if papers_payload is not None:
            briefing_count, content_fields = validate_papers_schema(papers_payload, violations)
    add_measurement(
        measurements,
        violations,
        "papers.json briefing count",
        briefing_count,
        PAPERS_BRIEFINGS_LIMIT,
        "items",
    )
    add_measurement(
        measurements,
        violations,
        "papers.json briefing content fields",
        content_fields,
        BRIEFING_CONTENT_FIELDS_LIMIT,
        "fields",
        "browser briefings must not contain a 'content' field",
    )

    submission_raw = read_required_file(
        root / "submission-meta.json", "submission-meta.json", violations
    )
    add_measurement(
        measurements,
        violations,
        "submission-meta.json raw bytes",
        len(submission_raw) if submission_raw is not None else None,
        SUBMISSION_META_BYTES_LIMIT,
        "bytes",
    )
    if submission_raw is not None:
        submission_payload = parse_json_object(
            submission_raw, "submission-meta.json", violations
        )
        if submission_payload is not None:
            validate_submission_schema(submission_payload, violations)

    favicon_raw = read_required_file(
        root / "assets" / "favicon.png", "assets/favicon.png", violations
    )
    add_measurement(
        measurements,
        violations,
        "assets/favicon.png raw bytes",
        len(favicon_raw) if favicon_raw is not None else None,
        FAVICON_BYTES_LIMIT,
        "bytes",
    )

    return AssetBudgetReport(tuple(measurements), tuple(violations))


def render_report(report: AssetBudgetReport, stream: TextIO | None = None) -> None:
    """Print every measured/limit pair followed by all validation violations."""
    output = stream if stream is not None else sys.stdout
    print("Static asset budget report:", file=output)
    for item in report.measurements:
        measured = "unavailable" if item.measured is None else str(item.measured)
        status = "ERROR" if item.measured is None else ("FAIL" if item.exceeded else "PASS")
        print(
            f"- {item.name}: measured={measured} {item.unit}, "
            f"limit={item.limit} {item.unit} [{status}]",
            file=output,
        )
    if report.violations:
        print("Violations:", file=output)
        for violation in report.violations:
            print(f"- {violation}", file=output)
    print(f"Asset budgets: {'PASS' if report.ok else 'FAIL'}", file=output)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line options for the repository root to inspect."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="repository root containing generated site assets (default: current checkout)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the checker, print its complete report, and return a shell exit code."""
    args = parse_args(argv)
    report = check_asset_budgets(args.root)
    render_report(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
