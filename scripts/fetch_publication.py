#!/usr/bin/env python3
"""Discover official publication evidence; dry-run by default, --write updates YAML."""

import argparse
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from tempfile import NamedTemporaryFile

try:
    from . import fetch_metrics as metrics
except ImportError:
    import fetch_metrics as metrics

PROCEEDINGS_HOSTS = {"proceedings.mlr.press", "aclanthology.org", "proceedings.neurips.cc", "papers.nips.cc", "openaccess.thecvf.com"}
REQUEST_HOSTS = PROCEEDINGS_HOSTS | {"openreview.net", "api2.openreview.net", "arxiv.org"}


def safe_url(value):
    """Allow only HTTPS metadata hosts, without credentials or unusual ports."""
    try:
        url = urllib.parse.urlsplit(str(value))
        return bool(url.scheme == "https" and url.hostname in REQUEST_HOSTS and not url.username
                    and not url.password and url.port in (None, 443)
                    and not url.path.lower().endswith(".pdf") and url.path != "/pdf")
    except ValueError:
        return False


def official_url(value):
    """Canonicalize recognized proceedings/PDF links without requesting PDFs."""
    try:
        url = urllib.parse.urlsplit(str(value))
        host, path = url.hostname, url.path
        if url.scheme != "https" or url.username or url.password or url.port not in (None, 443):
            return None
        if host == "openreview.net":
            note_id = urllib.parse.parse_qs(url.query).get("id", [""])[0]
            return "https://openreview.net/forum?id=" + note_id if path in ("/forum", "/pdf") and re.fullmatch(r"[\w-]+", note_id) else None
        if host not in PROCEEDINGS_HOSTS:
            return None
        if host == "proceedings.mlr.press":
            path = re.sub(r"^(/v\d+)/([^/]+)/\2\.pdf$", r"\1/\2.html", path)
            if not re.fullmatch(r"/v\d+/[^/]+\.html", path):
                return None
        elif host == "aclanthology.org":
            match = re.fullmatch(r"/([A-Z]\d{2}-\d{4}|\d{4}\.[\w-]+\.\d+)(?:\.pdf|/)?", path)
            if not match:
                return None
            path = "/" + match[1] + "/"
        elif host in {"proceedings.neurips.cc", "papers.nips.cc"}:
            path = path.replace("/file/", "/hash/").replace("-Paper", "-Abstract")
            path = re.sub(r"\.pdf$", ".html", path)
            if not re.fullmatch(r"/(?:paper|paper_files/paper)/\d{4}/hash/[\w-]+-Abstract(?:-Conference)?\.html", path):
                return None
        elif host == "openaccess.thecvf.com":
            path = path.replace("/papers/", "/html/")
            path = re.sub(r"\.pdf$", ".html", path)
            if not re.fullmatch(r"/content/[^?#]+/html/[^/]+\.html", path):
                return None
        return urllib.parse.urlunsplit(("https", host, path, "", ""))
    except ValueError:
        return None


def normalized_title(value):
    """Match Unicode titles exactly after whitespace and punctuation normalization."""
    return " ".join(re.sub(r"[\W_]+", " ", unicodedata.normalize("NFKC", str(value)).casefold()).split())


class CitationHTML(HTMLParser):
    """Collect standard citation metadata and candidate links, never page scripts."""

    def __init__(self, text):
        """Parse one bounded HTML response."""
        super().__init__(convert_charrefs=True)
        self.meta, self.links = {}, []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        """Read only metadata values and link destinations."""
        attrs = dict(attrs)
        if tag == "meta":
            self.meta[str(attrs.get("name", "")).lower()] = attrs.get("content", "")
        elif tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])


def short_venue(value):
    """Shorten main venues while retaining distinct workshop and Findings labels."""
    value = re.sub(r"^Proceedings of (?:the )?", "", str(value).strip(), flags=re.I)
    if "workshop" in value.lower():
        return value
    if "findings" in value.lower():
        match = re.search(r"\b(ACL|EMNLP|NAACL|EACL|AACL)\b", value)
        return "Findings of " + match[1] if match else value
    names = {
        "International Conference on Machine Learning": "ICML",
        "International Conference on Learning Representations": "ICLR",
        "Neural Information Processing Systems": "NeurIPS",
        "Empirical Methods in Natural Language Processing": "EMNLP",
        "Transactions of the Association for Computational Linguistics": "TACL",
        "European Chapter of the Association for Computational Linguistics": "EACL",
        "Asia-Pacific Chapter of the Association for Computational Linguistics": "AACL",
        "North American Chapter of the Association for Computational Linguistics": "NAACL",
        "Computer Vision and Pattern Recognition": "CVPR",
        "International Conference on Computer Vision": "ICCV",
        "Journal of Machine Learning Research": "JMLR",
        "Transactions on Machine Learning Research": "TMLR",
        "Annual Meeting of the Association for Computational Linguistics": "ACL",
    }
    for name, short in names.items():
        if name.lower() in value.lower():
            return short
    match = re.fullmatch(r"(ICML|ICLR|NeurIPS|COLM|ACL|EMNLP|NAACL|EACL|AACL|TACL|CVPR|ICCV|ECCV|TMLR|JMLR)(?:\s+\d{4})?(?:\s+(?:poster|oral|spotlight))?", value, re.I)
    return match[1] if match else value


def verify_html(title, url, text):
    """Require exact title and venue metadata on a supported official landing page."""
    source = official_url(url)
    if not source or urllib.parse.urlsplit(source).hostname not in PROCEEDINGS_HOSTS:
        return None
    meta = CitationHTML(text).meta
    venue = meta.get("citation_conference_title") or meta.get("citation_journal_title")
    if normalized_title(title) and normalized_title(title) == normalized_title(meta.get("citation_title", "")) and venue:
        return {"peer_reviewed": True, "venue": short_venue(venue), "venue_source": source}
    return None


def verify_openreview(title, note):
    """Accept root submission notes with a recognized accepted venue ID, not statuses."""
    if not isinstance(note, dict) or not isinstance(note.get("content"), dict):
        return None
    content = note.get("content") or {}
    content = {key: value.get("value") if isinstance(value, dict) else value for key, value in content.items()}
    venue_id, venue = str(content.get("venueid", "")), str(content.get("venue", ""))
    accepted = re.fullmatch(r"(?:ICLR\.cc|ICML\.cc|NeurIPS\.cc|[Cc][Oo][Ll][Mm]web\.org|robot-learning\.org)/\d{4}/(?:Conference|Workshop/[\w/-]+)", venue_id) or venue_id == "TMLR"
    if (not accepted or note.get("replyto") or note.get("forum") != note.get("id")
            or not re.fullmatch(r"[\w-]+", str(note.get("id", "")))
            or re.search(r"submitted|submission|under.review|rejected|withdrawn", venue_id + " " + venue, re.I)
            or not normalized_title(title) or normalized_title(title) != normalized_title(content.get("title", ""))):
        return None
    if "Workshop/" in venue_id and "workshop" not in venue.lower():
        venue = venue_id.split("/")[0].split(".")[0] + " Workshop " + venue_id.split("Workshop/", 1)[1]
    venue = short_venue(venue or venue_id.split("/")[0].split(".")[0])
    return {"peer_reviewed": True, "venue": venue, "venue_source": "https://openreview.net/forum?id=" + note["id"]}


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    """Keep redirects within the same explicit HTTPS metadata allowlist."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        """Reject redirected PDFs, credentials, private hosts and unknown domains."""
        if not safe_url(newurl):
            raise urllib.error.HTTPError(newurl, code, "Unsafe metadata redirect", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class MetadataClient:
    """Sequential, bounded requests; access denials stop that host for the run."""

    def __init__(self, delay=1.25):
        """Set request spacing without per-provider retry frameworks."""
        self.delay, self.last_request = delay, 0
        self.failures, self.blocked = {}, set()
        self.opener = urllib.request.build_opener(SafeRedirect())

    def get(self, url):
        """Fetch at most 1 MB of HTML/JSON, with no retries or access-control bypass."""
        if not safe_url(url):
            return None
        host = urllib.parse.urlsplit(url).hostname
        key = "openreview.net" if host and host.endswith(".openreview.net") else host
        if key in self.blocked:
            return None
        time.sleep(max(0, self.last_request + self.delay - time.monotonic()))
        self.last_request = time.monotonic()
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Awesome-Loop-Models publication-metadata/1.0"})
            with self.opener.open(request, timeout=12) as response:
                if "pdf" in response.headers.get("Content-Type", "").lower():
                    raise ValueError("PDF response is not metadata")
                data = response.read(1_000_001)
                if len(data) > 1_000_000:
                    raise ValueError("Metadata response exceeds 1 MB")
                text = data.decode("utf-8", "replace")
                result = json.loads(text) if host == "api2.openreview.net" else text
            self.failures[key] = 0
            return result
        except (OSError, ValueError) as error:
            self.failures[key] = self.failures.get(key, 0) + 1
            if getattr(error, "code", None) == 403 or self.failures[key] >= 2:
                self.blocked.add(key)
                reason = f"HTTP {error.code}" if getattr(error, "code", None) else type(error).__name__
                print(f"  [unavailable] {key} ({reason}); skipping remaining requests to this host")
            return None


def doi_candidate(value):
    """Resolve ACL DOIs deterministically without following arbitrary DOI redirects."""
    match = re.search(r"10\.18653/v1/([\w.-]+)", str(value), re.I)
    return official_url("https://aclanthology.org/" + match[1] + "/") if match else None


def discover_publication(paper, metadata, client):
    """Try bounded official candidates, arXiv links, then exact-title OpenReview lookup."""
    title = paper.get("title", "")
    candidates = list((paper.get("links") or {}).values()) + [paper.get("venue_source")]
    candidates += [(metadata.get("openAccessPdf") or {}).get("url"), doi_candidate((metadata.get("externalIds") or {}).get("DOI"))]
    seen = set()
    for phase in range(2):
        for candidate in candidates[:8]:
            url = official_url(candidate)
            if not url or url in seen:
                continue
            seen.add(url)
            if urllib.parse.urlsplit(url).hostname == "openreview.net":
                note_id = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["id"][0]
                payload = client.get("https://api2.openreview.net/notes?" + urllib.parse.urlencode({"id": note_id}))
                for note in payload.get("notes", []) if isinstance(payload, dict) else []:
                    evidence = verify_openreview(title, note)
                    if evidence:
                        return evidence
            else:
                text = client.get(url)
                evidence = verify_html(title, url, text) if isinstance(text, str) else None
                if evidence:
                    return evidence
        if phase == 0:
            arxiv_id = metrics._paper_arxiv_id(paper)
            text = client.get("https://arxiv.org/abs/" + arxiv_id) if arxiv_id and re.fullmatch(r"\d{4}\.\d{4,5}(?:v\d+)?", arxiv_id) else None
            parsed = CitationHTML(text) if isinstance(text, str) else None
            candidates = ([doi_candidate(parsed.meta.get("citation_doi"))]
                          + [official_url(link) or doi_candidate(link) for link in parsed.links
                             if official_url(link) or doi_candidate(link)]) if parsed else []
    payload = client.get("https://api2.openreview.net/notes?" + urllib.parse.urlencode({"content.title": title, "limit": 3}))
    for note in payload.get("notes", []) if isinstance(payload, dict) else []:
        evidence = verify_openreview(title, note)
        if evidence:
            return evidence
    return None


def write_evidence(path, evidence):
    """Change only publication scalar lines, retaining other formatting and comments."""
    if not evidence:
        return False
    original = path.read_text(encoding="utf-8")
    text = original
    for key in ("venue", "peer_reviewed", "venue_source"):
        value = json.dumps(evidence[key], ensure_ascii=False)
        node = next((node for field, node in metrics.yaml.compose(text).value if field.value == key), None)
        if node:
            start, end = node.start_mark.index, node.end_mark.index
            replacement = value + ("\n" if text[start:end].endswith("\n") else "")
            text = text[:start] + replacement + text[end:]
        else:
            text = text.rstrip("\n") + "\n" + key + ": " + value + "\n"
    if text == original:
        return False
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        try:
            output.write(text)
            output.flush()
            temporary.chmod(path.stat().st_mode)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    return True


def main(argv=None):
    """Attempt the selected catalog once, report unknowns and write only on request."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="save verified publication fields")
    parser.add_argument("--only", nargs="+", help="paper stems to check")
    args = parser.parse_args(argv)
    papers = [paper for paper in metrics.load_papers() if not args.only or paper["stem"] in args.only]
    if args.only and set(args.only) - {paper["stem"] for paper in papers}:
        parser.error("Unknown --only paper ID(s): " + ", ".join(sorted(set(args.only) - {paper["stem"] for paper in papers})))
    pending = [paper for paper in papers if not (paper.get("peer_reviewed") is True and paper.get("venue_source"))]
    identifiers = [(paper, metrics._semantic_scholar_ids_for_paper(paper)) for paper in pending]
    identified = [(paper, ids[0]) for paper, ids in identifiers if ids]
    metadata = {}
    for offset in range(0, len(identified), 100):
        if offset:
            time.sleep(1.25)
        batch = identified[offset:offset + 100]
        result = metrics._s2_http_post(metrics.S2_BATCH_URL + "?fields=title,externalIds,openAccessPdf,venue", {"ids": [identifier for _, identifier in batch]}, timeout=15, retries=0)
        if not isinstance(result, list):
            print("  [unavailable] Semantic Scholar discovery; continuing with saved and arXiv links")
            break
        metadata.update({paper["stem"]: item for (paper, _), item in zip(batch, result) if isinstance(item, dict)})
    client, verified, changed = MetadataClient(), 0, 0
    for paper in pending:
        evidence = discover_publication(paper, metadata.get(paper["stem"], {}), client)
        if evidence:
            verified += 1
            changed += bool(args.write and write_evidence(paper["_path"], evidence))
            print(f"  [verified] {paper['stem']}: {evidence['venue']} — {evidence['venue_source']}")
        else:
            print(f"  [unverified] {paper['stem']}: preserving existing publication fields")
    print(f"Publication metadata: {len(papers) - len(pending)} already verified, {verified} newly verified, {len(pending) - verified} unverified; {changed} files written" + (" (dry run)" if not args.write else ""))


if __name__ == "__main__":
    main()
