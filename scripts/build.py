#!/usr/bin/env python3
"""
build.py — Single-source build script for Awesome Loop Models.

Reads all papers/*.yaml and blogs/*.yaml files and generates:
  1. papers.json   — consumed by index.html
  2. README.md     — the GitHub repository README
  3. TAGS.md       — contributor-facing tag reference

The paper/blog YAML files are the source of truth.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import quote, urlparse

import yaml

REPO_ROOT = Path(__file__).parent.parent
PAPERS_DIR = REPO_ROOT / "papers"
BLOGS_DIR = REPO_ROOT / "blogs"
BRIEFINGS_DIR = REPO_ROOT / "briefings"
JSON_OUT = REPO_ROOT / "papers.json"
README_OUT = REPO_ROOT / "README.md"
TAGS_OUT = REPO_ROOT / "TAGS.md"
HEADER_FILE = Path(__file__).parent / "README_HEADER.md"
FOOTER_FILE = Path(__file__).parent / "README_FOOTER.md"
REPO_META_FILE = REPO_ROOT / "repo_meta.json"
REPO_META_JS_OUT = REPO_ROOT / "assets" / "repo-meta.js"
ISSUE_TEMPLATE_CONFIG_TEMPLATE_FILE = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "config.template.yml"
ISSUE_TEMPLATE_CONFIG_OUT = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml"

VALID_FOCUS_TAGS = (
    "objective-loss",
    "training-algorithm",
    "architecture",
    "data",
    "inference-algorithm",
)

VALID_MECHANISM_TAGS = (
    "hierarchical-loop",
    "flat-loop",
    "parallel-loop",
    "implicit-layer",
)

# Loop Mechanism is a strict browser-facing controlled vocabulary. Legacy paper
# acronyms and fine-grained mechanism labels are metadata aliases only; they are
# not mapped into mechanism_tags by the build.

CATEGORY_DISCLAIMER = (
    "The paper shelves are intentionally coarse: Theoretical and Mechanical Analysis, Architecture and Algorithm Designs, "
    "and Applications Focused. Foundation status plus Loop Mechanism / focus / domain tags carry secondary structure without "
    "introducing lineage buckets."
)
FOUNDATION_LABEL = "Foundation"
BLOG_SECTION_TITLE = "Blogs"
DAILY_BRIEFING_SECTION_TITLE = "Daily Briefing"
DAILY_BRIEFING_SECTION_DESC = (
    "Reader-facing daily research briefings: notable loop-model papers, watchlist candidates, "
    "and concise inclusion rationale."
)
BLOG_SECTION_DESC = (
    "Long-form technical posts, essays, and deep-dives about loop models. Blogs can carry Loop Mechanism / focus / domain tags but stay in a "
    "single flat section rather than the paper taxonomy."
)
BLOG_VENUE_CLASS = "venue-other"
BADGE_STYLE = "flat-square"
LINK_BADGES = {
    "blog": ("Blog", "0ea5e9"),
    "arxiv": ("arXiv", "b31b1b"),
    "alphaxiv": ("AlphaXiv", "7c3aed"),
    "paper": ("Paper", "0366d6"),
    "github": ("GitHub stars", "24292f"),
    "readme": ("README", "0969da"),
    "hf": ("HuggingFace", "ffb000"),
    "openreview": ("OpenReview", "8E44AD"),
    "project": ("Website", "blue"),
    "twitter": ("Twitter", "1d9bf0"),
}


def load_repo_meta() -> dict:
    meta = json.loads(REPO_META_FILE.read_text(encoding="utf-8"))
    required_keys = ("github_owner", "default_repo_name", "public_repo_name")
    missing = [key for key in required_keys if not meta.get(key)]
    if missing:
        raise ValueError(f"repo_meta.json is missing required keys: {', '.join(missing)}")
    meta["public_pages_base"] = f"https://{meta['github_owner']}.github.io/{meta['public_repo_name']}"
    meta["public_github_base"] = f"https://github.com/{meta['github_owner']}/{meta['public_repo_name']}"
    return meta


def render_repo_meta_js(meta: dict) -> str:
    return (
        "window.REPO_META = {\n"
        f"  githubOwner: {json.dumps(meta['github_owner'])},\n"
        f"  defaultRepoName: {json.dumps(meta['default_repo_name'])},\n"
        f"  publicRepoName: {json.dumps(meta['public_repo_name'])},\n"
        f"  publicPagesBase: {json.dumps(meta['public_pages_base'])},\n"
        "  inferRepoNameFromLocation(locationLike = window.location) {\n"
        "    const pathParts = String(locationLike.pathname || '').split('/').filter(Boolean);\n"
        "    const hostname = String(locationLike.hostname || '');\n"
        "    if (hostname.endsWith('github.io') && pathParts.length) return pathParts[0];\n"
        "    if (hostname === 'github.com' && pathParts.length >= 2) return pathParts[1];\n"
        "    return this.defaultRepoName;\n"
        "  },\n"
        "  getGitHubRepoBase(locationLike = window.location) {\n"
        "    return 'https://github.com/' + this.githubOwner + '/' + this.inferRepoNameFromLocation(locationLike);\n"
        "  },\n"
        "  getGitHubBlobUrl(path, locationLike = window.location) {\n"
        "    return this.getGitHubRepoBase(locationLike) + '/blob/main/' + String(path || '').replace(/^\\/+/, '');\n"
        "  },\n"
        "  getGitHubNewFileBase(locationLike = window.location) {\n"
        "    return this.getGitHubRepoBase(locationLike) + '/new/main';\n"
        "  }\n"
        "};\n"
    )


def build_repo_meta_js(meta: dict) -> None:
    REPO_META_JS_OUT.write_text(render_repo_meta_js(meta), encoding="utf-8")


def render_issue_template_config(meta: dict) -> str:
    template = ISSUE_TEMPLATE_CONFIG_TEMPLATE_FILE.read_text(encoding="utf-8")
    return (
        template
        .replace("{{PUBLIC_SUBMIT_URL}}", meta["public_pages_base"] + "/submit.html")
        .replace("{{PUBLIC_TAGS_URL}}", meta["public_github_base"] + "/blob/main/TAGS.md")
    )


def build_issue_template_config(meta: dict) -> None:
    ISSUE_TEMPLATE_CONFIG_OUT.write_text(render_issue_template_config(meta), encoding="utf-8")

VENUE_CLASSES = {
    "NeurIPS": "venue-neurips",
    "ICLR": "venue-iclr",
    "ICML": "venue-icml",
    "ACL": "venue-acl",
    "CoLM": "venue-colm",
    "LoG": "venue-log",
    "arXiv": "venue-arxiv",
}

def category_node(title: str, desc: str | None = None, children: dict | None = None) -> dict:
    node = {"title": title, "children": children or {}}
    if desc:
        node["desc"] = desc
    return node


CATEGORIES = {
    "analysis": {
        "id": "analysis",
        "title": "Theoretical and Mechanical Analysis",
        "icon": "🔬",
        "desc": "Analytical papers whose main artifact is understanding loop models: theory, mechanism analysis, diagnostics, formal properties, or interpretability.",
        "readme_intro": (
            "Theoretical and Mechanical Analysis collects papers whose primary contribution is analysis: why loop models work, what formal properties they have, and what mechanisms they exhibit."
        ),
        "children": {},
    },
    "designs": {
        "id": "designs",
        "title": "Architecture and Algorithm Designs",
        "icon": "🏗️",
        "desc": "Papers that propose loop-model architectures or algorithms, often to improve performance, efficiency, training, inference, or memory use.",
        "readme_intro": (
            "Architecture and Algorithm Designs collects the constructive side of the field: new looped architectures, algorithms, recurrent computation graphs, and efficiency or memory-compression methods."
        ),
        "children": {},
    },
    "applications": {
        "id": "applications",
        "title": "Applications Focused",
        "icon": "🧪",
        "desc": "Papers whose main reader takeaway is evidence that loop models work in a specific external domain or task, such as robotics, VLA, multimodal, tabular, or graph data.",
        "readme_intro": (
            "Applications Focused collects papers centered on applying loop models to concrete domains or tasks, including robotics, VLA, multimodal settings, tabular data, graph data, and other non-core benchmarks."
        ),
        "children": {},
    },
}


def normalize_str_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = [str(item) for item in value if item is not None]
    else:
        raise ValueError(f"expected string or list, got {type(value).__name__}")

    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        item = raw.strip()
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def normalize_tag_slug(raw_tag: str) -> str:
    tag = re.sub(r"[^a-z0-9-]+", "-", raw_tag.strip().lower().replace("_", "-").replace(" ", "-"))
    return re.sub(r"-+", "-", tag).strip("-")


def normalize_mechanism_tags(raw_mechanism_tags: object, source: str) -> list[str]:
    raw_tags = normalize_str_list(raw_mechanism_tags)
    out: list[str] = []
    seen: set[str] = set()
    invalid: list[str] = []
    for raw_tag in raw_tags:
        tag = normalize_tag_slug(raw_tag)
        if not tag:
            continue
        if tag not in VALID_MECHANISM_TAGS:
            invalid.append(raw_tag)
            continue
        if tag in seen:
            continue
        seen.add(tag)
        out.append(tag)
    if invalid:
        raise ValueError(
            f"{source}: invalid mechanism_tags {invalid!r}; valid values are {list(VALID_MECHANISM_TAGS)!r}"
        )
    return out


def merge_mechanism_tags(*groups: object) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for raw_tag in normalize_str_list(group):
            tag = normalize_tag_slug(raw_tag)
            # Only canonical Loop Mechanism values are merged. Older acronyms or
            # fine-grained labels stay in alias/domain metadata and are not mapped.
            if tag not in VALID_MECHANISM_TAGS or tag in seen:
                continue
            seen.add(tag)
            merged.append(tag)
    return merged


def split_domain_and_mechanism_tags(raw_domain_tags: object) -> tuple[list[str], list[str]]:
    return normalize_str_list(raw_domain_tags), []


def normalize_category_segment(segment: object) -> str:
    value = str(segment or "").strip().lower()
    if not value:
        return ""
    return value.replace("-", "_")



def has_non_empty_metadata_value(raw_value: object) -> bool:
    if raw_value is None:
        return False
    if isinstance(raw_value, str):
        return bool(raw_value.strip())
    if isinstance(raw_value, (list, tuple, set)):
        return any(has_non_empty_metadata_value(item) for item in raw_value)
    if isinstance(raw_value, dict):
        return bool(raw_value)
    return True


def normalize_bool_flag(raw_value: object) -> bool:
    if isinstance(raw_value, bool):
        return raw_value
    if raw_value is None:
        return False
    return str(raw_value).strip().lower() in {"1", "true", "yes", "y"}


def normalize_foundation_flag(raw_foundation: object) -> bool:
    return normalize_bool_flag(raw_foundation)


def normalize_must_read_flag(raw_must_read: object) -> bool:
    return normalize_bool_flag(raw_must_read)


def normalize_paper_taxonomy_fields(paper: dict, source: str = "<paper>") -> dict:
    raw_category = normalize_category_segment(paper.get("category"))
    if not raw_category:
        raise ValueError(f"{source}: missing category")
    if raw_category not in CATEGORIES:
        raise ValueError(
            f"{source}: invalid category '{raw_category}'; valid values are {list(CATEGORIES.keys())!r}"
        )
    if has_non_empty_metadata_value(paper.get("category_path")):
        raise ValueError(f"{source}: category_path is no longer supported; use the flat category field only")
    if has_non_empty_metadata_value(paper.get("subcategory")):
        raise ValueError(f"{source}: subcategory is no longer supported; use the flat category field only")

    return {
        "category": raw_category,
        "foundation": normalize_foundation_flag(paper.get("foundation")),
    }



def canonicalize_paper_category_fields(paper: dict) -> tuple[str, list[str]]:
    normalized = normalize_paper_taxonomy_fields(paper)
    return normalized["category"], []



def validate_paper_category_fields(paper: dict, source: str = "<paper>") -> list[str]:
    normalize_paper_taxonomy_fields(paper, source)
    return []



def paper_full_category_path(paper: dict) -> tuple[str, ...]:
    normalized = normalize_paper_taxonomy_fields(paper)
    return (normalized["category"],)


def iter_category_tree():
    for category_id, category in CATEGORIES.items():
        yield category_id, category


def iter_child_nodes(node: dict):
    for child_id, child in node.get("children", {}).items():
        yield child_id, child


def heading_anchor(text: str) -> str:
    return (
        text.lower()
        .replace(" ", "-")
        .replace("/", "")
        .replace("(", "")
        .replace(")", "")
        .replace("&", "")
        .replace(".", "")
        .replace(",", "")
    )


def get_arxiv_id(filename: str) -> str | None:
    stem = Path(filename).stem
    match = re.match(r"^(\d{4}\.\d{4,5})", stem)
    return match.group(1) if match else None


def get_arxiv_id_from_url(url: str) -> str | None:
    if not url:
        return None
    match = re.search(r"(?:arxiv\.org/(?:abs|pdf)|alphaxiv\.org/abs)/(\d{4}\.\d{4,5})(?:v\d+)?", url)
    return match.group(1) if match else None


def _repo_slug_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.netloc:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc.endswith("github.com") and len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    if parsed.netloc.endswith("huggingface.co") and parts:
        return "/".join(parts[:2]) if len(parts) >= 2 else parts[0]
    return None


def _hostname_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.strip().lower()
    if not host:
        return None
    return host.removeprefix("www.")


def _openreview_id_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.netloc.endswith("openreview.net"):
        return None
    query = parsed.query or ""
    match = re.search(r"(?:^|&)id=([^&]+)", query)
    if match:
        return match.group(1)
    return None


def _is_openreview_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.endswith("openreview.net")


def _github_stargazers_url(url: str) -> str | None:
    repo_slug = _repo_slug_from_url(url)
    if not repo_slug:
        return None
    return f"https://github.com/{repo_slug}/stargazers"


def shields_escape(text: str) -> str:
    return text.replace("_", "__").replace("-", "--").replace(" ", "_")


def badge_message_for_link(key: str, url: str) -> str | None:
    if key in {"arxiv", "alphaxiv"}:
        return get_arxiv_id_from_url(url)
    if key == "twitter":
        parsed = urlparse(url)
        parts = [part for part in parsed.path.split("/") if part]
        if parts and parts[0] not in {"home", "intent", "share", "search", "i"}:
            return f"@{parts[0].lstrip('@')}"
        return _hostname_from_url(url)
    if key in {"github", "hf", "readme"}:
        return _repo_slug_from_url(url) or _hostname_from_url(url)
    if key == "openreview":
        return _openreview_id_from_url(url) or _hostname_from_url(url)
    if key in {"project", "paper", "blog"}:
        return _hostname_from_url(url)
    return None


def normalize_comment_links(raw_comment: object) -> list[dict]:
    if not raw_comment:
        return []

    if isinstance(raw_comment, (str, dict)):
        items = [raw_comment]
    elif isinstance(raw_comment, list):
        items = raw_comment
    else:
        return []

    rows: list[tuple[str, str]] = []
    for item in items:
        label = ""
        url = ""
        if isinstance(item, str):
            url = item.strip()
        elif isinstance(item, dict):
            raw_url = item.get("url", "")
            raw_label = item.get("label", "")
            url = str(raw_url).strip() if raw_url is not None else ""
            label = str(raw_label).strip() if raw_label is not None else ""
        if url:
            rows.append((label, url))

    if not rows:
        return []

    multi = len(rows) > 1
    out = []
    for idx, (label, url) in enumerate(rows, start=1):
        out.append({
            "label": label or (f"Comment {idx}" if multi else "Comment"),
            "url": url,
        })
    return out


def validate_links(links: dict, source: str) -> None:
    if not isinstance(links, dict):
        raise ValueError(f"{source}: links must be a mapping")
    if not any(links.get(key) for key in ("arxiv", "paper", "openreview")):
        raise ValueError(f"{source}: at least one of links.arxiv, links.paper, or links.openreview is required")


# Blogs are intentionally flat metadata entries: they need a canonical public blog URL,
# but they do not participate in the paper taxonomy.
def validate_blog_links(links: dict, source: str) -> None:
    if not isinstance(links, dict):
        raise ValueError(f"{source}: links must be a mapping")
    if not links.get("blog"):
        raise ValueError(f"{source}: blogs require links.blog")


def normalize_venue_class(venue: str, entry_type: str) -> str:
    if entry_type == "blog":
        return BLOG_VENUE_CLASS
    return VENUE_CLASSES.get(venue, "venue-arxiv")


def normalize_focus_tags(raw_focus_tags: object, source: str) -> list[str]:
    focus_tags = normalize_str_list(raw_focus_tags)
    invalid = [tag for tag in focus_tags if tag not in VALID_FOCUS_TAGS]
    if invalid:
        raise ValueError(
            f"{source}: invalid focus_tags {invalid!r}; valid values are {list(VALID_FOCUS_TAGS)!r}"
        )
    return focus_tags


def split_focus_and_mechanism_tags(raw_focus_tags: object, source: str) -> tuple[list[str], list[str]]:
    return normalize_focus_tags(raw_focus_tags, source), []


def normalize_authors(raw_authors: object) -> tuple[list[str], str]:
    authors = normalize_str_list(raw_authors)
    return authors, ", ".join(authors)


DATE_FIELD_NAMES = {"published_date", "added_date"}


def normalize_optional_date_string(raw_value: object, field_name: str, source: str) -> str | None:
    if field_name not in DATE_FIELD_NAMES:
        raise ValueError(f"{source}: unsupported date field {field_name!r}")
    if raw_value is None or raw_value == "":
        return None
    if isinstance(raw_value, datetime):
        value = raw_value.date().isoformat()
    elif isinstance(raw_value, date):
        value = raw_value.isoformat()
    else:
        value = str(raw_value).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"{source}: invalid {field_name} {value!r}; expected YYYY-MM-DD")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"{source}: invalid {field_name} {value!r}; expected YYYY-MM-DD") from exc


def normalize_required_date_string(raw_value: object, field_name: str, source: str) -> str:
    value = normalize_optional_date_string(raw_value, field_name, source)
    if value is None:
        raise ValueError(f"{source}: missing required {field_name}")
    return value


def load_papers() -> list[dict]:
    papers = []
    for yaml_file in sorted(PAPERS_DIR.glob("*.yaml")):
        if yaml_file.name.startswith("_"):
            continue

        data = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
        taxonomy = normalize_paper_taxonomy_fields(data, yaml_file.name)
        category_id = taxonomy["category"]
        foundation = taxonomy["foundation"]

        links = dict(data.get("links") or {})
        validate_links(links, yaml_file.name)
        comments = normalize_comment_links(links.get("comment") or links.get("comments"))
        links = {k: v for k, v in links.items() if v and k not in {"comment", "comments"}}

        arxiv_id_from_link = get_arxiv_id_from_url(links.get("arxiv", ""))
        if arxiv_id_from_link and "alphaxiv" not in links:
            links["alphaxiv"] = f"https://www.alphaxiv.org/abs/{arxiv_id_from_link}"

        authors_list, authors_text = normalize_authors(data.get("authors", []))
        if has_non_empty_metadata_value(data.get("family_tags")):
            raise ValueError(f"{yaml_file.name}: family_tags is no longer supported; use tags or mechanism_tags")
        focus_tags, _ = split_focus_and_mechanism_tags(data.get("focus_tags", []), yaml_file.name)
        tags = normalize_str_list(data.get("tags", []))
        domain_tags, _ = split_domain_and_mechanism_tags(data.get("domain_tags", []))
        explicit_mechanism_tags = normalize_mechanism_tags(data.get("mechanism_tags", []), yaml_file.name)
        if not explicit_mechanism_tags:
            raise ValueError(
                f"{yaml_file.name}: missing mechanism_tags; choose at least one of {list(VALID_MECHANISM_TAGS)!r}"
            )
        mechanism_tags = merge_mechanism_tags(explicit_mechanism_tags)
        published_date = normalize_required_date_string(data.get("published_date"), "published_date", yaml_file.name)
        added_date = normalize_optional_date_string(data.get("added_date"), "added_date", yaml_file.name)
        must_read = normalize_must_read_flag(data.get("must_read"))

        paper = dict(data)
        paper.pop("family_tags", None)
        paper["id"] = yaml_file.stem
        paper["source_file"] = yaml_file.name
        paper["source_path"] = f"papers/{yaml_file.name}"
        paper["entry_type"] = "paper"
        paper["category"] = category_id
        paper["foundation"] = foundation
        paper["links"] = links
        paper["tags"] = tags
        paper["mechanism_tags"] = mechanism_tags
        paper["domain_tags"] = domain_tags
        paper["focus_tags"] = focus_tags
        paper["authors_list"] = authors_list
        paper["authors"] = authors_text
        paper["published_date"] = published_date
        if must_read:
            paper["must_read"] = True
        else:
            paper.pop("must_read", None)
        if added_date is not None:
            paper["added_date"] = added_date
        else:
            paper.pop("added_date", None)
        paper["venueClass"] = normalize_venue_class(str(paper.get("venue", "")), "paper")

        file_arxiv_id = get_arxiv_id(yaml_file.name)
        if file_arxiv_id:
            paper["arxiv_id"] = file_arxiv_id
        elif arxiv_id_from_link:
            paper["arxiv_id"] = arxiv_id_from_link

        if comments:
            paper["community_comments"] = comments
            paper["comments"] = comments

        papers.append(paper)
    return papers


# Blogs live in a separate flat section. They share tag/date/link metadata with papers
# but intentionally skip category/category_path/foundation classification.
def load_blogs() -> list[dict]:
    if not BLOGS_DIR.exists():
        return []

    blogs = []
    for yaml_file in sorted(BLOGS_DIR.glob("*.yaml")):
        if yaml_file.name.startswith("_"):
            continue

        data = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
        links = dict(data.get("links") or {})
        validate_blog_links(links, yaml_file.name)
        comments = normalize_comment_links(links.get("comment") or links.get("comments"))
        links = {k: v for k, v in links.items() if v and k not in {"comment", "comments"}}

        authors_list, authors_text = normalize_authors(data.get("authors", []))
        if has_non_empty_metadata_value(data.get("family_tags")):
            raise ValueError(f"{yaml_file.name}: family_tags is no longer supported; use tags or mechanism_tags")
        focus_tags, _ = split_focus_and_mechanism_tags(data.get("focus_tags", []), yaml_file.name)
        tags = normalize_str_list(data.get("tags", []))
        domain_tags, _ = split_domain_and_mechanism_tags(data.get("domain_tags", []))
        explicit_mechanism_tags = normalize_mechanism_tags(data.get("mechanism_tags", []), yaml_file.name)
        if not explicit_mechanism_tags:
            raise ValueError(
                f"{yaml_file.name}: missing mechanism_tags; choose at least one of {list(VALID_MECHANISM_TAGS)!r}"
            )
        mechanism_tags = merge_mechanism_tags(explicit_mechanism_tags)
        published_date = normalize_required_date_string(data.get("published_date"), "published_date", yaml_file.name)
        added_date = normalize_optional_date_string(data.get("added_date"), "added_date", yaml_file.name)
        must_read = normalize_must_read_flag(data.get("must_read"))

        blog = dict(data)
        blog.pop("family_tags", None)
        blog["id"] = yaml_file.stem
        blog["source_file"] = yaml_file.name
        blog["source_path"] = f"blogs/{yaml_file.name}"
        blog["entry_type"] = "blog"
        blog["links"] = links
        blog["tags"] = tags
        blog["mechanism_tags"] = mechanism_tags
        blog["domain_tags"] = domain_tags
        blog["focus_tags"] = focus_tags
        blog["authors_list"] = authors_list
        blog["authors"] = authors_text
        blog["published_date"] = published_date
        if must_read:
            blog["must_read"] = True
        else:
            blog.pop("must_read", None)
        if added_date is not None:
            blog["added_date"] = added_date
        else:
            blog.pop("added_date", None)
        blog["venueClass"] = normalize_venue_class(str(blog.get("venue", "")), "blog")

        if comments:
            blog["community_comments"] = comments
            blog["comments"] = comments

        blogs.append(blog)
    return blogs


def split_markdown_frontmatter(text: str, source: str) -> tuple[dict, str]:
    """Return YAML frontmatter metadata and the Markdown body for a briefing file."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        raise ValueError(f"{source}: frontmatter starts with --- but has no closing ---")
    frontmatter_text = text[4:end].strip()
    body_start = end + len("\n---")
    if text[body_start:body_start + 2] == "\r\n":
        body_start += 2
    elif text[body_start:body_start + 1] == "\n":
        body_start += 1
    metadata = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(metadata, dict):
        raise ValueError(f"{source}: frontmatter must be a mapping")
    return metadata, text[body_start:].strip()


def normalize_briefing_date(raw_value: object, source: str) -> str:
    """Normalize the required briefing date from YAML or string input."""
    if raw_value is None or raw_value == "":
        raise ValueError(f"{source}: missing required date")
    if isinstance(raw_value, datetime):
        value = raw_value.date().isoformat()
    elif isinstance(raw_value, date):
        value = raw_value.isoformat()
    else:
        value = str(raw_value).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"{source}: invalid date {value!r}; expected YYYY-MM-DD")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"{source}: invalid date {value!r}; expected YYYY-MM-DD") from exc


def normalize_briefing_candidates(raw_candidates: object, source: str) -> list[dict]:
    """Normalize optional candidate rows from a daily briefing frontmatter block."""
    if raw_candidates is None:
        return []
    if not isinstance(raw_candidates, list):
        raise ValueError(f"{source}: candidates must be a list")
    candidates = []
    for idx, raw_candidate in enumerate(raw_candidates, start=1):
        if not isinstance(raw_candidate, dict):
            raise ValueError(f"{source}: candidates[{idx}] must be a mapping")
        candidate = {
            str(key): str(value).strip()
            for key, value in raw_candidate.items()
            if value is not None and str(value).strip()
        }
        if candidate:
            candidates.append(candidate)
    return candidates


def load_briefings() -> list[dict]:
    """Load daily Markdown briefings stored as briefings/YYYY/MM/YYYY-MM-DD.md."""
    if not BRIEFINGS_DIR.exists():
        return []

    briefings = []
    for markdown_file in sorted(BRIEFINGS_DIR.glob("*/*/*.md")):
        if markdown_file.name.startswith("_"):
            continue
        try:
            source_path = markdown_file.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            source_path = markdown_file.relative_to(BRIEFINGS_DIR.parent).as_posix()
        metadata, body = split_markdown_frontmatter(markdown_file.read_text(encoding="utf-8"), source_path)
        briefing_date = normalize_briefing_date(metadata.get("date") or markdown_file.stem, source_path)
        expected_relative_path = f"briefings/{briefing_date[:4]}/{briefing_date[5:7]}/{briefing_date}.md"
        if source_path != expected_relative_path:
            raise ValueError(f"{source_path}: expected path {expected_relative_path}")

        highlights = normalize_str_list(metadata.get("highlights", []))
        candidates = normalize_briefing_candidates(metadata.get("candidates", []), source_path)
        briefing = {
            "date": briefing_date,
            "title": str(metadata.get("title") or f"Daily Loop-Model Watch — {briefing_date}").strip(),
            "status": str(metadata.get("status") or "ok").strip(),
            "summary": str(metadata.get("summary") or "").strip(),
            "highlights": highlights,
            "candidates": candidates,
            "content": body,
            "source_path": source_path,
        }
        briefings.append(briefing)

    return sorted(briefings, key=lambda item: item["date"], reverse=True)


def build_json(papers: list[dict], blogs: list[dict], briefings: list[dict] | None = None) -> None:
    briefings = sorted(briefings or [], key=lambda item: item.get("date", ""), reverse=True)
    payload = {
        "meta": {
            "total": len(papers) + len(blogs),
            "paper_total": len(papers),
            "blog_total": len(blogs),
            "briefing_total": len(briefings),
            "latest_briefing_date": briefings[0]["date"] if briefings else None,
            "generated": datetime.now(timezone.utc).isoformat(),
            "generated_local_date": datetime.now().astimezone().date().isoformat(),
            "category_disclaimer": CATEGORY_DISCLAIMER,
            "foundation_label": FOUNDATION_LABEL,
            "blog_section_title": BLOG_SECTION_TITLE,
            "blog_section_desc": BLOG_SECTION_DESC,
            "briefing_section_title": DAILY_BRIEFING_SECTION_TITLE,
            "briefing_section_desc": DAILY_BRIEFING_SECTION_DESC,
        },
        "categories": CATEGORIES,
        "mechanism_tags": list(VALID_MECHANISM_TAGS),
        "focus_tags": list(VALID_FOCUS_TAGS),
        "papers": papers,
        "blogs": blogs,
        "briefings": briefings,
    }
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ papers.json  — {len(papers)} papers, {len(blogs)} blogs, {len(briefings)} briefings")


def render_tags_reference_text(papers: list[dict], blogs: list[dict]) -> str:
    mechanism_counts: Counter[str] = Counter()
    focus_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    alias_counts: Counter[str] = Counter()

    for entry in [*papers, *blogs]:
        mechanism_counts.update(entry.get("mechanism_tags", []))
        focus_counts.update(entry.get("focus_tags", []))
        domain_counts.update(entry.get("domain_tags", []))
        alias_counts.update(entry.get("tags", []))

    def sort_counted_tags(counter: Counter[str]) -> list[tuple[str, int]]:
        return sorted(counter.items(), key=lambda item: (-item[1], item[0].lower(), item[0]))

    lines = [
        "# TAGS",
        "",
        "Prefer existing tags from this file when adding a paper or blog. Only propose a new tag when no current option fits.",
        "",
        "This file is auto-generated from `papers/*.yaml` and `blogs/*.yaml` by `scripts/build.py`.",
        "",
        "## Selection Policy",
        "",
        "- Reuse an existing tag whenever possible.",
        "- Reuse the existing spelling and case exactly.",
        "- Loop Mechanism (`mechanism_tags`) describes the loop form and must be one of `hierarchical-loop`, `flat-loop`, `parallel-loop`, or `implicit-layer`; do not use paper acronyms or lineage labels such as `DEQ` as browser-facing tags.",
        "- `focus_tags` are controlled vocabulary and must come from the allowlist below.",
        "- `domain_tags` are browser-facing domain labels; prefer an existing one before proposing a new domain tag.",
        "- `tags` are optional alias metadata for short model or paper identifiers; prefer existing spellings before proposing a new alias tag.",
        "",
    ]

    def append_section(title: str, intro: str, items: list[tuple[str, int]]) -> None:
        lines.extend([f"## {title}", "", intro, ""])
        if items:
            for tag, count in items:
                lines.append(f"- `{tag}` ({count})")
        else:
            lines.append("- _None yet_")
        lines.append("")

    append_section(
        "Loop Mechanism (`mechanism_tags`)",
        "Loop Mechanism is a controlled loop-form tag set. Use only `hierarchical-loop`, `flat-loop`, `parallel-loop`, or `implicit-layer`.",
        [(tag, mechanism_counts.get(tag, 0)) for tag in VALID_MECHANISM_TAGS],
    )
    append_section(
        "focus_tags",
        "Controlled vocabulary. The build validates these values, and the interactive browser uses them as filter chips.",
        [(tag, focus_counts.get(tag, 0)) for tag in VALID_FOCUS_TAGS],
    )
    append_section(
        "domain_tags",
        "Observed browser-facing domain tags currently used across the repo.",
        sort_counted_tags(domain_counts),
    )
    append_section(
        "tags",
        "Observed alias tags currently used across the repo. These do not appear as browser filter chips, but contributors should still prefer existing spellings.",
        sort_counted_tags(alias_counts),
    )

    return "\n".join(lines).rstrip() + "\n"


def build_tags_reference(papers: list[dict], blogs: list[dict]) -> None:
    tag_text = render_tags_reference_text(papers, blogs)
    TAGS_OUT.write_text(tag_text, encoding="utf-8")

    unique_mechanism_tags = {tag for entry in [*papers, *blogs] for tag in entry.get("mechanism_tags", [])}
    unique_domain_tags = {tag for entry in [*papers, *blogs] for tag in entry.get("domain_tags", [])}
    unique_alias_tags = {tag for entry in [*papers, *blogs] for tag in entry.get("tags", [])}
    print(
        f"✓ TAGS.md      — {len(unique_mechanism_tags)} Loop Mechanism tags, {len(VALID_FOCUS_TAGS)} focus tags, "
        f"{len(unique_domain_tags)} domain tags, {len(unique_alias_tags)} alias tags"
    )


def primary_link(links: dict) -> str:
    return (
        links.get("blog")
        or links.get("arxiv")
        or links.get("paper")
        or links.get("openreview")
        or links.get("project")
        or links.get("github")
        or links.get("hf")
        or links.get("twitter")
        or "#"
    )


def link_badge_parts(key: str, url: str) -> tuple[str, str, str]:
    if key == "github":
        repo_slug = _repo_slug_from_url(url)
        stargazers_url = _github_stargazers_url(url)
        if repo_slug and stargazers_url:
            badge_url = f"https://img.shields.io/github/stars/{quote(repo_slug, safe='/')}?style=social"
            return ("GitHub stars", badge_url, stargazers_url)

    if key == "project":
        return ("Website", "https://img.shields.io/badge/Website-Link-blue", url)

    if key == "openreview" or (key == "paper" and _is_openreview_url(url)):
        return ("OpenReview", "https://img.shields.io/badge/OpenReview-Paper-8E44AD.svg", url)

    label, color = LINK_BADGES[key]
    message = badge_message_for_link(key, url) or "link"
    badge_url = (
        f"https://img.shields.io/badge/{quote(shields_escape(label), safe='')}-"
        f"{quote(shields_escape(message), safe='')}-{color}.svg"
    )
    return (label, badge_url, url)


def render_link_badge(key: str, url: str) -> str:
    label, badge_url, target_url = link_badge_parts(key, url)
    return f"[![{label}]({badge_url})]({target_url})"


def render_link_badge_html(key: str, url: str, linked: bool = True) -> str:
    label, badge_url, target_url = link_badge_parts(key, url)
    img_html = f'<img alt="{escape(label, quote=True)}" src="{escape(badge_url, quote=True)}">'
    if not linked:
        return img_html
    return f'<a href="{escape(target_url, quote=True)}">{img_html}</a>'


def iter_ordered_link_items(links: dict):
    ordered = [
        ("blog", "Blog"),
        ("arxiv", "arXiv"),
        ("alphaxiv", "AlphaXiv"),
        ("paper", "Paper"),
        ("github", "GitHub stars"),
        ("readme", "README"),
        ("hf", "HuggingFace"),
        ("openreview", "OpenReview"),
        ("project", "Website"),
        ("twitter", "Twitter"),
    ]
    paper_is_openreview = _is_openreview_url(links.get("paper") or "")
    for key, _label in ordered:
        if not links.get(key):
            continue
        if key == "openreview" and paper_is_openreview:
            continue
        yield key, links[key]


def render_link_list(links: dict) -> str:
    return " ".join(render_link_badge(key, url) for key, url in iter_ordered_link_items(links))


def render_link_list_html(links: dict, linked: bool = True) -> str:
    return " ".join(render_link_badge_html(key, url, linked=linked) for key, url in iter_ordered_link_items(links))


def _readme_display_date(published_date: object) -> str:
    """Format a normalized publication date for README entry prefixes."""
    value = str(published_date or "").strip()
    if not value:
        return ""
    try:
        parsed_date = date.fromisoformat(value)
    except ValueError:
        return ""
    return parsed_date.strftime("%m/%d/%Y")


def _paper_to_md(paper: dict) -> str:
    title = paper.get("title", "Untitled")
    authors = paper.get("authors", "")
    venue = paper.get("venue", "")
    year = paper.get("year", "")
    desc = (paper.get("desc") or "").strip()
    focus_tags = paper.get("focus_tags", [])
    mechanism_tags = paper.get("mechanism_tags", [])
    domain_tags = paper.get("domain_tags", [])
    comments = paper.get("community_comments") or []
    links = paper.get("links", {})

    venue_year = f"{venue} {year}" if venue and venue != "arXiv" else str(year)
    summary_link_html = render_link_list_html(links, linked=True)

    summary_parts = []
    display_date = _readme_display_date(paper.get("published_date"))
    if display_date:
        summary_parts.append(f"[{display_date}]")
    if paper.get("must_read"):
        summary_parts.append("🌟")
    summary_parts.append(f"<strong>{escape(title)}</strong>")
    if summary_link_html:
        summary_parts.append(summary_link_html)

    lines = ["- <details>", f"  <summary>{' '.join(summary_parts)}</summary>"]

    detail_lines = []
    metadata = " · ".join(str(part).strip() for part in (authors, venue_year) if str(part).strip())
    if metadata:
        detail_lines.append(f"  <div><strong>Authors:</strong> {escape(metadata)}</div>")
    if mechanism_tags:
        detail_lines.append(f"  <div><strong>Loop Mechanism:</strong> {escape(' · '.join(mechanism_tags))}</div>")
    if focus_tags:
        detail_lines.append(f"  <div><strong>Focus:</strong> {escape(' · '.join(focus_tags))}</div>")
    if domain_tags:
        detail_lines.append(f"  <div><strong>Domains:</strong> {escape(' · '.join(domain_tags))}</div>")
    if comments:
        cc_links = [
            f'<a href="{escape(item["url"])}">{escape(item["label"])}</a>'
            for item in comments
            if item.get("url") and item.get("label")
        ]
        if cc_links:
            detail_lines.append(f"  <div><strong>Community Comments:</strong> {' '.join(cc_links)}</div>")
    if desc:
        detail_lines.append(f"  <div><strong>TL;DR:</strong> {escape(desc)}</div>")

    lines.extend(detail_lines)
    lines.append("  </details>")
    return "\n".join(lines)


def render_readme_fragment(template_text: str, meta: dict) -> str:
    return (
        template_text
        .replace("{{PUBLIC_INDEX_URL}}", meta["public_pages_base"] + "/index.html")
        .replace("{{PUBLIC_SUBMIT_URL}}", meta["public_pages_base"] + "/submit.html")
    )


def build_readme(papers: list[dict], blogs: list[dict], repo_meta: dict) -> None:
    header = render_readme_fragment(HEADER_FILE.read_text(encoding="utf-8").rstrip(), repo_meta)
    footer = render_readme_fragment(FOOTER_FILE.read_text(encoding="utf-8").rstrip(), repo_meta)

    papers_by_path: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    papers_by_prefix_count: dict[tuple[str, ...], int] = defaultdict(int)

    for paper in papers:
        full_path = paper_full_category_path(paper)
        papers_by_path[full_path].append(paper)
        for depth in range(1, len(full_path) + 1):
            papers_by_prefix_count[full_path[:depth]] += 1

    def sort_key(entry: dict):
        # README sections should read newest-to-oldest within each category.
        published_date = str(entry.get("published_date") or "").strip()
        try:
            date_rank = -date.fromisoformat(published_date).toordinal()
            missing_date_rank = 0
        except ValueError:
            date_rank = 0
            missing_date_rank = 1
        return (
            missing_date_rank,
            date_rank,
            str(entry.get("title", "")).lower(),
        )

    toc_lines = ["## Table of Contents", ""]
    anchor_counts: dict[str, int] = defaultdict(int)

    def next_anchor(title: str) -> str:
        base = heading_anchor(title)
        count = anchor_counts[base]
        anchor_counts[base] += 1
        return base if count == 0 else f"{base}-{count}"

    def append_toc_node(node: dict, path: tuple[str, ...], depth: int) -> None:
        count = papers_by_prefix_count.get(path, 0)
        if count == 0:
            return
        indent = "  " * depth
        toc_lines.append(f"{indent}- [{node['title']}](#{next_anchor(node['title'])}) ({count})")
        for child_id, child in iter_child_nodes(node):
            append_toc_node(child, path + (child_id,), depth + 1)

    for category_id, category in iter_category_tree():
        append_toc_node(category, (category_id,), 0)
    if blogs:
        toc_lines.append(f"- [{BLOG_SECTION_TITLE}](#{next_anchor(BLOG_SECTION_TITLE)}) ({len(blogs)})")
    toc_lines.append("")
    toc_lines.append("> " + CATEGORY_DISCLAIMER)
    if blogs:
        toc_lines.append("> Blogs are a separate flat section: they can carry tags, but they do not use the paper taxonomy.")
    toc_lines.append("")
    toc_lines.append("---")
    toc = "\n".join(toc_lines)

    sections: list[str] = []
    for category_id, category in iter_category_tree():
        category_path = (category_id,)
        if papers_by_prefix_count.get(category_path, 0) == 0:
            continue

        section_lines = [f"## {category['title']}", ""]
        if category.get("readme_intro"):
            section_lines.append(category["readme_intro"])
            section_lines.append("")

        def append_section_node(node: dict, path: tuple[str, ...], depth: int) -> None:
            for child_id, child in iter_child_nodes(node):
                child_path = path + (child_id,)
                if papers_by_prefix_count.get(child_path, 0) == 0:
                    continue
                heading_level = min(6, depth + 3)
                section_lines.append(f"{'#' * heading_level} {child['title']}")
                section_lines.append("")
                if child.get("desc"):
                    section_lines.append(child["desc"])
                    section_lines.append("")
                append_section_node(child, child_path, depth + 1)

            for paper in sorted(papers_by_path.get(path, []), key=sort_key):
                section_lines.append(_paper_to_md(paper))
                section_lines.append("")

        append_section_node(category, category_path, 0)
        section_lines.append("---")
        sections.append("\n".join(section_lines))

    if blogs:
        blog_lines = [f"## {BLOG_SECTION_TITLE}", "", BLOG_SECTION_DESC, ""]
        for blog in sorted(blogs, key=sort_key):
            blog_lines.append(_paper_to_md(blog))
            blog_lines.append("")
        blog_lines.append("---")
        sections.append("\n".join(blog_lines))

    auto_note = (
        "<!-- AUTO-GENERATED by scripts/build.py on "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} — "
        "DO NOT EDIT the lists below manually. Edit papers/*.yaml or blogs/*.yaml and run `python3 scripts/build.py` instead. -->"
    )

    README_OUT.write_text("\n\n".join([header, toc, auto_note, "\n\n".join(sections), footer]) + "\n", encoding="utf-8")
    print(f"✓ README.md    — {len(papers)} papers, {len(blogs)} blogs")


def build() -> None:
    repo_meta = load_repo_meta()
    papers = load_papers()
    blogs = load_blogs()
    briefings = load_briefings()
    build_json(papers, blogs, briefings)
    build_readme(papers, blogs, repo_meta)
    build_tags_reference(papers, blogs)
    build_repo_meta_js(repo_meta)
    build_issue_template_config(repo_meta)

    counts = Counter(paper["category"] for paper in papers)
    for category_id, category in CATEGORIES.items():
        n = counts.get(category_id, 0)
        if n:
            print(f"    {category['title']}: {n}")
    if blogs:
        print(f"    {BLOG_SECTION_TITLE}: {len(blogs)}")


if __name__ == "__main__":
    build()
