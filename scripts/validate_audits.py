#!/usr/bin/env python3
"""Validate read-only per-paper evidence records against canonical YAML."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Sequence
from urllib.parse import parse_qs, urlsplit, urlunsplit

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_FIELDS = frozenset(
    {
        "paper_id",
        "status",
        "source",
        "reviewer",
        "confidence",
        "scope",
        "taxonomy",
        "content_checks",
        "unresolved_questions",
    }
)
SOURCE_FIELDS = frozenset({"url", "version", "verified_on"})
SCOPE_FIELDS = frozenset({"verdict", "evidence", "locator"})
TAXONOMY_FIELDS = (
    "category",
    "mechanism_tags",
    "focus_tags",
    "domain_tags",
    "tags",
)
CONTENT_CHECK_FIELDS = (
    "title_authors",
    "publication",
    "description",
    "links",
)
STATUS_VALUES = frozenset({"needs-review", "verified", "remove"})
CONFIDENCE_VALUES = frozenset({"low", "medium", "high"})
SCOPE_VALUES = frozenset({"in-scope", "out-of-scope", "uncertain"})
CHECK_STATUS_VALUES = frozenset({"verified", "issue", "unresolved"})
PRIMARY_LINK_FIELDS = ("arxiv", "paper", "openreview")
ARXIV_ID_RE = re.compile(r"^\d{4}\.\d{4,5}$")
ARXIV_PATH_RE = re.compile(
    r"^/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?/?$",
    re.IGNORECASE,
)
YAML_LOAD_FAILED = object()


class DuplicateYamlKeyError(yaml.YAMLError):
    """Raised when a YAML mapping repeats an explicit key."""


class UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def construct_unique_mapping(
    loader: UniqueKeySafeLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict:
    """Construct a mapping while rejecting keys that SafeLoader overwrites."""
    mapping: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            line = key_node.start_mark.line + 1
            raise DuplicateYamlKeyError(
                f"Duplicate YAML mapping key {key!r} at line {line}."
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_unique_mapping,
)


@dataclass(frozen=True)
class Finding:
    """One deterministic validation error."""

    severity: str
    code: str
    source: str
    field: str
    message: str


@dataclass(frozen=True)
class Coverage:
    """Deterministic review coverage counts for the canonical catalog."""

    canonical_papers: int
    audit_records: int
    covered_papers: int
    verified: int
    needs_review: int
    remove: int
    complete_decisions: int
    missing_papers: int


@dataclass(frozen=True)
class ValidationResult:
    """Findings and coverage returned by the validator."""

    coverage: Coverage
    findings: tuple[Finding, ...]

    @property
    def valid(self) -> bool:
        """Return whether validation produced no errors."""
        return not self.findings

    def to_dict(self) -> dict:
        """Return the stable JSON-ready representation."""
        return {
            "valid": self.valid,
            "coverage": asdict(self.coverage),
            "findings": [asdict(finding) for finding in self.findings],
        }


def _source_name(path: Path, root: Path) -> str:
    """Return a repository-relative source path when possible."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _add(
    findings: list[Finding],
    code: str,
    source: str,
    field: str,
    message: str,
) -> None:
    """Append one validation error."""
    findings.append(Finding("error", code, source, field, message))


def _sort_findings(findings: list[Finding]) -> tuple[Finding, ...]:
    """Return findings in a stable order shared by both output formats."""
    return tuple(
        sorted(
            findings,
            key=lambda item: (
                item.source,
                item.field,
                item.code,
                item.message,
            ),
        )
    )


def _yaml_paths(directory: Path) -> list[Path]:
    """List non-template YAML sources in deterministic order."""
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.glob("*.yaml")
        if not path.name.startswith("_template")
    )


def _load_yaml(
    path: Path,
    root: Path,
    findings: list[Finding],
) -> object:
    """Load one YAML source safely and turn parse failures into findings."""
    source = _source_name(path, root)
    try:
        return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeySafeLoader)
    except DuplicateYamlKeyError as exc:
        _add(findings, "duplicate-yaml-key", source, "$", str(exc))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        _add(findings, "yaml-parse", source, "$", str(exc))
    return YAML_LOAD_FAILED


def _validate_mapping_shape(
    value: dict,
    required: Sequence[str],
    allowed: frozenset[str],
    source: str,
    prefix: str,
    findings: list[Finding],
) -> None:
    """Report missing and unknown keys for one schema mapping."""
    for field in required:
        if field not in value:
            path = f"{prefix}.{field}" if prefix else field
            _add(findings, "missing-field", source, path, "Required field is missing.")
    for field in sorted(value, key=str):
        if field not in allowed:
            path = f"{prefix}.{field}" if prefix else str(field)
            _add(findings, "unknown-field", source, path, "Field is not allowed.")


def _mapping_field(
    value: dict,
    field: str,
    source: str,
    prefix: str,
    findings: list[Finding],
) -> dict | None:
    """Return a nested mapping or report its invalid type."""
    if field not in value:
        return None
    nested = value[field]
    path = f"{prefix}.{field}" if prefix else field
    if not isinstance(nested, dict):
        _add(
            findings,
            "invalid-field-type",
            source,
            path,
            f"Expected a mapping; got {type(nested).__name__}.",
        )
        return None
    return nested


def _string_field(
    value: dict,
    field: str,
    source: str,
    prefix: str,
    findings: list[Finding],
) -> str | None:
    """Return a non-empty string field or report its invalid value."""
    if field not in value:
        return None
    item = value[field]
    path = f"{prefix}.{field}" if prefix else field
    if not isinstance(item, str) or not item.strip():
        _add(
            findings,
            "invalid-field-type",
            source,
            path,
            "Expected a non-empty string.",
        )
        return None
    return item


def _enum_field(
    value: dict,
    field: str,
    choices: frozenset[str],
    source: str,
    prefix: str,
    findings: list[Finding],
) -> str | None:
    """Return a permitted enum value or report its invalid value."""
    item = _string_field(value, field, source, prefix, findings)
    if item is not None and item not in choices:
        path = f"{prefix}.{field}" if prefix else field
        _add(
            findings,
            "invalid-enum",
            source,
            path,
            f"Expected one of {', '.join(sorted(choices))}; got {item!r}.",
        )
        return None
    return item


def _string_list_field(
    value: dict,
    field: str,
    source: str,
    prefix: str,
    findings: list[Finding],
) -> list[str] | None:
    """Return a unique string list or report type, item, and duplicate errors."""
    if field not in value:
        return None
    items = value[field]
    path = f"{prefix}.{field}" if prefix else field
    if not isinstance(items, list):
        _add(
            findings,
            "invalid-field-type",
            source,
            path,
            f"Expected a list; got {type(items).__name__}.",
        )
        return None
    valid_items: list[str] = []
    seen: dict[str, int] = {}
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        if not isinstance(item, str) or not item.strip():
            _add(
                findings,
                "invalid-list-item",
                source,
                item_path,
                "Expected a non-empty string.",
            )
            continue
        normalized = item.strip().casefold()
        if normalized in seen:
            _add(
                findings,
                "duplicate-list-item",
                source,
                item_path,
                f"Duplicates {path}[{seen[normalized]}].",
            )
        else:
            seen[normalized] = index
        valid_items.append(item)
    return valid_items


def _is_iso_date(value: str) -> bool:
    """Return whether a string is a real zero-padded ISO calendar date."""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _is_absolute_http_url(value: str) -> bool:
    """Return whether a string is an absolute HTTP(S) URL with a host."""
    try:
        parsed = urlsplit(value)
        return parsed.scheme.lower() in {"http", "https"} and bool(parsed.hostname)
    except ValueError:
        return False


def _url_identity(value: str) -> str | None:
    """Return a stable paper-source identity for a valid absolute URL."""
    if not _is_absolute_http_url(value):
        return None
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    if host in {"arxiv.org", "www.arxiv.org"}:
        match = ARXIV_PATH_RE.fullmatch(parsed.path)
        if match:
            return f"arxiv:{match.group(1)}"
    if host in {"openreview.net", "www.openreview.net"}:
        openreview_id = parse_qs(parsed.query).get("id", [])
        if openreview_id and openreview_id[0]:
            return f"openreview:{openreview_id[0]}"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), netloc, path, parsed.query, ""))


def _validate_canonical_paper(
    data: dict,
    paper_id: str,
    source: str,
    findings: list[Finding],
) -> tuple[dict[str, object], frozenset[str]]:
    """Validate and return canonical taxonomy plus primary-source identities."""
    taxonomy: dict[str, object] = {}
    required = ("category", "mechanism_tags", "focus_tags", "domain_tags", "links")
    for field in required:
        if field not in data:
            _add(
                findings,
                "missing-field",
                source,
                field,
                "Canonical field required for audit validation is missing.",
            )
    category = data.get("category")
    if isinstance(category, str) and category.strip():
        taxonomy["category"] = category
    elif "category" in data:
        _add(
            findings,
            "invalid-field-type",
            source,
            "category",
            "Expected a non-empty string.",
        )
    for field in TAXONOMY_FIELDS[1:]:
        if field not in data:
            if field == "tags":
                taxonomy[field] = []
            continue
        items = _string_list_field(data, field, source, "", findings)
        if items is not None:
            taxonomy[field] = items

    identities: set[str] = set()
    links = data.get("links")
    if isinstance(links, dict):
        for field in PRIMARY_LINK_FIELDS:
            url = links.get(field)
            if url in (None, ""):
                continue
            if not isinstance(url, str) or not _is_absolute_http_url(url):
                _add(
                    findings,
                    "invalid-url",
                    source,
                    f"links.{field}",
                    "Expected an absolute HTTP(S) URL.",
                )
                continue
            identity = _url_identity(url)
            if identity is not None:
                identities.add(identity)
            if ARXIV_ID_RE.fullmatch(paper_id) and identity is not None:
                if identity.startswith("arxiv:") and identity != f"arxiv:{paper_id}":
                    _add(
                        findings,
                        "canonical-source-id-mismatch",
                        source,
                        f"links.{field}",
                        f"Source identity {identity!r} does not match {paper_id!r}.",
                    )
    elif "links" in data:
        _add(
            findings,
            "invalid-field-type",
            source,
            "links",
            f"Expected a mapping; got {type(links).__name__}.",
        )
    if not identities:
        _add(
            findings,
            "missing-primary-source",
            source,
            "links",
            "Expected an absolute arxiv, paper, or openreview source URL.",
        )
    return taxonomy, frozenset(identities)


def _validate_taxonomy(
    data: dict,
    source: str,
    findings: list[Finding],
) -> dict[str, object]:
    """Validate taxonomy value/rationale mappings and return their values."""
    _validate_mapping_shape(
        data,
        TAXONOMY_FIELDS,
        frozenset(TAXONOMY_FIELDS),
        source,
        "taxonomy",
        findings,
    )
    values: dict[str, object] = {}
    for field in TAXONOMY_FIELDS:
        entry = _mapping_field(data, field, source, "taxonomy", findings)
        if entry is None:
            continue
        value_key = "value" if field == "category" else "values"
        allowed = frozenset({value_key, "rationale"})
        _validate_mapping_shape(
            entry,
            (value_key, "rationale"),
            allowed,
            source,
            f"taxonomy.{field}",
            findings,
        )
        if field == "category":
            category = _string_field(
                entry, "value", source, "taxonomy.category", findings
            )
            if category is not None:
                values[field] = category
        else:
            tags = _string_list_field(
                entry, "values", source, f"taxonomy.{field}", findings
            )
            if tags is not None:
                values[field] = tags
        _string_field(entry, "rationale", source, f"taxonomy.{field}", findings)
    return values


def _validate_content_checks(
    data: dict,
    source: str,
    findings: list[Finding],
) -> dict[str, str]:
    """Validate content-check mappings and return each valid status."""
    _validate_mapping_shape(
        data,
        CONTENT_CHECK_FIELDS,
        frozenset(CONTENT_CHECK_FIELDS),
        source,
        "content_checks",
        findings,
    )
    statuses: dict[str, str] = {}
    for field in CONTENT_CHECK_FIELDS:
        entry = _mapping_field(data, field, source, "content_checks", findings)
        if entry is None:
            continue
        _validate_mapping_shape(
            entry,
            ("status", "evidence"),
            frozenset({"status", "evidence"}),
            source,
            f"content_checks.{field}",
            findings,
        )
        status = _enum_field(
            entry,
            "status",
            CHECK_STATUS_VALUES,
            source,
            f"content_checks.{field}",
            findings,
        )
        if status is not None:
            statuses[field] = status
        _string_field(
            entry,
            "evidence",
            source,
            f"content_checks.{field}",
            findings,
        )
    return statuses


def _same_taxonomy_value(field: str, audit_value: object, paper_value: object) -> bool:
    """Compare category exactly and tag arrays as order-insensitive exact values."""
    if field == "category":
        return audit_value == paper_value
    if not isinstance(audit_value, list) or not isinstance(paper_value, list):
        return False
    return sorted(audit_value) == sorted(paper_value)


def _validate_audit_record(
    data: dict,
    path: Path,
    root: Path,
    canonical: dict[str, tuple[dict[str, object], frozenset[str]]],
    findings: list[Finding],
) -> tuple[str | None, str | None]:
    """Validate one audit record and return its logical ID and valid status."""
    source = _source_name(path, root)
    _validate_mapping_shape(
        data,
        tuple(AUDIT_FIELDS),
        AUDIT_FIELDS,
        source,
        "",
        findings,
    )
    paper_id = _string_field(data, "paper_id", source, "", findings)
    status = _enum_field(
        data, "status", STATUS_VALUES, source, "", findings
    )
    confidence = _enum_field(
        data, "confidence", CONFIDENCE_VALUES, source, "", findings
    )
    _string_field(data, "reviewer", source, "", findings)

    if paper_id is not None and paper_id != path.stem:
        _add(
            findings,
            "filename-id-mismatch",
            source,
            "paper_id",
            f"Record ID {paper_id!r} does not match filename stem {path.stem!r}.",
        )
    if paper_id is not None and paper_id not in canonical:
        _add(
            findings,
            "unknown-paper-id",
            source,
            "paper_id",
            f"No canonical papers/{paper_id}.yaml record exists.",
        )

    source_data = _mapping_field(data, "source", source, "", findings)
    source_identity: str | None = None
    if source_data is not None:
        _validate_mapping_shape(
            source_data,
            tuple(SOURCE_FIELDS),
            SOURCE_FIELDS,
            source,
            "source",
            findings,
        )
        source_url = _string_field(source_data, "url", source, "source", findings)
        if source_url is not None:
            if not _is_absolute_http_url(source_url):
                _add(
                    findings,
                    "invalid-url",
                    source,
                    "source.url",
                    "Expected an absolute HTTP(S) URL.",
                )
            else:
                source_identity = _url_identity(source_url)
        _string_field(source_data, "version", source, "source", findings)
        verified_on = _string_field(
            source_data, "verified_on", source, "source", findings
        )
        if verified_on is not None and not _is_iso_date(verified_on):
            _add(
                findings,
                "invalid-date",
                source,
                "source.verified_on",
                "Expected a real ISO date in YYYY-MM-DD form.",
            )

    scope_data = _mapping_field(data, "scope", source, "", findings)
    scope_verdict: str | None = None
    if scope_data is not None:
        _validate_mapping_shape(
            scope_data,
            tuple(SCOPE_FIELDS),
            SCOPE_FIELDS,
            source,
            "scope",
            findings,
        )
        scope_verdict = _enum_field(
            scope_data,
            "verdict",
            SCOPE_VALUES,
            source,
            "scope",
            findings,
        )
        _string_field(scope_data, "evidence", source, "scope", findings)
        _string_field(scope_data, "locator", source, "scope", findings)

    taxonomy_data = _mapping_field(data, "taxonomy", source, "", findings)
    taxonomy_values = (
        _validate_taxonomy(taxonomy_data, source, findings)
        if taxonomy_data is not None
        else {}
    )
    checks_data = _mapping_field(data, "content_checks", source, "", findings)
    check_statuses = (
        _validate_content_checks(checks_data, source, findings)
        if checks_data is not None
        else {}
    )
    unresolved = _string_list_field(
        data, "unresolved_questions", source, "", findings
    )

    if paper_id in canonical:
        paper_taxonomy, canonical_identities = canonical[paper_id]
        if source_identity is not None and source_identity not in canonical_identities:
            _add(
                findings,
                "source-id-mismatch",
                source,
                "source.url",
                "Audit source does not match a canonical primary source URL.",
            )
        if status == "verified":
            for field in TAXONOMY_FIELDS:
                if field in taxonomy_values and field in paper_taxonomy:
                    if not _same_taxonomy_value(
                        field, taxonomy_values[field], paper_taxonomy[field]
                    ):
                        value_key = "value" if field == "category" else "values"
                        _add(
                            findings,
                            "taxonomy-drift",
                            source,
                            f"taxonomy.{field}.{value_key}",
                            "Verified taxonomy must exactly match canonical YAML.",
                        )

    if status == "verified":
        if scope_verdict != "in-scope":
            _add(
                findings,
                "verified-scope",
                source,
                "scope.verdict",
                "Verified records must have an in-scope verdict.",
            )
        if confidence not in {"medium", "high"}:
            _add(
                findings,
                "verified-confidence",
                source,
                "confidence",
                "Verified records require medium or high confidence.",
            )
        for field, check_status in check_statuses.items():
            if check_status != "verified":
                _add(
                    findings,
                    "verified-content",
                    source,
                    f"content_checks.{field}.status",
                    "Every content check must be verified.",
                )
        if unresolved:
            _add(
                findings,
                "verified-unresolved",
                source,
                "unresolved_questions",
                "Verified records cannot have unresolved questions.",
            )
    elif status == "remove" and scope_verdict != "out-of-scope":
        _add(
            findings,
            "remove-scope",
            source,
            "scope.verdict",
            "Removal records must have an out-of-scope verdict.",
        )
    return paper_id, status


def validate_audits(
    root: Path | str = REPO_ROOT,
    require_complete: bool = False,
) -> ValidationResult:
    """Validate canonical paper and audit YAML without writing or using network."""
    root = Path(root)
    findings: list[Finding] = []
    paper_paths = _yaml_paths(root / "papers")
    audit_paths = _yaml_paths(root / "audits" / "papers")

    canonical: dict[str, tuple[dict[str, object], frozenset[str]]] = {}
    canonical_sources: dict[str, str] = {}
    for path in paper_paths:
        source = _source_name(path, root)
        canonical_sources[path.stem] = source
        loaded = _load_yaml(path, root, findings)
        if loaded is YAML_LOAD_FAILED:
            canonical[path.stem] = ({}, frozenset())
        elif not isinstance(loaded, dict):
            _add(
                findings,
                "top-level-type",
                source,
                "$",
                f"Expected a mapping; got {type(loaded).__name__}.",
            )
            canonical[path.stem] = ({}, frozenset())
        else:
            canonical[path.stem] = _validate_canonical_paper(
                loaded, path.stem, source, findings
            )

    audit_records: list[tuple[str, str | None, str | None]] = []
    records_by_id: dict[str, list[str]] = {}
    for path in audit_paths:
        source = _source_name(path, root)
        loaded = _load_yaml(path, root, findings)
        paper_id: str | None = None
        status: str | None = None
        if loaded is YAML_LOAD_FAILED:
            pass
        elif not isinstance(loaded, dict):
            _add(
                findings,
                "top-level-type",
                source,
                "$",
                f"Expected a mapping; got {type(loaded).__name__}.",
            )
        else:
            paper_id, status = _validate_audit_record(
                loaded, path, root, canonical, findings
            )
        audit_records.append((source, paper_id, status))
        if paper_id is not None:
            prior = records_by_id.setdefault(paper_id, [])
            if prior:
                _add(
                    findings,
                    "duplicate-audit-id",
                    source,
                    "paper_id",
                    f"Paper ID {paper_id!r} already appears in {prior[0]}.",
                )
            prior.append(source)

    canonical_ids = set(canonical)
    covered_ids = canonical_ids.intersection(records_by_id)
    missing_ids = canonical_ids.difference(records_by_id)
    unique_statuses: dict[str, str] = {}
    for _, paper_id, status in audit_records:
        if (
            paper_id in covered_ids
            and len(records_by_id[paper_id]) == 1
            and status is not None
        ):
            unique_statuses[paper_id] = status

    if require_complete:
        for paper_id in sorted(missing_ids):
            _add(
                findings,
                "missing-audit",
                canonical_sources[paper_id],
                "audit",
                f"No audits/papers/{paper_id}.yaml record exists.",
            )
        for source, paper_id, status in audit_records:
            if paper_id in canonical_ids and status == "needs-review":
                _add(
                    findings,
                    "incomplete-review",
                    source,
                    "status",
                    "Complete mode requires verified or remove status.",
                )

    verified = sum(status == "verified" for status in unique_statuses.values())
    needs_review = sum(
        status == "needs-review" for status in unique_statuses.values()
    )
    remove = sum(status == "remove" for status in unique_statuses.values())
    coverage = Coverage(
        canonical_papers=len(canonical),
        audit_records=len(audit_paths),
        covered_papers=len(covered_ids),
        verified=verified,
        needs_review=needs_review,
        remove=remove,
        complete_decisions=verified + remove,
        missing_papers=len(missing_ids),
    )
    return ValidationResult(coverage, _sort_findings(findings))


def _render_human(result: ValidationResult) -> str:
    """Render a compact deterministic human-readable report."""
    coverage = result.coverage
    lines = [
        "Paper evidence audit validation",
        (
            "Coverage: "
            f"{coverage.covered_papers}/{coverage.canonical_papers} papers; "
            f"verified={coverage.verified}; "
            f"needs-review={coverage.needs_review}; "
            f"remove={coverage.remove}; "
            f"missing={coverage.missing_papers}; "
            f"audit-records={coverage.audit_records}"
        ),
        f"Errors: {len(result.findings)}",
    ]
    if not result.findings:
        lines.append("No validation errors.")
    else:
        for finding in result.findings:
            lines.append(
                f"ERROR [{finding.code}] {finding.source}:{finding.field}: "
                f"{finding.message}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Validate per-paper evidence records without modifying files."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root containing papers/ and audits/papers/.",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Require one verified or remove decision for every canonical paper.",
    )
    parser.add_argument(
        "--format",
        choices=("human", "json"),
        default="human",
        help="Output format (default: human).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the validator CLI and return zero only when no errors are found."""
    args = _build_parser().parse_args(argv)
    result = validate_audits(args.root, require_complete=args.require_complete)
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(_render_human(result))
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
