#!/usr/bin/env python3
"""Generate a paper YAML stub from an arXiv ID for this repository."""

from __future__ import annotations

import argparse
import sys
import textwrap
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

NS = {"a": "http://www.w3.org/2005/Atom"}
ROOT = Path(__file__).resolve().parents[1]
PAPERS_DIR = ROOT / "papers"
VALID_MECHANISM_TAGS = (
    "hierarchical-loop",
    "flat-loop",
    "parallel-loop",
    "implicit-layer",
)


def yaml_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def clean_text(text: str) -> str:
    return " ".join((text or "").split())


def normalize_iso_date(value: str, field_name: str) -> str:
    try:
        return date.fromisoformat(str(value).strip()).isoformat()
    except ValueError as exc:
        raise SystemExit(f"Invalid {field_name}: {value!r} (expected YYYY-MM-DD)") from exc


def extract_iso_date(value: str) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None

    raw_date = raw.split("T", 1)[0]
    try:
        return date.fromisoformat(raw_date).isoformat()
    except ValueError:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            return None


def wrap_desc(desc: str) -> str:
    wrapped = textwrap.wrap(desc, width=88)
    if not wrapped:
        return "''"
    if len(wrapped) == 1:
        return wrapped[0]
    return wrapped[0] + "\n  " + "\n  ".join(wrapped[1:])


def fetch_arxiv_entry(arxiv_id: str) -> dict:
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": arxiv_id})
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            payload = resp.read()
    except Exception:
        import subprocess

        payload = subprocess.check_output(["curl", "-fsSL", url], timeout=30)
    root = ET.fromstring(payload)
    entry = root.find("a:entry", NS)
    if entry is None:
        raise SystemExit(f"No arXiv entry found for {arxiv_id}")
    published = entry.findtext("a:published", default="", namespaces=NS)
    published_date = extract_iso_date(published)
    if not published_date:
        raise SystemExit(f"Missing usable published_date in arXiv metadata for {arxiv_id}: {published!r}")
    return {
        "title": clean_text(entry.findtext("a:title", default="", namespaces=NS)),
        "authors": [a.findtext("a:name", default="", namespaces=NS) for a in entry.findall("a:author", NS)],
        "year": int(published_date[:4]),
        "published_date": published_date,
        "summary": clean_text(entry.findtext("a:summary", default="", namespaces=NS)),
        "id": entry.findtext("a:id", default="", namespaces=NS).split("/abs/")[-1].split("v")[0],
    }


def first_sentence(summary: str) -> str:
    parts = summary.split(". ")
    sentence = parts[0].strip()
    if not sentence.endswith("."):
        sentence += "."
    return sentence


def render_yaml(data: dict, args: argparse.Namespace) -> str:
    lines: list[str] = []
    lines.append(f"title: {yaml_quote(data['title'])}")
    lines.append("authors:")
    for author in data["authors"]:
        lines.append(f"- {yaml_quote(author)}")
    lines.append(f"year: {data['year']}")
    if data.get("published_date"):
        lines.append(f"published_date: {yaml_quote(data['published_date'])}")
    if args.added_date:
        lines.append(f"added_date: {yaml_quote(args.added_date)}")
    lines.append(f"venue: {args.venue}")
    lines.append(f"category: {args.category}")
    lines.append("mechanism_tags:")
    for item in args.mechanism_tags:
        lines.append(f"- {item}")
    if args.domain_tags:
        lines.append("domain_tags:")
        for item in args.domain_tags:
            lines.append(f"- {item}")
    if args.tags:
        lines.append("tags:")
        for item in args.tags:
            lines.append(f"- {item}")
    desc = args.desc or first_sentence(data["summary"])
    lines.append(f"desc: {wrap_desc(desc)}")
    lines.append("links:")
    lines.append(f"  arxiv: https://arxiv.org/abs/{data['id']}")
    lines.append("citations: 0")
    if args.metrics_updated:
        lines.append(f"metrics_updated: {yaml_quote(args.metrics_updated)}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("arxiv_id", help="arXiv ID, e.g. 2604.11791")
    p.add_argument("--venue", default="arXiv")
    p.add_argument("--category", required=True, choices=["analysis", "designs", "applications"])
    p.add_argument("--mechanism-tag", action="append", required=True, choices=VALID_MECHANISM_TAGS, dest="mechanism_tags")
    p.add_argument("--domain-tag", action="append", default=[], dest="domain_tags")
    p.add_argument("--tag", action="append", default=[], dest="tags")
    p.add_argument("--desc", help="Curated one-line description; defaults to first abstract sentence")
    p.add_argument("--added-date", default=date.today().isoformat(), help="Repo intake date in YYYY-MM-DD; defaults to today")
    p.add_argument("--metrics-updated", help="Optional YYYY-MM-DD stamp")
    p.add_argument("--output", help="Optional custom output path")
    p.add_argument("--force", action="store_true", help="Overwrite existing file")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.added_date:
        args.added_date = normalize_iso_date(args.added_date, "--added-date")
    if args.metrics_updated:
        args.metrics_updated = normalize_iso_date(args.metrics_updated, "--metrics-updated")
    data = fetch_arxiv_entry(args.arxiv_id)
    output = Path(args.output) if args.output else PAPERS_DIR / f"{data['id']}.yaml"
    if output.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing file: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_yaml(data, args), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
