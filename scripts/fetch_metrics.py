#!/usr/bin/env python3
"""
fetch_metrics.py — Fetch citation counts and GitHub stars for all papers.

Data sources:
  - Citation counts: Semantic Scholar Public API (batch endpoint, up to 500/request)
  - GitHub stars:    GitHub REST API (uses GITHUB_TOKEN env var if available)

Usage:
    python3 scripts/fetch_metrics.py                         # update all papers using free citation sources
    python3 scripts/fetch_metrics.py --dry-run               # print without writing
    python3 scripts/fetch_metrics.py --google-scholar        # include Scholar best-effort scrape
    python3 scripts/fetch_metrics.py --only 2506.21734 --google-scholar --scholar-delay-min 3 --scholar-delay-max 8

After running, call `python3 scripts/build.py` to regenerate papers.json + README.md.
"""

import os
import re
import ssl
import sys
import time
import json
import random
import argparse
import difflib
import subprocess
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

try:
    import yaml
except ModuleNotFoundError as exc:
    if exc.name == "yaml":
        raise SystemExit(
            "Missing dependency 'PyYAML'. Install it with:\n"
            "  python3 -m pip install pyyaml"
        ) from exc
    raise

try:
    from tqdm.auto import tqdm
except ModuleNotFoundError:
    tqdm = None

REPO_ROOT  = Path(__file__).parent.parent
PAPERS_DIR = REPO_ROOT / "papers"
ENV_FILE   = REPO_ROOT / ".env"
CACHE_DIR  = REPO_ROOT / ".cache"
CACHE_FILE = CACHE_DIR / "fetch_metrics_cache.json"
GITHUB_LINK_REPORT_FILE = CACHE_DIR / "github_link_report.json"
CACHE_VERSION = 1
CITATION_CACHE_TTL_DAYS = float(os.environ.get("CITATION_CACHE_TTL_DAYS", "7"))
CITATION_MISS_CACHE_TTL_HOURS = float(os.environ.get("CITATION_MISS_CACHE_TTL_HOURS", "12"))
STAR_CACHE_TTL_DAYS = float(os.environ.get("STAR_CACHE_TTL_DAYS", "3"))
STAR_MISS_CACHE_TTL_HOURS = float(os.environ.get("STAR_MISS_CACHE_TTL_HOURS", "12"))


def _load_dotenv_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or key in os.environ:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[key] = value


_load_dotenv_file(ENV_FILE)


def _resolve_progress_enabled(progress: bool | None) -> bool:
    if progress is not None:
        if progress and tqdm is None:
            print(
                "      [warn] tqdm is not installed; progress bars are disabled. "
                "Install it with: python3 -m pip install tqdm"
            )
            return False
        return progress
    return tqdm is not None and sys.stderr.isatty()


def _progress(iterable, *, total: int | None = None, desc: str = "", unit: str = "item", enabled: bool = False):
    if not enabled or tqdm is None:
        return iterable
    return tqdm(iterable, total=total, desc=desc, unit=unit, dynamic_ncols=True, leave=False)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _load_metrics_cache(path: Path = CACHE_FILE) -> dict:
    if not path.exists():
        return {"version": CACHE_VERSION, "papers": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": CACHE_VERSION, "papers": {}}
    if not isinstance(data, dict):
        return {"version": CACHE_VERSION, "papers": {}}
    data.setdefault("version", CACHE_VERSION)
    data.setdefault("papers", {})
    return data


def _save_metrics_cache(cache: dict, path: Path = CACHE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _cache_lookup(
    cache: dict,
    stem: str,
    metric_kind: str,
    source: str,
    *,
    success_ttl_days: float,
    miss_ttl_hours: float,
) -> tuple[bool, int | None]:
    entry = _cache_entry(cache, stem, metric_kind, source)
    if not entry:
        return False, None
    fetched_at = entry.get("fetched_at")
    if not fetched_at:
        return False, None
    try:
        fetched_dt = datetime.fromisoformat(fetched_at)
    except ValueError:
        return False, None
    if fetched_dt.tzinfo is None:
        fetched_dt = fetched_dt.replace(tzinfo=timezone.utc)
    value = entry.get("value")
    ttl_seconds = success_ttl_days * 86400 if value is not None else miss_ttl_hours * 3600
    age_seconds = (_utcnow() - fetched_dt).total_seconds()
    if age_seconds > ttl_seconds:
        return False, None
    return True, value


def _cache_entry(cache: dict, stem: str, metric_kind: str, source: str) -> dict:
    papers = cache.get("papers", {}) if isinstance(cache, dict) else {}
    return (((papers.get(stem) or {}).get(metric_kind) or {}).get(source) or {})


def _cache_store(
    cache: dict,
    stem: str,
    metric_kind: str,
    source: str,
    value: int | None,
    extra: dict | None = None,
) -> None:
    papers = cache.setdefault("papers", {})
    paper_entry = papers.setdefault(stem, {})
    metric_entry = paper_entry.setdefault(metric_kind, {})
    payload = {
        "value": value,
        "fetched_at": _utcnow().isoformat(),
    }
    if extra:
        payload.update(extra)
    metric_entry[source] = payload


# ── HTTP helper ───────────────────────────────────────────────────────────────


def _should_try_curl_fallback(error: Exception | None) -> bool:
    if error is None:
        return False
    if isinstance(error, urllib.error.HTTPError):
        return False
    if isinstance(error, ssl.SSLCertVerificationError):
        return True
    if isinstance(error, urllib.error.URLError):
        reason = getattr(error, "reason", None)
        if isinstance(reason, ssl.SSLCertVerificationError):
            return True
        if reason and "CERTIFICATE_VERIFY_FAILED" in str(reason):
            return True
    return "CERTIFICATE_VERIFY_FAILED" in str(error)


def _curl_json_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict | None = None,
    body: dict | None = None,
    timeout: int = 10,
) -> dict | list | None:
    cmd = ["curl", "-fsSL", "--max-time", str(timeout), "-X", method.upper()]
    for key, value in (headers or {}).items():
        cmd.extend(["-H", f"{key}: {value}"])
    payload = None
    if body is not None:
        payload = json.dumps(body).encode()
        cmd.extend(["-H", "Content-Type: application/json", "--data-binary", "@-"])
    cmd.append(url)
    try:
        proc = subprocess.run(
            cmd,
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode("utf-8", "ignore").strip()
        if stderr:
            print(f"    [curl] {stderr[:120]}")
        return None
    except Exception as e:
        print(f"    [curl error] {url[:80]}: {e}")
        return None

    try:
        return json.loads(proc.stdout.decode())
    except Exception as e:
        print(f"    [curl parse error] {url[:80]}: {e}")
        return None


def _curl_text_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict | None = None,
    timeout: int = 10,
) -> str | None:
    cmd = ["curl", "-fsSL", "--max-time", str(timeout), "-X", method.upper()]
    for key, value in (headers or {}).items():
        cmd.extend(["-H", f"{key}: {value}"])
    cmd.append(url)
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode("utf-8", "ignore").strip()
        if stderr:
            print(f"    [curl] {stderr[:120]}")
        return None
    except Exception as e:
        print(f"    [curl error] {url[:80]}: {e}")
        return None
    return proc.stdout.decode("utf-8", "ignore")


def _curl_status_code(
    url: str,
    *,
    headers: dict | None = None,
    timeout: int = 10,
) -> int | None:
    cmd = ["curl", "-sS", "-L", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", str(timeout)]
    for key, value in (headers or {}).items():
        cmd.extend(["-H", f"{key}: {value}"])
    cmd.append(url)
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=timeout,
        )
    except Exception:
        return None
    try:
        code = int(proc.stdout.decode("utf-8", "ignore").strip())
    except ValueError:
        return None
    return code if code > 0 else None


def _http_get_text(
    url: str,
    headers: dict | None = None,
    timeout: int = 10,
    retries: int = 3,
    retry_backoff: float = 1.5,
) -> str | None:
    req = urllib.request.Request(url, headers=headers or {})
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            last_error = e
            is_retryable = e.code in (429, 500, 502, 503, 504)
            if attempt < retries and is_retryable:
                sleep_s = retry_backoff ** attempt
                print(f"    [HTTP {e.code}] GET retry in {sleep_s:.1f}s: {url[:80]}")
                time.sleep(sleep_s)
                continue
            if e.code not in (404, 403):
                print(f"    [HTTP {e.code}] {url[:80]}")
            return None
        except Exception as e:
            last_error = e
            if _should_try_curl_fallback(e):
                print(f"    [error] {url[:80]}: {e}")
                break
            if attempt < retries:
                sleep_s = retry_backoff ** attempt
                print(f"    [error] GET retry in {sleep_s:.1f}s: {url[:80]}: {e}")
                time.sleep(sleep_s)
                continue
            print(f"    [error] {url[:80]}: {e}")

    if _should_try_curl_fallback(last_error):
        return _curl_text_request(url, headers=headers, timeout=timeout)
    return None


def _http_get(
    url: str,
    headers: dict | None = None,
    timeout: int = 10,
    retries: int = 3,
    retry_backoff: float = 1.5,
) -> dict | list | None:
    req = urllib.request.Request(url, headers=headers or {})
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            last_error = e
            is_retryable = e.code in (429, 500, 502, 503, 504)
            if attempt < retries and is_retryable:
                sleep_s = retry_backoff ** attempt
                print(f"    [HTTP {e.code}] GET retry in {sleep_s:.1f}s: {url[:80]}")
                time.sleep(sleep_s)
                continue
            if e.code not in (404, 403):
                print(f"    [HTTP {e.code}] {url[:80]}")
            return None
        except Exception as e:
            last_error = e
            if _should_try_curl_fallback(e):
                print(f"    [error] {url[:80]}: {e}")
                break
            if attempt < retries:
                sleep_s = retry_backoff ** attempt
                print(f"    [error] GET retry in {sleep_s:.1f}s: {url[:80]}: {e}")
                time.sleep(sleep_s)
                continue
            print(f"    [error] {url[:80]}: {e}")

    if _should_try_curl_fallback(last_error):
        return _curl_json_request(url, headers=headers, timeout=timeout)
    return None


def _http_post(
    url: str,
    body: dict,
    headers: dict | None = None,
    timeout: int = 15,
    retries: int = 3,
    retry_backoff: float = 1.5,
) -> dict | list | None:
    data = json.dumps(body).encode()
    req_headers = {"Content-Type": "application/json", **(headers or {})}
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers=req_headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            last_error = e
            is_retryable = e.code in (429, 500, 502, 503, 504)
            if attempt < retries and is_retryable:
                sleep_s = retry_backoff ** attempt
                print(f"    [HTTP {e.code}] POST retry in {sleep_s:.1f}s: {url[:80]}")
                time.sleep(sleep_s)
                continue
            print(f"    [HTTP {e.code}] POST {url[:80]}")
            return None
        except Exception as e:
            last_error = e
            if _should_try_curl_fallback(e):
                print(f"    [error] POST {url[:80]}: {e}")
                break
            if attempt < retries:
                sleep_s = retry_backoff ** attempt
                print(f"    [error] POST retry in {sleep_s:.1f}s: {url[:80]}: {e}")
                time.sleep(sleep_s)
                continue
            print(f"    [error] POST {url[:80]}: {e}")

    if _should_try_curl_fallback(last_error):
        return _curl_json_request(url, method="POST", headers=req_headers, body=body, timeout=timeout)
    return None


# ── Semantic Scholar batch API ────────────────────────────────────────────────

S2_BATCH_URL = "https://api.semanticscholar.org/graph/v1/paper/batch"
S2_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")
S2_HEADERS = {"x-api-key": S2_API_KEY} if S2_API_KEY else {}
OPENALEX_WORKS_URL = "https://api.openalex.org/works"
CROSSREF_WORKS_URL = "https://api.crossref.org/works"
OPENCITATIONS_COCI_URL = "https://opencitations.net/index/coci/api/v1/citation-count"
S2_PAPER_FIELDS = "citationCount,externalIds,title,year,url"
S2_SEARCH_MATCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search/match"
S2_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
S2_MIN_INTERVAL_SECONDS = max(
    float(os.environ.get("SEMANTIC_SCHOLAR_MIN_INTERVAL_SECONDS", "1.25" if S2_API_KEY else "0")),
    0.0,
)
_S2_RATE_LIMIT_LOCK = Lock()
_S2_LAST_REQUEST_AT = 0.0


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _normalize_title(text: str) -> str:
    text = _normalize_whitespace(text).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return _normalize_whitespace(text)


def _title_similarity(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, _normalize_title(left), _normalize_title(right)).ratio()


def _retry_delay_seconds(
    attempt: int,
    retry_backoff: float,
    error: urllib.error.HTTPError | None = None,
) -> float:
    delay = retry_backoff ** attempt
    if error is not None:
        retry_after = error.headers.get("Retry-After")
        if retry_after:
            try:
                delay = max(delay, float(retry_after))
            except ValueError:
                pass
    return delay


def _s2_wait_for_slot() -> None:
    global _S2_LAST_REQUEST_AT

    if S2_MIN_INTERVAL_SECONDS <= 0:
        return

    with _S2_RATE_LIMIT_LOCK:
        now = time.monotonic()
        wait_s = _S2_LAST_REQUEST_AT + S2_MIN_INTERVAL_SECONDS - now
        if wait_s > 0:
            time.sleep(wait_s)
        _S2_LAST_REQUEST_AT = time.monotonic()


def _s2_http_get(
    url: str,
    timeout: int = 15,
    retries: int = 4,
    retry_backoff: float = 2.0,
) -> dict | list | None:
    req = urllib.request.Request(url, headers=S2_HEADERS)
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        _s2_wait_for_slot()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            last_error = e
            is_retryable = e.code in (429, 500, 502, 503, 504)
            if attempt < retries and is_retryable:
                sleep_s = _retry_delay_seconds(attempt, retry_backoff, e)
                print(f"    [HTTP {e.code}] S2 GET retry in {sleep_s:.1f}s: {url[:80]}")
                time.sleep(sleep_s)
                continue
            if e.code not in (404, 403):
                print(f"    [HTTP {e.code}] S2 GET {url[:80]}")
            return None
        except Exception as e:
            last_error = e
            if _should_try_curl_fallback(e):
                print(f"    [error] S2 GET {url[:80]}: {e}")
                break
            if attempt < retries:
                sleep_s = retry_backoff ** attempt
                print(f"    [error] S2 GET retry in {sleep_s:.1f}s: {url[:80]}: {e}")
                time.sleep(sleep_s)
                continue
            print(f"    [error] S2 GET {url[:80]}: {e}")

    if _should_try_curl_fallback(last_error):
        return _curl_json_request(url, headers=S2_HEADERS, timeout=timeout)
    return None


def _s2_http_post(
    url: str,
    body: dict,
    timeout: int = 20,
    retries: int = 4,
    retry_backoff: float = 2.0,
) -> dict | list | None:
    data = json.dumps(body).encode()
    req_headers = {"Content-Type": "application/json", **S2_HEADERS}
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        _s2_wait_for_slot()
        req = urllib.request.Request(url, data=data, headers=req_headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            last_error = e
            is_retryable = e.code in (429, 500, 502, 503, 504)
            if attempt < retries and is_retryable:
                sleep_s = _retry_delay_seconds(attempt, retry_backoff, e)
                print(f"    [HTTP {e.code}] S2 POST retry in {sleep_s:.1f}s: {url[:80]}")
                time.sleep(sleep_s)
                continue
            print(f"    [HTTP {e.code}] S2 POST {url[:80]}")
            return None
        except Exception as e:
            last_error = e
            if _should_try_curl_fallback(e):
                print(f"    [error] S2 POST {url[:80]}: {e}")
                break
            if attempt < retries:
                sleep_s = retry_backoff ** attempt
                print(f"    [error] S2 POST retry in {sleep_s:.1f}s: {url[:80]}: {e}")
                time.sleep(sleep_s)
                continue
            print(f"    [error] S2 POST {url[:80]}: {e}")

    if _should_try_curl_fallback(last_error):
        return _curl_json_request(url, method="POST", headers=req_headers, body=body, timeout=timeout)
    return None


def _arxiv_id_from_stem(stem: str) -> str | None:
    m = re.match(r"^(\d{4}\.\d{4,5})", stem)
    return m.group(1) if m else None


def _paper_arxiv_id(paper: dict) -> str | None:
    return (
        _arxiv_id_from_stem(paper.get("stem", ""))
        or paper.get("arxiv_id")
        or _arxiv_id_from_links(paper.get("links", {}))
    )


def _arxiv_id_from_links(links: dict) -> str | None:
    arxiv_url = (links or {}).get("arxiv", "")
    m = re.search(r"arxiv\.org/abs/(\d{4}\.\d{4,5})(?:v\d+)?", arxiv_url)
    return m.group(1) if m else None


def _doi_from_text(text: str) -> str | None:
    m = re.search(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", text or "", re.IGNORECASE)
    if not m:
        return None
    return m.group(1).rstrip(").,;")


def _doi_from_links(links: dict) -> str | None:
    links = links or {}
    for key in ("doi", "paper"):
        doi = _doi_from_text(str(links.get(key, "")).strip())
        if doi:
            return doi
    return None


def _paper_doi_candidates(paper: dict) -> list[str]:
    candidates = []
    explicit_doi = _doi_from_links(paper.get("links", {}))
    if explicit_doi:
        candidates.append(explicit_doi)

    arxiv_id = _paper_arxiv_id(paper)
    if arxiv_id:
        candidates.append(f"10.48550/arXiv.{arxiv_id}")

    deduped = []
    seen = set()
    for doi in candidates:
        normalized = doi.lower()
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(doi)
    return deduped


def _semantic_scholar_ids_for_paper(paper: dict) -> list[str]:
    ids = []
    arxiv_id = _paper_arxiv_id(paper)
    if arxiv_id:
        ids.append(f"ARXIV:{arxiv_id}")
        ids.append(f"DOI:10.48550/arXiv.{arxiv_id}")

    doi = _doi_from_links(paper.get("links", {}))
    if doi:
        ids.append(f"DOI:{doi}")

    deduped = []
    seen = set()
    for identifier in ids:
        if identifier not in seen:
            seen.add(identifier)
            deduped.append(identifier)
    return deduped


def _s2_item_lookup_keys(item: dict) -> set[str]:
    keys = set()
    ext = item.get("externalIds", {}) or {}
    arxiv_id = ext.get("ArXiv") or ext.get("ARXIV")
    doi = ext.get("DOI")
    title = item.get("title")

    if arxiv_id:
        keys.add(f"ARXIV:{arxiv_id}")
        keys.add(f"DOI:10.48550/arXiv.{arxiv_id}")
    if doi:
        keys.add(f"DOI:{doi}")
    if title:
        keys.add(f"TITLE:{_normalize_title(title)}")
    return keys


def fetch_citations_batch(papers: list[dict], show_progress: bool = False) -> dict[str, int]:
    """
    Fetch citation counts for all papers in one batch POST to Semantic Scholar.
    Returns dict: paper_id (yaml stem) -> citation_count
    """
    ids = []
    id_map: dict[str, set[str]] = {}
    for p in papers:
        stem = p["stem"]
        for s2_id in _semantic_scholar_ids_for_paper(p):
            ids.append(s2_id)
            id_map.setdefault(s2_id, set()).add(stem)
        title = p.get("title")
        if title:
            id_map.setdefault(f"TITLE:{_normalize_title(title)}", set()).add(stem)

    if not ids:
        return {}

    ids = list(dict.fromkeys(ids))
    # S2 batch endpoint allows up to 500 IDs
    results = {}
    chunk_size = 100  # keep responses small and stay well under the API limit
    chunks = [ids[i:i + chunk_size] for i in range(0, len(ids), chunk_size)]
    for chunk in _progress(chunks, total=len(chunks), desc="S2 batch", unit="batch", enabled=show_progress):
        body = {"ids": chunk}
        data = _s2_http_post(
            f"{S2_BATCH_URL}?fields={urllib.parse.quote(S2_PAPER_FIELDS)}",
            body,
        )
        if data and isinstance(data, list):
            for item in data:
                if item is None:
                    continue
                citation_count = item.get("citationCount")
                if citation_count is None:
                    continue
                matched_stems = set()
                for key in _s2_item_lookup_keys(item):
                    matched_stems.update(id_map.get(key, set()))
                for stem in matched_stems:
                    results[stem] = int(citation_count)

    return results


def _fetch_citation_count_via_title_match(paper: dict) -> int | None:
    title = _normalize_whitespace(paper.get("title", ""))
    if not title:
        return None

    params = urllib.parse.urlencode({"query": title, "fields": S2_PAPER_FIELDS})
    data = _s2_http_get(f"{S2_SEARCH_MATCH_URL}?{params}")
    if not data:
        return None

    similarity = _title_similarity(title, data.get("title", ""))
    normalized_expected = _normalize_title(title)
    normalized_actual = _normalize_title(data.get("title", ""))
    expected_year = paper.get("year")
    actual_year = data.get("year")
    year_matches = True
    if expected_year and actual_year:
        try:
            year_matches = abs(int(expected_year) - int(actual_year)) <= 1
        except (TypeError, ValueError):
            year_matches = True

    if normalized_expected != normalized_actual and (similarity < 0.9 or not year_matches):
        return None

    citation_count = data.get("citationCount")
    return int(citation_count) if citation_count is not None else None


def _fetch_citation_count_via_search(paper: dict) -> int | None:
    title = _normalize_whitespace(paper.get("title", ""))
    if not title:
        return None

    params = {
        "query": title,
        "fields": S2_PAPER_FIELDS,
        "limit": "5",
    }
    year = paper.get("year")
    if year:
        try:
            year_int = int(year)
            params["year"] = f"{year_int - 1}-{year_int + 1}"
        except (TypeError, ValueError):
            params["year"] = str(year)

    data = _s2_http_get(f"{S2_SEARCH_URL}?{urllib.parse.urlencode(params)}")
    if not data:
        return None

    candidates = data.get("data", [])
    if not isinstance(candidates, list):
        return None

    best_score = 0.0
    best_citation_count = None
    normalized_expected = _normalize_title(title)
    for candidate in candidates:
        candidate_title = candidate.get("title", "")
        similarity = _title_similarity(title, candidate_title)
        if _normalize_title(candidate_title) == normalized_expected:
            similarity = max(similarity, 1.0)

        candidate_year = candidate.get("year")
        if year and candidate_year:
            try:
                if abs(int(year) - int(candidate_year)) > 1:
                    similarity -= 0.1
            except (TypeError, ValueError):
                pass

        if similarity > best_score and similarity >= 0.85:
            citation_count = candidate.get("citationCount")
            if citation_count is not None:
                best_score = similarity
                best_citation_count = int(citation_count)

    return best_citation_count


def fetch_citations_semantic_scholar(
    papers: list[dict],
    show_progress: bool = False,
    cache: dict | None = None,
    cache_ttl_days: float = CITATION_CACHE_TTL_DAYS,
    miss_ttl_hours: float = CITATION_MISS_CACHE_TTL_HOURS,
) -> dict[str, int]:
    cache = cache or {"papers": {}}
    results: dict[str, int] = {}
    unresolved: list[dict] = []
    for paper in papers:
        stem = paper["stem"]
        hit, value = _cache_lookup(
            cache,
            stem,
            "citations",
            "semantic_scholar",
            success_ttl_days=cache_ttl_days,
            miss_ttl_hours=miss_ttl_hours,
        )
        if hit:
            if value is not None:
                results[stem] = value
        else:
            unresolved.append(paper)

    if not unresolved:
        return results

    fresh_results = fetch_citations_batch(unresolved, show_progress=show_progress)
    missing = [paper for paper in unresolved if paper["stem"] not in fresh_results]
    if missing:
        print(f"      Falling back to S2 title search for {len(missing)} papers.")
        for paper in _progress(
            missing,
            total=len(missing),
            desc="S2 fallback",
            unit="paper",
            enabled=show_progress,
        ):
            citation_count = _fetch_citation_count_via_title_match(paper)
            if citation_count is None:
                citation_count = _fetch_citation_count_via_search(paper)
            if citation_count is not None:
                fresh_results[paper["stem"]] = citation_count

    for paper in unresolved:
        stem = paper["stem"]
        value = fresh_results.get(stem)
        _cache_store(cache, stem, "citations", "semantic_scholar", value)
        if value is not None:
            results[stem] = value

    return results


def _fetch_best_count_for_dois(dois: list[str], fetcher) -> int | None:
    best = None
    for doi in dois:
        count = fetcher(doi)
        if count is None:
            continue
        if best is None or count > best:
            best = count
    return best


def _fetch_openalex_for_doi(doi: str) -> int | None:
    doi_url = f"https://doi.org/{doi}"
    params = urllib.parse.urlencode({
        "filter": f"doi:{doi_url}",
        "select": "cited_by_count",
        "per-page": "1",
    })
    data = _http_get(f"{OPENALEX_WORKS_URL}?{params}", timeout=15)
    if not isinstance(data, dict):
        return None
    results = data.get("results", [])
    if not results:
        return None
    c = results[0].get("cited_by_count")
    return int(c) if c is not None else None


def _fetch_openalex_for_doi_candidates(dois: list[str]) -> int | None:
    return _fetch_best_count_for_dois(dois, _fetch_openalex_for_doi)


def fetch_citations_openalex(
    papers: list[dict],
    show_progress: bool = False,
    cache: dict | None = None,
    cache_ttl_days: float = CITATION_CACHE_TTL_DAYS,
    miss_ttl_hours: float = CITATION_MISS_CACHE_TTL_HOURS,
) -> dict[str, int]:
    """
    Fetch citation counts from OpenAlex by DOI (preferring explicit DOI, then arXiv DOI).
    Returns dict: paper_id (yaml stem) -> citation_count
    """
    cache = cache or {"papers": {}}
    results: dict[str, int] = {}
    pairs: list[tuple[str, list[str]]] = []
    for p in papers:
        stem = p["stem"]
        hit, value = _cache_lookup(
            cache,
            stem,
            "citations",
            "openalex",
            success_ttl_days=cache_ttl_days,
            miss_ttl_hours=miss_ttl_hours,
        )
        if hit:
            if value is not None:
                results[stem] = value
            continue
        dois = _paper_doi_candidates(p)
        if dois:
            pairs.append((stem, dois))
        else:
            _cache_store(cache, stem, "citations", "openalex", None)

    def _fetch(pair: tuple[str, list[str]]) -> tuple[str, int | None]:
        stem, dois = pair
        return stem, _fetch_openalex_for_doi_candidates(dois)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_fetch, pair): pair[0] for pair in pairs}
        for future in _progress(
            as_completed(futures),
            total=len(futures),
            desc="OpenAlex",
            unit="paper",
            enabled=show_progress,
        ):
            stem, c = future.result()
            _cache_store(cache, stem, "citations", "openalex", c)
            if c is not None:
                results[stem] = c

    return results


def _fetch_opencitations_for_doi(doi: str) -> int | None:
    encoded = urllib.parse.quote(doi, safe="")
    data = _http_get(f"{OPENCITATIONS_COCI_URL}/{encoded}", timeout=15)
    if not isinstance(data, list) or not data:
        return None
    c = data[0].get("count")
    return int(c) if c is not None else None


def _fetch_opencitations_for_doi_candidates(dois: list[str]) -> int | None:
    return _fetch_best_count_for_dois(dois, _fetch_opencitations_for_doi)


def fetch_citations_opencitations(
    papers: list[dict],
    show_progress: bool = False,
    cache: dict | None = None,
    cache_ttl_days: float = CITATION_CACHE_TTL_DAYS,
    miss_ttl_hours: float = CITATION_MISS_CACHE_TTL_HOURS,
) -> dict[str, int]:
    """Fetch citation counts from OpenCitations COCI by DOI."""
    cache = cache or {"papers": {}}
    results: dict[str, int] = {}
    pairs: list[tuple[str, list[str]]] = []
    for p in papers:
        stem = p["stem"]
        hit, value = _cache_lookup(
            cache,
            stem,
            "citations",
            "opencitations",
            success_ttl_days=cache_ttl_days,
            miss_ttl_hours=miss_ttl_hours,
        )
        if hit:
            if value is not None:
                results[stem] = value
            continue
        dois = _paper_doi_candidates(p)
        if dois:
            pairs.append((stem, dois))
        else:
            _cache_store(cache, stem, "citations", "opencitations", None)

    def _fetch(pair: tuple[str, list[str]]) -> tuple[str, int | None]:
        stem, dois = pair
        return stem, _fetch_opencitations_for_doi_candidates(dois)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_fetch, pair): pair[0] for pair in pairs}
        for future in _progress(
            as_completed(futures),
            total=len(futures),
            desc="OpenCitations",
            unit="paper",
            enabled=show_progress,
        ):
            stem, c = future.result()
            _cache_store(cache, stem, "citations", "opencitations", c)
            if c is not None:
                results[stem] = c

    return results


def _fetch_crossref_for_doi(doi: str) -> int | None:
    encoded = urllib.parse.quote(doi, safe="")
    data = _http_get(f"{CROSSREF_WORKS_URL}/{encoded}", timeout=15)
    if not isinstance(data, dict):
        return None
    message = data.get("message", {})
    c = message.get("is-referenced-by-count")
    return int(c) if c is not None else None


def _fetch_crossref_for_doi_candidates(dois: list[str]) -> int | None:
    explicit_only = [doi for doi in dois if not doi.lower().startswith("10.48550/arxiv.")]
    if not explicit_only:
        return None
    return _fetch_best_count_for_dois(explicit_only, _fetch_crossref_for_doi)


def fetch_citations_crossref(
    papers: list[dict],
    show_progress: bool = False,
    cache: dict | None = None,
    cache_ttl_days: float = CITATION_CACHE_TTL_DAYS,
    miss_ttl_hours: float = CITATION_MISS_CACHE_TTL_HOURS,
) -> dict[str, int]:
    """Fetch citation counts from Crossref using explicit DOIs when available."""
    cache = cache or {"papers": {}}
    results: dict[str, int] = {}
    pairs: list[tuple[str, list[str]]] = []
    for p in papers:
        stem = p["stem"]
        hit, value = _cache_lookup(
            cache,
            stem,
            "citations",
            "crossref",
            success_ttl_days=cache_ttl_days,
            miss_ttl_hours=miss_ttl_hours,
        )
        if hit:
            if value is not None:
                results[stem] = value
            continue
        dois = _paper_doi_candidates(p)
        if any(not doi.lower().startswith("10.48550/arxiv.") for doi in dois):
            pairs.append((stem, dois))
        else:
            _cache_store(cache, stem, "citations", "crossref", None)

    def _fetch(pair: tuple[str, list[str]]) -> tuple[str, int | None]:
        stem, dois = pair
        return stem, _fetch_crossref_for_doi_candidates(dois)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_fetch, pair): pair[0] for pair in pairs}
        for future in _progress(
            as_completed(futures),
            total=len(futures),
            desc="Crossref",
            unit="paper",
            enabled=show_progress,
        ):
            stem, c = future.result()
            _cache_store(cache, stem, "citations", "crossref", c)
            if c is not None:
                results[stem] = c

    return results


# ── Google Scholar (best-effort scrape) ──────────────────────────────────────

GS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
}


def _extract_scholar_cited_by(html: str, arxiv_id: str) -> int | None:
    needle = f"https://arxiv.org/abs/{arxiv_id}"
    pos = html.find(needle)
    if pos < 0:
        return None

    # Isolate the nearest result card to avoid grabbing unrelated "Cited by" counts.
    card_start = html.rfind('<div class="gs_r gs_or gs_scl"', 0, pos)
    if card_start < 0:
        card_start = max(0, pos - 8000)
    card_end = html.find('<div class="gs_r gs_or gs_scl"', pos + len(needle))
    if card_end < 0:
        card_end = min(len(html), pos + 20000)
    card = html[card_start:card_end]

    # Ensure this card is truly the arXiv entry we asked for.
    if f"arXiv:{arxiv_id}" not in card:
        return None

    m = re.search(r">Cited by (\d+)<", card)
    if m:
        return int(m.group(1))

    # If the result exists but "Cited by" is absent, treat as 0.
    return 0


def _fetch_google_scholar_for_arxiv(
    arxiv_id: str,
    endpoint: str = "https://scholar.google.com",
) -> int | None:
    q = urllib.parse.quote(arxiv_id)
    endpoint = endpoint.rstrip("/")
    url = f"{endpoint}/scholar?q={q}&hl=en&as_sdt=0,39"
    req = urllib.request.Request(url, headers=GS_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        print(f"    [HTTP {e.code}] Scholar {arxiv_id}")
        return None
    except Exception as e:
        print(f"    [error] Scholar {arxiv_id}: {e}")
        return None
    return _extract_scholar_cited_by(html, arxiv_id)


def fetch_citations_google_scholar(
    papers: list[dict],
    delay_min_seconds: float = 2.0,
    delay_max_seconds: float = 5.0,
    endpoint: str = "https://scholar.google.com",
    show_progress: bool = False,
) -> dict[str, int]:
    """
    Best-effort Google Scholar scrape by arXiv ID.
    Returns dict: paper_id (yaml stem) -> citation_count
    """
    pairs: list[tuple[str, str]] = []
    for p in papers:
        stem = p["stem"]
        arxiv_id = _paper_arxiv_id(p)
        if arxiv_id:
            pairs.append((stem, arxiv_id))

    results: dict[str, int] = {}
    total = len(pairs)
    delay_min_seconds = max(0.0, delay_min_seconds)
    delay_max_seconds = max(delay_min_seconds, delay_max_seconds)

    pairs_iter = _progress(
        pairs,
        total=total,
        desc="Scholar",
        unit="paper",
        enabled=show_progress,
    )
    for i, (stem, arxiv_id) in enumerate(pairs_iter, start=1):
        c = _fetch_google_scholar_for_arxiv(arxiv_id, endpoint=endpoint)
        if c is not None:
            results[stem] = c
        if i < total:
            time.sleep(random.uniform(delay_min_seconds, delay_max_seconds))
    return results


# ── GitHub Stars ──────────────────────────────────────────────────────────────

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "awesome-iterative-inference-bot",
}
if GH_TOKEN:
    GH_HEADERS["Authorization"] = f"Bearer {GH_TOKEN}"


def _parse_github_repo(url: str) -> tuple[str, str] | None:
    m = re.search(r"github\.com/([^/]+)/([^/?#\s]+)", url)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    repo = repo.rstrip("/").removesuffix(".git")
    return owner, repo


def _parse_github_stars_from_html(html: str) -> int | None:
    if not html:
        return None
    patterns = [
        r'([0-9][0-9,]*(?:\.[0-9]+)?[kKmM]?)\s+stars?',
        r'aria-label="([0-9][0-9,]*(?:\.[0-9]+)?[kKmM]?)\s+users?\s+starred',
    ]
    for pattern in patterns:
        m = re.search(pattern, html)
        if not m:
            continue
        raw = m.group(1).replace(',', '').strip().lower()
        multiplier = 1
        if raw.endswith('k'):
            multiplier = 1000
            raw = raw[:-1]
        elif raw.endswith('m'):
            multiplier = 1000000
            raw = raw[:-1]
        try:
            return int(float(raw) * multiplier)
        except ValueError:
            continue
    return None


def get_github_star_details(github_url: str) -> tuple[int | None, str | None, dict | None]:
    parsed = _parse_github_repo(github_url)
    if not parsed:
        return None, None, None
    owner, repo = parsed
    repo_url = f"https://github.com/{owner}/{repo}"
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    data = _http_get(api_url, GH_HEADERS)
    if isinstance(data, dict) and "stargazers_count" in data:
        return int(data["stargazers_count"]), "github_api", None

    html = _http_get_text(repo_url, GH_HEADERS)
    stars = _parse_github_stars_from_html(html)
    if stars is not None:
        return stars, "github_html", None

    status = _curl_status_code(repo_url, headers=GH_HEADERS)
    if status == 404:
        return None, None, {
            "url": repo_url,
            "reason": "github_repo_404",
            "status_code": 404,
        }
    return None, None, None


def get_github_stars(github_url: str) -> int | None:
    stars, _source, _broken = get_github_star_details(github_url)
    return stars


def fetch_stars_parallel(
    papers: list[dict],
    show_progress: bool = False,
    cache: dict | None = None,
    cache_ttl_days: float = STAR_CACHE_TTL_DAYS,
    miss_ttl_hours: float = STAR_MISS_CACHE_TTL_HOURS,
) -> tuple[dict[str, int], dict[str, dict[str, int]], list[dict]]:
    """Fetch GitHub stars for all papers in parallel."""
    cache = cache or {"papers": {}}
    results: dict[str, int] = {}
    source_maps: dict[str, dict[str, int]] = {}
    broken_links: list[dict] = []
    unresolved = []
    for p in papers:
        stem = p["stem"]
        hit, value = _cache_lookup(
            cache,
            stem,
            "stars",
            "github",
            success_ttl_days=cache_ttl_days,
            miss_ttl_hours=miss_ttl_hours,
        )
        if hit:
            entry = _cache_entry(cache, stem, "stars", "github")
            source = entry.get("source") or ("github_api" if value is not None else None)
            if value is not None:
                results[stem] = value
                if source:
                    source_maps[stem] = {source: value}
            elif entry.get("reason") == "github_repo_404":
                broken_links.append({
                    "stem": stem,
                    "url": entry.get("url") or (p.get("links", {}) or {}).get("github", ""),
                    "reason": entry.get("reason"),
                    "status_code": entry.get("status_code", 404),
                })
            continue
        github_url = p.get("links", {}).get("github", "")
        if github_url:
            unresolved.append(p)
        else:
            _cache_store(cache, stem, "stars", "github", None)

    def _fetch(p):
        stem = p["stem"]
        github_url = p.get("links", {}).get("github", "")
        stars, source, broken = get_github_star_details(github_url) if github_url else (None, None, None)
        return stem, github_url, stars, source, broken

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_fetch, p): p["stem"] for p in unresolved}
        for future in _progress(
            as_completed(futures),
            total=len(futures),
            desc="GitHub",
            unit="paper",
            enabled=show_progress,
        ):
            stem, github_url, stars, source, broken = future.result()
            extra = {"source": source} if source else {}
            if broken:
                extra.update(broken)
                broken_links.append({"stem": stem, **broken})
            _cache_store(cache, stem, "stars", "github", stars, extra=extra)
            if stars is not None:
                results[stem] = stars
                if source:
                    source_maps[stem] = {source: stars}

    return results, source_maps, broken_links


# ── Main ──────────────────────────────────────────────────────────────────────

def load_papers() -> list[dict]:
    papers = []
    for yaml_file in sorted(PAPERS_DIR.glob("*.yaml")):
        if yaml_file.name.startswith("_"):
            continue
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data["stem"] = yaml_file.stem
        data["_path"] = yaml_file
        papers.append(data)
    return papers


def _print_missing_s2_papers(papers: list[dict], s2_citations_map: dict[str, int]) -> list[dict]:
    missing = [p for p in papers if p["stem"] not in s2_citations_map]
    if not missing:
        return missing

    print("      Missing from Semantic Scholar results:")
    for paper in missing:
        stem = paper.get("stem", "<unknown>")
        title = paper.get("title", "Untitled")
        links = paper.get("links", {}) or {}
        has_identifier = bool(_semantic_scholar_ids_for_paper(paper))
        reason = "no arXiv/DOI identifier" if not has_identifier else "title fallback did not match or paper is not indexed yet"
        openreview = links.get("openreview")
        extra = f" ({openreview})" if openreview else ""
        print(f"        - {stem}: {title} [{reason}]{extra}")
    return missing


def _citation_sources_for_stem(
    stem: str,
    *,
    scholar_citations_map: dict[str, int],
    s2_citations_map: dict[str, int],
    oa_citations_map: dict[str, int],
    oc_citations_map: dict[str, int],
    crossref_citations_map: dict[str, int],
) -> dict[str, int]:
    sources: dict[str, int] = {}
    if stem in scholar_citations_map:
        sources["google_scholar"] = scholar_citations_map[stem]
    if stem in s2_citations_map:
        sources["semantic_scholar"] = s2_citations_map[stem]
    if stem in oa_citations_map:
        sources["openalex"] = oa_citations_map[stem]
    if stem in oc_citations_map:
        sources["opencitations"] = oc_citations_map[stem]
    if stem in crossref_citations_map:
        sources["crossref"] = crossref_citations_map[stem]
    return sources


def _best_citation_source(source_counts: dict[str, int]) -> str | None:
    if not source_counts:
        return None
    priority = {
        "semantic_scholar": 0,
        "openalex": 1,
        "crossref": 2,
        "opencitations": 3,
        "google_scholar": 4,
    }
    return max(source_counts.items(), key=lambda item: (item[1], -priority.get(item[0], 999)))[0]


def _best_star_source(source_counts: dict[str, int]) -> str | None:
    if not source_counts:
        return None
    priority = {
        "github_api": 0,
        "github_html": 1,
    }
    return max(source_counts.items(), key=lambda item: (item[1], -priority.get(item[0], 999)))[0]


def _save_github_link_report(broken_links: list[dict], path: Path = GITHUB_LINK_REPORT_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": _utcnow().isoformat(),
        "broken_links": broken_links,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def fetch_all(
    dry_run: bool = False,
    google_scholar: bool = False,
    scholar_delay_min: float = 2.0,
    scholar_delay_max: float = 5.0,
    scholar_endpoint: str = "https://scholar.google.com",
    only: set[str] | None = None,
    progress: bool | None = None,
    use_openalex: bool = True,
    use_opencitations: bool = True,
    use_crossref: bool = True,
) -> None:
    show_progress = _resolve_progress_enabled(progress)
    cache = _load_metrics_cache(CACHE_FILE)
    papers = load_papers()
    if only:
        filtered = []
        for p in papers:
            stem = p.get("stem", "")
            arxiv_id = _paper_arxiv_id(p)
            if stem in only or (arxiv_id and arxiv_id in only):
                filtered.append(p)
        papers = filtered
    print(f"Loaded {len(papers)} papers.")

    scholar_citations_map = {}
    if google_scholar:
        print("\n[0] Fetching citation counts from Google Scholar (best-effort)…")
        scholar_citations_map = fetch_citations_google_scholar(
            papers,
            delay_min_seconds=scholar_delay_min,
            delay_max_seconds=scholar_delay_max,
            endpoint=scholar_endpoint,
            show_progress=show_progress,
        )
        print(f"      Got Scholar citations for {len(scholar_citations_map)}/{len(papers)} papers.")

    print("\n[1] Fetching citation counts from Semantic Scholar (batch + title fallback)…")
    if S2_API_KEY:
        print(f"      Using SEMANTIC_SCHOLAR_API_KEY from environment/.env with {S2_MIN_INTERVAL_SECONDS:.2f}s spacing.")
    else:
        print("      [warn] SEMANTIC_SCHOLAR_API_KEY is not set; unauthenticated requests may be throttled.")
    s2_citations_map = fetch_citations_semantic_scholar(papers, show_progress=show_progress, cache=cache)
    print(f"      Got S2 citations for {len(s2_citations_map)}/{len(papers)} papers.")

    missing_s2 = _print_missing_s2_papers(papers, s2_citations_map)

    oa_citations_map = {}
    if use_openalex:
        print("\n[2] Fetching citation counts from OpenAlex (parallel)…")
        oa_citations_map = fetch_citations_openalex(papers, show_progress=show_progress, cache=cache)
        print(f"      Got OpenAlex citations for {len(oa_citations_map)}/{len(papers)} papers.")
    else:
        print("\n[2] Skipping OpenAlex.")

    oc_citations_map = {}
    if use_opencitations:
        print("\n[3] Fetching citation counts from OpenCitations COCI (parallel)…")
        oc_citations_map = fetch_citations_opencitations(papers, show_progress=show_progress, cache=cache)
        print(f"      Got OpenCitations citations for {len(oc_citations_map)}/{len(papers)} papers.")
    else:
        print("\n[3] Skipping OpenCitations.")

    crossref_citations_map = {}
    if use_crossref:
        print("\n[4] Fetching citation counts from Crossref (parallel, DOI-only)…")
        crossref_citations_map = fetch_citations_crossref(papers, show_progress=show_progress, cache=cache)
        print(f"      Got Crossref citations for {len(crossref_citations_map)}/{len(papers)} papers.")
    else:
        print("\n[4] Skipping Crossref.")

    if missing_s2 and not any((use_openalex, use_opencitations, use_crossref)):
        print("      All free fallbacks are disabled; unresolved citations stay unchanged.")

    citation_source_maps: dict[str, dict[str, int]] = {}
    citations_map = {}
    for p in papers:
        stem = p["stem"]
        source_counts = _citation_sources_for_stem(
            stem,
            scholar_citations_map=scholar_citations_map,
            s2_citations_map=s2_citations_map,
            oa_citations_map=oa_citations_map,
            oc_citations_map=oc_citations_map,
            crossref_citations_map=crossref_citations_map,
        )
        citation_source_maps[stem] = source_counts
        if source_counts:
            citations_map[stem] = max(source_counts.values())
    print(f"      Merged citations for {len(citations_map)}/{len(papers)} papers.")

    print("\n[5] Fetching GitHub stars (parallel)…")
    stars_map, star_source_maps, broken_github_links = fetch_stars_parallel(
        papers,
        show_progress=show_progress,
        cache=cache,
    )
    print(f"      Got stars for {len(stars_map)}/{len(papers)} papers.")

    now_str = _utcnow().strftime("%Y-%m-%d")
    updated = 0
    for p in papers:
        stem = p["stem"]
        yaml_file = p["_path"]

        new_citations = citations_map.get(stem)
        new_stars = stars_map.get(stem)
        new_citation_sources = citation_source_maps.get(stem, {})
        best_citation_source = _best_citation_source(new_citation_sources)
        new_star_sources = star_source_maps.get(stem, {})
        best_star_source = _best_star_source(new_star_sources)

        changed = False
        if new_citations is not None:
            if p.get("citations") != new_citations:
                p["citations"] = new_citations
                changed = True
            if p.get("citation_sources") != new_citation_sources:
                p["citation_sources"] = new_citation_sources
                changed = True
            if p.get("citation_source_best") != best_citation_source:
                p["citation_source_best"] = best_citation_source
                changed = True
        else:
            if "citation_sources" in p:
                p.pop("citation_sources", None)
                changed = True
            if "citation_source_best" in p:
                p.pop("citation_source_best", None)
                changed = True

        if new_stars is not None:
            if p.get("github_stars") != new_stars:
                p["github_stars"] = new_stars
                changed = True
            if p.get("star_sources") != new_star_sources:
                p["star_sources"] = new_star_sources
                changed = True
            if p.get("star_source_best") != best_star_source:
                p["star_source_best"] = best_star_source
                changed = True
        else:
            if "star_sources" in p:
                p.pop("star_sources", None)
                changed = True
            if "star_source_best" in p:
                p.pop("star_source_best", None)
                changed = True
        if changed:
            p["metrics_updated"] = now_str

        if changed and not dry_run:
            write_data = {k: v for k, v in p.items() if not k.startswith("_") and k != "stem"}
            with open(yaml_file, "w", encoding="utf-8") as f:
                yaml.dump(write_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
            updated += 1

    _save_metrics_cache(cache, CACHE_FILE)
    _save_github_link_report(broken_github_links, GITHUB_LINK_REPORT_FILE)
    if broken_github_links:
        print(f"      Wrote GitHub link report with {len(broken_github_links)} broken link(s) to {GITHUB_LINK_REPORT_FILE}.")

    print("\n── Summary ──────────────────────────────────────────────────")
    print(f"{'File':<25} {'Citations':>10} {'Stars':>10}")
    print("-" * 50)
    for p in sorted(papers, key=lambda x: citations_map.get(x["stem"], 0), reverse=True):
        stem = p["stem"]
        c = citations_map.get(stem, "–")
        s = stars_map.get(stem, "–")
        if c != "–" or s != "–":
            print(f"{stem:<25} {str(c):>10} {str(s):>10}")

    print(f"\nUpdated {updated}/{len(papers)} YAML files.")
    if dry_run:
        print("(dry-run: no files written)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch citation counts and GitHub stars")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing")
    parser.add_argument(
        "--google-scholar",
        action="store_true",
        help="Also scrape Google Scholar citation counts (best-effort, slower).",
    )
    parser.add_argument(
        "--scholar-delay-min",
        type=float,
        default=2.0,
        help="Minimum delay (seconds) between Scholar queries (default: 2.0).",
    )
    parser.add_argument(
        "--scholar-delay-max",
        type=float,
        default=5.0,
        help="Maximum delay (seconds) between Scholar queries (default: 5.0).",
    )
    parser.add_argument(
        "--scholar-endpoint",
        type=str,
        default=os.environ.get("GOOGLE_SCHOLAR_ENDPOINT", "https://scholar.google.com"),
        help="Google Scholar base endpoint (default: https://scholar.google.com).",
    )
    parser.add_argument(
        "--only",
        type=str,
        default="",
        help="Comma-separated paper IDs (yaml stem or arXiv ID), e.g. 2506.21734,2602.08864",
    )
    parser.add_argument(
        "--progress",
        dest="progress",
        action="store_true",
        help="Force-enable tqdm progress bars if tqdm is installed.",
    )
    parser.add_argument(
        "--no-progress",
        dest="progress",
        action="store_false",
        help="Disable tqdm progress bars.",
    )
    parser.add_argument(
        "--with-openalex",
        dest="use_openalex",
        action="store_true",
        help="Enable OpenAlex citation fallback (default: enabled).",
    )
    parser.add_argument(
        "--no-openalex",
        dest="use_openalex",
        action="store_false",
        help="Disable OpenAlex citation fallback.",
    )
    parser.add_argument(
        "--with-opencitations",
        dest="use_opencitations",
        action="store_true",
        help="Enable OpenCitations COCI citation fallback (default: enabled).",
    )
    parser.add_argument(
        "--no-opencitations",
        dest="use_opencitations",
        action="store_false",
        help="Disable OpenCitations COCI citation fallback.",
    )
    parser.add_argument(
        "--with-crossref",
        dest="use_crossref",
        action="store_true",
        help="Enable Crossref DOI citation fallback (default: enabled).",
    )
    parser.add_argument(
        "--no-crossref",
        dest="use_crossref",
        action="store_false",
        help="Disable Crossref DOI citation fallback.",
    )
    parser.set_defaults(progress=None, use_openalex=True, use_opencitations=True, use_crossref=True)
    args = parser.parse_args()
    only = {x.strip() for x in args.only.split(",") if x.strip()} or None
    fetch_all(
        dry_run=args.dry_run,
        google_scholar=args.google_scholar,
        scholar_delay_min=args.scholar_delay_min,
        scholar_delay_max=args.scholar_delay_max,
        scholar_endpoint=args.scholar_endpoint,
        only=only,
        progress=args.progress,
        use_openalex=args.use_openalex,
        use_opencitations=args.use_opencitations,
        use_crossref=args.use_crossref,
    )
