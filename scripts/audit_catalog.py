#!/usr/bin/env python3
"""Read-only structural auditor for canonical ``papers/*.yaml`` records."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Literal, Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import yaml

try:
    from scripts.build import CATEGORIES, VALID_FOCUS_TAGS, VALID_MECHANISM_TAGS
except ModuleNotFoundError:  # Support ``python scripts/audit_catalog.py``.
    from build import CATEGORIES, VALID_FOCUS_TAGS, VALID_MECHANISM_TAGS


REPO_ROOT = Path(__file__).resolve().parents[1]
DESC_LENGTH_LIMIT = 320
REQUIRED_FIELDS = (
    "title",
    "authors",
    "year",
    "published_date",
    "venue",
    "category",
    "mechanism_tags",
    "domain_tags",
    "focus_tags",
    "desc",
    "links",
)
ALLOWED_FIELDS = frozenset(
    REQUIRED_FIELDS
    + (
        "added_date",
        "citation_source_best",
        "citation_sources",
        "citations",
        "foundation",
        "github_stars",
        "metrics_updated",
        "must_read",
        "star_source_best",
        "star_sources",
        "tags",
    )
)
TAG_FIELDS = ("mechanism_tags", "domain_tags", "focus_tags", "tags")
PRIMARY_LINK_FIELDS = ("arxiv", "paper", "openreview")
ARXIV_FILENAME_RE = re.compile(r"^(\d{4}\.\d{4,5})$")
ARXIV_URL_RE = re.compile(
    r"^https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?(?:[?#].*)?$",
    re.IGNORECASE,
)
Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class Finding:
    """One deterministic catalog finding suitable for human or JSON output."""

    severity: Severity
    code: str
    source: str
    field: str
    message: str

    def __post_init__(self) -> None:
        """Reject severity values outside the public two-level contract."""
        if self.severity not in {"error", "warning"}:
            raise ValueError(f"unsupported finding severity: {self.severity!r}")


def _finding_sort_key(finding: Finding) -> tuple[str, str, int, str, str]:
    """Return the stable ordering key shared by both output formats."""
    severity_rank = 0 if finding.severity == "error" else 1
    return (
        finding.source,
        finding.field,
        severity_rank,
        finding.code,
        finding.message,
    )


def _add(
    findings: list[Finding],
    severity: Severity,
    code: str,
    source: str,
    field: str,
    message: str,
) -> None:
    """Append one typed finding while keeping validation call sites concise."""
    findings.append(Finding(severity, code, source, field, message))


def _normalize_tag(value: str) -> str:
    """Normalize a raw tag for duplicate and cross-axis comparison only."""
    normalized = value.strip().lower().replace("_", "-").replace(" ", "-")
    return re.sub(r"-+", "-", normalized).strip("-")


def _normalize_title(value: str) -> str:
    """Normalize case, Unicode, punctuation, and whitespace in a paper title."""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.sub(r"[^\w]+", " ", normalized).split())


def _validate_scalar_fields(data: dict, source: str, findings: list[Finding]) -> None:
    """Validate required scalar and author fields without normalizing raw values."""
    for field in REQUIRED_FIELDS:
        if field not in data:
            _add(findings, "error", "missing-field", source, field, "Required field is missing.")

    for field in ("title", "venue", "category", "desc"):
        if field not in data:
            continue
        value = data[field]
        if not isinstance(value, str):
            _add(
                findings,
                "error",
                "invalid-field-type",
                source,
                field,
                f"Expected a non-empty string; got {type(value).__name__}.",
            )
        elif not value.strip():
            _add(findings, "error", "empty-field", source, field, "Expected a non-empty string.")

    if "year" in data and (not isinstance(data["year"], int) or isinstance(data["year"], bool)):
        _add(
            findings,
            "error",
            "invalid-field-type",
            source,
            "year",
            f"Expected an integer; got {type(data['year']).__name__}.",
        )

    if "authors" in data:
        authors = data["authors"]
        if not isinstance(authors, list):
            _add(
                findings,
                "error",
                "invalid-field-type",
                source,
                "authors",
                f"Expected a list of non-empty strings; got {type(authors).__name__}.",
            )
        else:
            if not authors:
                _add(findings, "error", "empty-field", source, "authors", "Expected at least one author.")
            for index, author in enumerate(authors):
                if not isinstance(author, str) or not author.strip():
                    _add(
                        findings,
                        "error",
                        "invalid-list-item",
                        source,
                        f"authors[{index}]",
                        "Expected a non-empty string.",
                    )

    category = data.get("category")
    if isinstance(category, str) and category.strip() and category not in CATEGORIES:
        expected = ", ".join(sorted(CATEGORIES))
        _add(
            findings,
            "error",
            "invalid-category",
            source,
            "category",
            f"Expected one of {expected}; got {category!r}.",
        )


def _parse_iso_date(
    data: dict,
    field: str,
    source: str,
    findings: list[Finding],
) -> date | None:
    """Validate one present raw date as a quoted ISO string and return it."""
    if field not in data:
        return None
    value = data[field]
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        _add(
            findings,
            "error",
            "invalid-date",
            source,
            field,
            "Expected a quoted ISO date in YYYY-MM-DD form.",
        )
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        _add(
            findings,
            "error",
            "invalid-date",
            source,
            field,
            f"Invalid calendar date {value!r}; expected YYYY-MM-DD.",
        )
        return None


def _validate_dates(data: dict, source: str, findings: list[Finding]) -> None:
    """Validate canonical dates and warn when year disagrees with publication date."""
    published_date = _parse_iso_date(data, "published_date", source, findings)
    for field in ("added_date", "metrics_updated"):
        _parse_iso_date(data, field, source, findings)
    year = data.get("year")
    if published_date is not None and isinstance(year, int) and not isinstance(year, bool):
        if year != published_date.year:
            _add(
                findings,
                "warning",
                "year-date-mismatch",
                source,
                "year",
                f"year is {year} but published_date starts with {published_date.year}.",
            )


def _valid_http_url(value: str) -> bool:
    """Return whether ``value`` is an absolute HTTP(S) URL."""
    parsed = urlsplit(value)
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def _validate_comment_links(value: object, source: str, field: str, findings: list[Finding]) -> None:
    """Validate URL-bearing values in the supported comment link shapes."""
    items = value if isinstance(value, list) else [value]
    for index, item in enumerate(items):
        item_field = f"{field}[{index}]" if isinstance(value, list) else field
        if isinstance(item, str):
            url = item
            url_field = item_field
        elif isinstance(item, dict):
            url = item.get("url")
            url_field = f"{item_field}.url"
        else:
            _add(findings, "error", "invalid-link-type", source, item_field, "Expected a URL string or mapping.")
            continue
        if not isinstance(url, str):
            _add(findings, "error", "invalid-link-type", source, url_field, "Expected a URL string.")
        elif url.strip() and not _valid_http_url(url.strip()):
            _add(findings, "error", "invalid-url", source, url_field, "Expected an absolute http:// or https:// URL.")


def _validate_links(data: dict, source: str, findings: list[Finding]) -> dict | None:
    """Validate the raw links mapping, URL schemes, and primary-link presence."""
    if "links" not in data:
        return None
    links = data["links"]
    if not isinstance(links, dict):
        _add(
            findings,
            "error",
            "invalid-links-type",
            source,
            "links",
            f"Expected a mapping; got {type(links).__name__}.",
        )
        return None

    for key in sorted(links, key=str):
        value = links[key]
        field = f"links.{key}"
        if key in {"comment", "comments"}:
            _validate_comment_links(value, source, field, findings)
            continue
        if value is None or value == "":
            continue
        if not isinstance(value, str):
            _add(findings, "error", "invalid-link-type", source, field, "Expected a URL string.")
        elif not _valid_http_url(value.strip()):
            _add(findings, "error", "invalid-url", source, field, "Expected an absolute http:// or https:// URL.")

    if not any(isinstance(links.get(key), str) and links[key].strip() for key in PRIMARY_LINK_FIELDS):
        _add(
            findings,
            "error",
            "missing-primary-link",
            source,
            "links",
            "Expected at least one of links.arxiv, links.paper, or links.openreview.",
        )
    return links


def _arxiv_id_from_url(value: object) -> str | None:
    """Extract a canonical modern arXiv ID from a raw arXiv URL."""
    if not isinstance(value, str):
        return None
    match = ARXIV_URL_RE.fullmatch(value.strip())
    return match.group(1) if match else None


def _validate_arxiv_identity(path: Path, links: dict | None, source: str, findings: list[Finding]) -> None:
    """Require filename and arXiv link IDs to be present together and equal."""
    filename_match = ARXIV_FILENAME_RE.fullmatch(path.stem)
    filename_id = filename_match.group(1) if filename_match else None
    raw_url = links.get("arxiv") if links else None
    link_id = _arxiv_id_from_url(raw_url)

    if isinstance(raw_url, str) and raw_url.strip() and link_id is None:
        _add(
            findings,
            "error",
            "invalid-arxiv-id",
            source,
            "links.arxiv",
            "Expected an arxiv.org abs/pdf URL containing a modern arXiv ID.",
        )
        return
    if filename_id == link_id:
        return
    if filename_id and not link_id:
        message = f"Filename encodes arXiv ID {filename_id}, but links.arxiv is missing."
    elif link_id and not filename_id:
        message = f"links.arxiv encodes {link_id}, but the filename does not encode that ID."
    else:
        message = f"Filename encodes {filename_id}, but links.arxiv encodes {link_id}."
    _add(findings, "error", "arxiv-id-mismatch", source, "links.arxiv", message)


def _validate_tags(data: dict, source: str, findings: list[Finding]) -> None:
    """Validate tag list shape, duplicates, controlled values, and axis collisions."""
    normalized_by_field: dict[str, list[tuple[int, str]]] = {}
    for field in TAG_FIELDS:
        if field not in data:
            continue
        value = data[field]
        if not isinstance(value, list):
            _add(
                findings,
                "error",
                "invalid-tag-list",
                source,
                field,
                f"Expected a list of non-empty strings; got {type(value).__name__}.",
            )
            continue
        seen: set[str] = set()
        normalized_items: list[tuple[int, str]] = []
        for index, item in enumerate(value):
            item_field = f"{field}[{index}]"
            if not isinstance(item, str):
                _add(findings, "error", "invalid-tag", source, item_field, "Expected a non-empty string.")
                continue
            tag = _normalize_tag(item)
            if not tag:
                _add(findings, "error", "empty-tag", source, item_field, "Expected a non-empty string.")
                continue
            if tag in seen:
                _add(findings, "error", "duplicate-tag", source, item_field, f"Duplicate tag {item!r} within {field}.")
            else:
                seen.add(tag)
            normalized_items.append((index, tag))
            if field == "mechanism_tags" and item not in VALID_MECHANISM_TAGS:
                _add(findings, "error", "invalid-mechanism-tag", source, item_field, f"Unknown controlled mechanism tag {item!r}.")
            if field == "focus_tags" and item not in VALID_FOCUS_TAGS:
                _add(findings, "error", "invalid-focus-tag", source, item_field, f"Unknown controlled focus tag {item!r}.")
        normalized_by_field[field] = normalized_items

    controlled = set(VALID_MECHANISM_TAGS) | set(VALID_FOCUS_TAGS)
    for index, tag in normalized_by_field.get("domain_tags", []):
        if tag in controlled:
            _add(
                findings,
                "warning",
                "cross-axis-tag-collision",
                source,
                f"domain_tags[{index}]",
                f"Domain tag {tag!r} belongs to a controlled mechanism/focus axis.",
            )
    selected_browser_tags = {
        tag
        for field in ("mechanism_tags", "domain_tags", "focus_tags")
        for _, tag in normalized_by_field.get(field, [])
    }
    for index, tag in normalized_by_field.get("tags", []):
        if tag in controlled or tag in selected_browser_tags:
            _add(
                findings,
                "warning",
                "cross-axis-tag-collision",
                source,
                f"tags[{index}]",
                f"Alias tag {tag!r} duplicates a browser-facing tag axis.",
            )


def _validate_description(data: dict, source: str, findings: list[Finding]) -> None:
    """Apply non-blocking length and sentence-count guidance to descriptions."""
    desc = data.get("desc")
    if not isinstance(desc, str):
        return
    if len(desc.strip()) > DESC_LENGTH_LIMIT:
        _add(
            findings,
            "warning",
            "desc-too-long",
            source,
            "desc",
            f"Description is longer than the {DESC_LENGTH_LIMIT}-character soft limit.",
        )
    if re.search(r"[.!?][\"')\]]*\s+\S", desc.strip()):
        _add(
            findings,
            "warning",
            "desc-multiple-sentences",
            source,
            "desc",
            "Description appears to contain more than one sentence.",
        )


def _canonical_url(value: str) -> str:
    """Normalize an HTTP URL for deterministic duplicate-source comparison."""
    parsed = urlsplit(value.strip())
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, query, ""))


def _primary_source_id(links: dict | None) -> str | None:
    """Return a canonical arXiv/OpenReview/URL identity for a paper's primary source."""
    if not links:
        return None
    arxiv_id = _arxiv_id_from_url(links.get("arxiv"))
    if arxiv_id:
        return f"arxiv:{arxiv_id}"
    for key in ("paper", "openreview"):
        value = links.get(key)
        if not isinstance(value, str) or not _valid_http_url(value.strip()):
            continue
        parsed = urlsplit(value.strip())
        if parsed.netloc.lower().removeprefix("www.").endswith("openreview.net"):
            openreview_id = dict(parse_qsl(parsed.query)).get("id")
            if openreview_id:
                return f"openreview:{openreview_id}"
        return f"url:{_canonical_url(value)}"
    return None


def _record_duplicates(
    data: dict,
    links: dict | None,
    source: str,
    title_sources: dict[str, str],
    primary_sources: dict[str, str],
    findings: list[Finding],
) -> None:
    """Report normalized title and source duplicates against the first source."""
    title = data.get("title")
    if isinstance(title, str) and title.strip():
        normalized_title = _normalize_title(title)
        first_source = title_sources.setdefault(normalized_title, source)
        if first_source != source:
            _add(findings, "error", "duplicate-title", source, "title", f"Normalized title conflicts with {first_source}.")

    primary_id = _primary_source_id(links)
    if primary_id:
        first_source = primary_sources.setdefault(primary_id, source)
        if first_source != source:
            _add(findings, "error", "duplicate-primary-source", source, "links", f"Canonical primary source {primary_id!r} conflicts with {first_source}.")


def audit_catalog(root: Path = REPO_ROOT) -> list[Finding]:
    """Audit raw canonical paper YAML below ``root`` without modifying any file."""
    root = Path(root)
    papers_dir = root / "papers"
    findings: list[Finding] = []
    if not papers_dir.is_dir():
        return [Finding("error", "missing-papers-directory", "papers", "$", "Required papers directory is missing.")]

    title_sources: dict[str, str] = {}
    primary_sources: dict[str, str] = {}
    for path in sorted(papers_dir.glob("*.yaml"), key=lambda item: item.name):
        if path.name.startswith("_template"):
            continue
        source = f"papers/{path.name}"
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            _add(findings, "error", "yaml-parse", source, "$", "YAML could not be parsed.")
            continue
        if not isinstance(data, dict):
            _add(findings, "error", "top-level-type", source, "$", "Expected a top-level mapping.")
            continue

        for field in sorted(data, key=str):
            if field not in ALLOWED_FIELDS:
                _add(findings, "error", "unknown-field", source, str(field), "Unknown top-level field.")
        _validate_scalar_fields(data, source, findings)
        _validate_dates(data, source, findings)
        links = _validate_links(data, source, findings)
        _validate_arxiv_identity(path, links, source, findings)
        _validate_tags(data, source, findings)
        _validate_description(data, source, findings)
        _record_duplicates(data, links, source, title_sources, primary_sources, findings)

    return sorted(findings, key=_finding_sort_key)


def _serialize(findings: list[Finding]) -> dict:
    """Build the stable JSON output object with counts and full finding records."""
    return {
        "counts": {
            "error": sum(item.severity == "error" for item in findings),
            "warning": sum(item.severity == "warning" for item in findings),
        },
        "findings": [asdict(item) for item in findings],
    }


def _render_human(findings: list[Finding]) -> str:
    """Render a compact human report containing every finding field."""
    payload = _serialize(findings)
    counts = payload["counts"]
    lines = [f"Catalog audit: {counts['error']} error(s), {counts['warning']} warning(s)"]
    lines.extend(
        f"{item.severity.upper()} {item.code} {item.source} {item.field}: {item.message}"
        for item in findings
    )
    if not findings:
        lines.append("No findings.")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for root selection and output format."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Repository root (default: script parent).")
    parser.add_argument("--format", choices=("human", "json"), default="human", help="Output format (default: human).")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the auditor and return one only when at least one error exists."""
    args = build_parser().parse_args(argv)
    findings = audit_catalog(args.root)
    if args.format == "json":
        print(json.dumps(_serialize(findings), indent=2, sort_keys=True))
    else:
        print(_render_human(findings), end="")
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
