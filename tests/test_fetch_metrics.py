import json
import ssl
import unittest
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from scripts import fetch_metrics


class SemanticScholarFetchTests(unittest.TestCase):
    def test_semantic_scholar_ids_include_arxiv_and_doi(self):
        paper = {
            "stem": "2403.09629",
            "links": {"arxiv": "https://arxiv.org/abs/2403.09629"},
        }

        self.assertEqual(
            fetch_metrics._semantic_scholar_ids_for_paper(paper),
            [
                "ARXIV:2403.09629",
                "DOI:10.48550/arXiv.2403.09629",
            ],
        )

    def test_paper_doi_candidates_include_explicit_and_arxiv_doi(self):
        paper = {
            "stem": "2403.09629",
            "links": {
                "arxiv": "https://arxiv.org/abs/2403.09629",
                "paper": "https://doi.org/10.1000/test-doi",
            },
        }

        self.assertEqual(
            fetch_metrics._paper_doi_candidates(paper),
            ["10.1000/test-doi", "10.48550/arXiv.2403.09629"],
        )

    def test_title_fallback_preserves_zero_citations(self):
        paper = {"stem": "openreview-chaingpt", "title": "ChainGPT", "year": 2025}

        with mock.patch.object(fetch_metrics, "fetch_citations_batch", return_value={}):
            with mock.patch.object(fetch_metrics, "_fetch_citation_count_via_title_match", return_value=0):
                with mock.patch.object(fetch_metrics, "_fetch_citation_count_via_search") as search_mock:
                    results = fetch_metrics.fetch_citations_semantic_scholar([paper])

        self.assertEqual(results, {"openreview-chaingpt": 0})
        search_mock.assert_not_called()

    def test_title_fallback_uses_search_when_match_missing(self):
        paper = {"stem": "openreview-modr", "title": "MoDr", "year": 2026}

        with mock.patch.object(fetch_metrics, "fetch_citations_batch", return_value={}):
            with mock.patch.object(fetch_metrics, "_fetch_citation_count_via_title_match", return_value=None):
                with mock.patch.object(fetch_metrics, "_fetch_citation_count_via_search", return_value=12):
                    results = fetch_metrics.fetch_citations_semantic_scholar([paper])

        self.assertEqual(results, {"openreview-modr": 12})

    def test_http_get_falls_back_to_curl_on_ssl_error(self):
        ssl_error = urllib.error.URLError(ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED"))
        curl_result = mock.Mock(stdout=b'{"count": 7}', stderr=b'')

        with mock.patch.object(fetch_metrics.urllib.request, "urlopen", side_effect=ssl_error) as urlopen_mock:
            with mock.patch.object(fetch_metrics.subprocess, "run", return_value=curl_result) as run_mock:
                result = fetch_metrics._http_get("https://example.com/api", retries=0)

        self.assertEqual(result, {"count": 7})
        self.assertEqual(urlopen_mock.call_count, 1)
        run_mock.assert_called_once()

    def test_http_get_skips_redundant_retries_for_ssl_errors(self):
        ssl_error = urllib.error.URLError(ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED"))
        curl_result = mock.Mock(stdout=b'{"count": 9}', stderr=b'')

        with mock.patch.object(fetch_metrics.urllib.request, "urlopen", side_effect=ssl_error) as urlopen_mock:
            with mock.patch.object(fetch_metrics.subprocess, "run", return_value=curl_result):
                result = fetch_metrics._http_get("https://example.com/api", retries=3)

        self.assertEqual(result, {"count": 9})
        self.assertEqual(urlopen_mock.call_count, 1)

    def test_fetch_citations_opencitations_preserves_zero_counts(self):
        paper = {
            "stem": "2403.09629",
            "links": {"arxiv": "https://arxiv.org/abs/2403.09629"},
        }

        with mock.patch.object(fetch_metrics, "_fetch_opencitations_for_doi_candidates", return_value=0):
            results = fetch_metrics.fetch_citations_opencitations([paper])

        self.assertEqual(results, {"2403.09629": 0})

    def test_metrics_cache_roundtrip_preserves_values(self):
        with TemporaryDirectory() as tmp_dir:
            cache_path = Path(tmp_dir) / "fetch_metrics_cache.json"
            cache = fetch_metrics._load_metrics_cache(cache_path)

            fetch_metrics._cache_store(cache, "2403.09629", "citations", "openalex", 7)
            fetch_metrics._cache_store(cache, "2403.09629", "stars", "github", 42)
            fetch_metrics._save_metrics_cache(cache, cache_path)

            loaded = fetch_metrics._load_metrics_cache(cache_path)
            citation_hit, citation_value = fetch_metrics._cache_lookup(
                loaded,
                "2403.09629",
                "citations",
                "openalex",
                success_ttl_days=7,
                miss_ttl_hours=12,
            )
            star_hit, star_value = fetch_metrics._cache_lookup(
                loaded,
                "2403.09629",
                "stars",
                "github",
                success_ttl_days=3,
                miss_ttl_hours=12,
            )

        self.assertEqual((citation_hit, citation_value), (True, 7))
        self.assertEqual((star_hit, star_value), (True, 42))

    def test_fetch_citations_openalex_uses_fresh_cache_before_network(self):
        paper = {
            "stem": "2403.09629",
            "links": {"arxiv": "https://arxiv.org/abs/2403.09629"},
        }
        cache = {
            "version": 1,
            "papers": {
                "2403.09629": {
                    "citations": {
                        "openalex": {
                            "value": 5,
                            "fetched_at": "2099-01-01T00:00:00+00:00",
                        }
                    }
                }
            },
        }

        with mock.patch.object(fetch_metrics, "_fetch_openalex_for_doi_candidates") as fetch_mock:
            results = fetch_metrics.fetch_citations_openalex(
                [paper],
                cache=cache,
                cache_ttl_days=7,
            )

        self.assertEqual(results, {"2403.09629": 5})
        fetch_mock.assert_not_called()

    def test_parse_github_stars_from_html_handles_k_suffix(self):
        html = '<a href="/owner/repo/stargazers">1.6k stars</a>'
        self.assertEqual(fetch_metrics._parse_github_stars_from_html(html), 1600)

    def test_get_github_stars_falls_back_to_html_when_api_missing(self):
        html = '<a href="/owner/repo/stargazers">987 stars</a>'
        with mock.patch.object(fetch_metrics, "_http_get", return_value=None):
            with mock.patch.object(fetch_metrics, "_http_get_text", return_value=html) as text_mock:
                stars = fetch_metrics.get_github_stars("https://github.com/owner/repo")

        self.assertEqual(stars, 987)
        text_mock.assert_called_once()

    def test_fetch_stars_parallel_defaults_cached_source_to_github_api(self):
        paper = {
            "stem": "2403.09629",
            "links": {"github": "https://github.com/owner/repo"},
        }
        cache = {
            "version": 1,
            "papers": {
                "2403.09629": {
                    "stars": {
                        "github": {
                            "value": 42,
                            "fetched_at": "2099-01-01T00:00:00+00:00"
                        }
                    }
                }
            },
        }

        stars_map, star_source_maps, broken_links = fetch_metrics.fetch_stars_parallel(
            [paper],
            cache=cache,
            cache_ttl_days=7,
        )

        self.assertEqual(stars_map, {"2403.09629": 42})
        self.assertEqual(star_source_maps, {"2403.09629": {"github_api": 42}})
        self.assertEqual(broken_links, [])

    def test_fetch_all_persists_star_provenance_and_broken_link_report(self):
        with TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            papers_dir = repo_root / "papers"
            papers_dir.mkdir()
            cache_dir = repo_root / ".cache"
            cache_file = cache_dir / "fetch_metrics_cache.json"
            report_file = cache_dir / "github_link_report.json"

            good_path = papers_dir / "2403.09629.yaml"
            good_path.write_text(
                "title: Test Paper\n"
                "year: 2024\n"
                "links:\n"
                "  arxiv: https://arxiv.org/abs/2403.09629\n"
                "  github: https://github.com/owner/repo\n",
                encoding="utf-8",
            )
            broken_path = papers_dir / "broken-paper.yaml"
            broken_path.write_text(
                "title: Broken Paper\n"
                "year: 2024\n"
                "links:\n"
                "  github: https://github.com/owner/missing\n",
                encoding="utf-8",
            )

            with mock.patch.object(fetch_metrics, "PAPERS_DIR", papers_dir):
                with mock.patch.object(fetch_metrics, "CACHE_DIR", cache_dir):
                    with mock.patch.object(fetch_metrics, "CACHE_FILE", cache_file):
                        with mock.patch.object(fetch_metrics, "GITHUB_LINK_REPORT_FILE", report_file):
                            with mock.patch.object(fetch_metrics, "fetch_citations_semantic_scholar", return_value={}):
                                with mock.patch.object(fetch_metrics, "fetch_citations_openalex", return_value={}):
                                    with mock.patch.object(fetch_metrics, "fetch_citations_opencitations", return_value={}):
                                        with mock.patch.object(fetch_metrics, "fetch_citations_crossref", return_value={}):
                                            with mock.patch.object(
                                                fetch_metrics,
                                                "fetch_stars_parallel",
                                                return_value=(
                                                    {"2403.09629": 321},
                                                    {"2403.09629": {"github_api": 321}},
                                                    [{
                                                        "stem": "broken-paper",
                                                        "url": "https://github.com/owner/missing",
                                                        "reason": "github_repo_404",
                                                    }],
                                                ),
                                            ):
                                                fetch_metrics.fetch_all(
                                                    dry_run=False,
                                                    progress=False,
                                                    google_scholar=False,
                                                    use_openalex=True,
                                                    use_opencitations=True,
                                                    use_crossref=True,
                                                )

            updated = fetch_metrics.yaml.safe_load(good_path.read_text(encoding="utf-8"))
            report_data = json.loads(report_file.read_text(encoding="utf-8"))

        self.assertEqual(updated["github_stars"], 321)
        self.assertEqual(updated["star_sources"], {"github_api": 321})
        self.assertEqual(updated["star_source_best"], "github_api")
        self.assertEqual(report_data["broken_links"][0]["stem"], "broken-paper")

    def test_fetch_all_persists_citation_provenance(self):
        with TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            papers_dir = repo_root / "papers"
            papers_dir.mkdir()
            cache_dir = repo_root / ".cache"
            cache_file = cache_dir / "fetch_metrics_cache.json"
            paper_path = papers_dir / "2403.09629.yaml"
            paper_path.write_text(
                "title: Test Paper\n"
                "year: 2024\n"
                "links:\n"
                "  arxiv: https://arxiv.org/abs/2403.09629\n",
                encoding="utf-8",
            )

            with mock.patch.object(fetch_metrics, "PAPERS_DIR", papers_dir):
                with mock.patch.object(fetch_metrics, "CACHE_DIR", cache_dir):
                    with mock.patch.object(fetch_metrics, "CACHE_FILE", cache_file):
                        with mock.patch.object(fetch_metrics, "fetch_citations_semantic_scholar", return_value={"2403.09629": 5}):
                            with mock.patch.object(fetch_metrics, "fetch_citations_openalex", return_value={"2403.09629": 7}):
                                with mock.patch.object(fetch_metrics, "fetch_citations_opencitations", return_value={"2403.09629": 6}):
                                        with mock.patch.object(fetch_metrics, "fetch_citations_crossref", return_value={}):
                                            with mock.patch.object(fetch_metrics, "fetch_stars_parallel", return_value=({}, {}, [])):
                                                fetch_metrics.fetch_all(
                                                    dry_run=False,
                                                    progress=False,
                                                    google_scholar=False,
                                                    use_openalex=True,
                                                    use_opencitations=True,
                                                    use_crossref=True,
                                                )

            updated = fetch_metrics.yaml.safe_load(paper_path.read_text(encoding="utf-8"))
            cache_data = json.loads(cache_file.read_text(encoding="utf-8"))

        self.assertEqual(updated["citations"], 7)
        self.assertEqual(
            updated["citation_sources"],
            {
                "semantic_scholar": 5,
                "openalex": 7,
                "opencitations": 6,
            },
        )
        self.assertEqual(updated["citation_source_best"], "openalex")
        self.assertEqual(cache_data["version"], 1)

    def test_fetch_all_applies_source_corrections_and_preserves_failed_citation_provenance(self):
        """Apply fresh corrections while retaining failed citation provenance."""
        with TemporaryDirectory() as tmp_dir:
            papers_dir = Path(tmp_dir) / "papers"
            papers_dir.mkdir()
            paper_path = papers_dir / "2403.09629.yaml"
            original = (
                "title: Test Paper\n"
                "year: 2024\n"
                "links:\n"
                "  arxiv: https://arxiv.org/abs/2403.09629\n"
                "  github: https://github.com/owner/repo\n"
                "citations: 9\n"
                "citation_sources:\n"
                "  semantic_scholar: 9\n"
                "  openalex: 6\n"
                "citation_source_best: semantic_scholar\n"
                "github_stars: 42\n"
                "star_sources:\n"
                "  github_api: 42\n"
                "  github_html: 41\n"
                "star_source_best: github_api\n"
                "metrics_updated: '2026-08-01'\n"
            ).encode()
            paper_path.write_bytes(original)

            with (
                mock.patch.object(fetch_metrics, "PAPERS_DIR", papers_dir),
                mock.patch.object(fetch_metrics, "CACHE_FILE", Path(tmp_dir) / "cache.json"),
                mock.patch.object(
                    fetch_metrics,
                    "GITHUB_LINK_REPORT_FILE",
                    Path(tmp_dir) / "github-links.json",
                ),
                mock.patch.object(
                    fetch_metrics,
                    "fetch_citations_semantic_scholar",
                    return_value={"2403.09629": 5},
                ),
                mock.patch.object(fetch_metrics, "fetch_citations_openalex", return_value={}),
                mock.patch.object(fetch_metrics, "fetch_citations_opencitations", return_value={}),
                mock.patch.object(fetch_metrics, "fetch_citations_crossref", return_value={}),
                mock.patch.object(
                    fetch_metrics,
                    "fetch_stars_parallel",
                    return_value=(
                        {"2403.09629": 40},
                        {"2403.09629": {"github_api": 40}},
                        [],
                    ),
                ),
                mock.patch.object(
                    fetch_metrics,
                    "_utcnow",
                    return_value=datetime(2026, 9, 3, tzinfo=timezone.utc),
                ),
                mock.patch.object(fetch_metrics, "_save_metrics_cache"),
                mock.patch.object(fetch_metrics, "_save_github_link_report"),
            ):
                fetch_metrics.fetch_all(progress=False)

            updated_bytes = paper_path.read_bytes()
            updated = fetch_metrics.yaml.safe_load(updated_bytes)

        self.assertNotEqual(updated_bytes, original)
        self.assertEqual(updated["citations"], 6)
        self.assertEqual(
            updated["citation_sources"],
            {"semantic_scholar": 5, "openalex": 6},
        )
        self.assertEqual(updated["citation_source_best"], "openalex")
        self.assertEqual(updated["github_stars"], 40)
        self.assertEqual(updated["star_sources"], {"github_api": 40})
        self.assertEqual(updated["star_source_best"], "github_api")
        self.assertEqual(updated["metrics_updated"], "2026-09-03")

    def test_fetch_all_preserves_legacy_aggregates_during_partial_and_total_outages(self):
        """Retain unsupported legacy metrics across lower results and outages."""
        with TemporaryDirectory() as tmp_dir:
            papers_dir = Path(tmp_dir) / "papers"
            papers_dir.mkdir()
            paper_path = papers_dir / "legacy-paper.yaml"
            original = (
                "title: Legacy Paper\n"
                "year: 2024\n"
                "links:\n"
                "  arxiv: https://arxiv.org/abs/2403.09629\n"
                "  github: https://github.com/owner/repo\n"
                "citations: 7\n"
                "github_stars: 42\n"
                "metrics_updated: '2026-08-01'\n"
            ).encode()
            paper_path.write_bytes(original)
            outage_path = papers_dir / "outage-paper.yaml"
            outage_original = (
                "title: Outage Paper\n"
                "year: 2024\n"
                "links:\n"
                "  arxiv: https://arxiv.org/abs/2403.09630\n"
                "  github: https://github.com/owner/outage\n"
                "citations: 3\n"
                "citation_sources:\n"
                "  semantic_scholar: 3\n"
                "citation_source_best: semantic_scholar\n"
                "github_stars: 5\n"
                "star_sources:\n"
                "  github_api: 5\n"
                "star_source_best: github_api\n"
                "metrics_updated: '2026-08-02'\n"
            ).encode()
            outage_path.write_bytes(outage_original)
            unsupported_path = papers_dir / "unsupported-paper.yaml"
            unsupported_original = (
                "title: Unsupported Legacy Metrics\n"
                "year: 2024\n"
                "links:\n"
                "  arxiv: https://arxiv.org/abs/2403.09631\n"
                "  github: https://github.com/owner/unsupported\n"
                "citations: 10\n"
                "citation_sources:\n"
                "  semantic_scholar: 8\n"
                "citation_source_best: semantic_scholar\n"
                "github_stars: 50\n"
                "metrics_updated: '2026-08-03'\n"
            ).encode()
            unsupported_path.write_bytes(unsupported_original)

            with (
                mock.patch.object(fetch_metrics, "PAPERS_DIR", papers_dir),
                mock.patch.object(fetch_metrics, "CACHE_FILE", Path(tmp_dir) / "cache.json"),
                mock.patch.object(
                    fetch_metrics,
                    "GITHUB_LINK_REPORT_FILE",
                    Path(tmp_dir) / "github-links.json",
                ),
                mock.patch.object(
                    fetch_metrics,
                    "fetch_citations_semantic_scholar",
                    return_value={"legacy-paper": 6, "unsupported-paper": 7},
                ),
                mock.patch.object(fetch_metrics, "fetch_citations_openalex", return_value={}),
                mock.patch.object(fetch_metrics, "fetch_citations_opencitations", return_value={}),
                mock.patch.object(fetch_metrics, "fetch_citations_crossref", return_value={}),
                mock.patch.object(
                    fetch_metrics,
                    "fetch_stars_parallel",
                    return_value=(
                        {"legacy-paper": 40, "unsupported-paper": 44},
                        {
                            "legacy-paper": {"github_html": 40},
                            "unsupported-paper": {"github_api": 44},
                        },
                        [],
                    ),
                ),
                mock.patch.object(
                    fetch_metrics,
                    "_utcnow",
                    return_value=datetime(2026, 9, 3, tzinfo=timezone.utc),
                ),
                mock.patch.object(fetch_metrics, "_save_metrics_cache"),
                mock.patch.object(fetch_metrics, "_save_github_link_report"),
            ):
                fetch_metrics.fetch_all(progress=False)

            updated_bytes = paper_path.read_bytes()
            updated = fetch_metrics.yaml.safe_load(updated_bytes)
            outage_bytes = outage_path.read_bytes()
            outage = fetch_metrics.yaml.safe_load(outage_bytes)
            unsupported_bytes = unsupported_path.read_bytes()
            unsupported = fetch_metrics.yaml.safe_load(unsupported_bytes)

        self.assertNotEqual(updated_bytes, original)
        self.assertEqual(updated["citations"], 7)
        self.assertEqual(updated["citation_sources"], {"semantic_scholar": 6})
        self.assertNotIn("citation_source_best", updated)
        self.assertEqual(updated["github_stars"], 40)
        self.assertEqual(updated["star_sources"], {"github_html": 40})
        self.assertEqual(updated["star_source_best"], "github_html")
        self.assertEqual(updated["metrics_updated"], "2026-09-03")
        self.assertEqual(outage_bytes, outage_original)
        self.assertEqual(outage["metrics_updated"], "2026-08-02")
        self.assertEqual(outage["citation_sources"], {"semantic_scholar": 3})
        self.assertEqual(outage["citation_source_best"], "semantic_scholar")
        self.assertEqual(outage["star_sources"], {"github_api": 5})
        self.assertEqual(outage["star_source_best"], "github_api")
        self.assertNotEqual(unsupported_bytes, unsupported_original)
        self.assertEqual(unsupported["citations"], 10)
        self.assertEqual(unsupported["citation_sources"], {"semantic_scholar": 7})
        self.assertNotIn("citation_source_best", unsupported)
        self.assertEqual(unsupported["github_stars"], 44)
        self.assertEqual(unsupported["star_sources"], {"github_api": 44})
        self.assertEqual(unsupported["star_source_best"], "github_api")
        self.assertEqual(unsupported["metrics_updated"], "2026-09-03")

    def test_fetch_all_strict_fails_before_writes_for_known_zero_metrics(self):
        """Treat zero as known and abort strict refreshes before any write."""
        with TemporaryDirectory() as tmp_dir:
            papers_dir = Path(tmp_dir) / "papers"
            papers_dir.mkdir()
            paper_path = papers_dir / "zero-metrics.yaml"
            original = (
                "title: Zero Metrics\n"
                "year: 2026\n"
                "links:\n"
                "  arxiv: https://arxiv.org/abs/2601.00001\n"
                "  github: https://github.com/owner/repo\n"
                "citations: 0\n"
                "github_stars: 0\n"
                "metrics_updated: '2026-08-01'\n"
            ).encode()
            paper_path.write_bytes(original)

            with (
                mock.patch.object(fetch_metrics, "PAPERS_DIR", papers_dir),
                mock.patch.object(fetch_metrics, "CACHE_FILE", Path(tmp_dir) / "cache.json"),
                mock.patch.object(
                    fetch_metrics,
                    "GITHUB_LINK_REPORT_FILE",
                    Path(tmp_dir) / "github-links.json",
                ),
                mock.patch.object(fetch_metrics, "fetch_citations_semantic_scholar", return_value={}),
                mock.patch.object(fetch_metrics, "fetch_citations_openalex", return_value={}),
                mock.patch.object(fetch_metrics, "fetch_citations_opencitations", return_value={}),
                mock.patch.object(fetch_metrics, "fetch_citations_crossref", return_value={}),
                mock.patch.object(fetch_metrics, "fetch_stars_parallel", return_value=({}, {}, [])),
                mock.patch.object(fetch_metrics, "_save_metrics_cache") as cache_writer,
                mock.patch.object(fetch_metrics, "_save_github_link_report") as report_writer,
            ):
                with self.assertRaises(RuntimeError) as raised:
                    fetch_metrics.fetch_all(progress=False, strict=True)

            updated_bytes = paper_path.read_bytes()

        self.assertIn("zero-metrics: citations", str(raised.exception))
        self.assertIn("zero-metrics: github_stars", str(raised.exception))
        self.assertEqual(updated_bytes, original)
        cache_writer.assert_not_called()
        report_writer.assert_not_called()

    def test_fetch_all_strict_allows_new_paper_without_metrics(self):
        """Allow strict refreshes when a new paper has no known metric values."""
        with TemporaryDirectory() as tmp_dir:
            papers_dir = Path(tmp_dir) / "papers"
            papers_dir.mkdir()
            paper_path = papers_dir / "new-paper.yaml"
            original = (
                "title: New Paper\n"
                "year: 2026\n"
                "links:\n"
                "  arxiv: https://arxiv.org/abs/2601.00002\n"
                "  github: https://github.com/owner/new-repo\n"
            ).encode()
            paper_path.write_bytes(original)

            with (
                mock.patch.object(fetch_metrics, "PAPERS_DIR", papers_dir),
                mock.patch.object(fetch_metrics, "CACHE_FILE", Path(tmp_dir) / "cache.json"),
                mock.patch.object(
                    fetch_metrics,
                    "GITHUB_LINK_REPORT_FILE",
                    Path(tmp_dir) / "github-links.json",
                ),
                mock.patch.object(fetch_metrics, "fetch_citations_semantic_scholar", return_value={}),
                mock.patch.object(fetch_metrics, "fetch_citations_openalex", return_value={}),
                mock.patch.object(fetch_metrics, "fetch_citations_opencitations", return_value={}),
                mock.patch.object(fetch_metrics, "fetch_citations_crossref", return_value={}),
                mock.patch.object(fetch_metrics, "fetch_stars_parallel", return_value=({}, {}, [])),
                mock.patch.object(fetch_metrics, "_load_metrics_cache") as cache_loader,
                mock.patch.object(fetch_metrics, "_save_metrics_cache") as cache_writer,
                mock.patch.object(fetch_metrics, "_save_github_link_report") as report_writer,
            ):
                fetch_metrics.fetch_all(progress=False, strict=True)

            updated_bytes = paper_path.read_bytes()

        self.assertEqual(updated_bytes, original)
        cache_loader.assert_not_called()
        cache_writer.assert_not_called()
        report_writer.assert_called_once()

    def test_load_dotenv_file_sets_missing_values_only(self):
        with TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / ".env"
            env_file.write_text(
                "SEMANTIC_SCHOLAR_API_KEY=from-dotenv\n"
                "SEMANTIC_SCHOLAR_MIN_INTERVAL_SECONDS='1.50'\n"
                "EXISTING_VALUE=from-dotenv\n",
                encoding="utf-8",
            )

            with mock.patch.dict(
                fetch_metrics.os.environ,
                {"EXISTING_VALUE": "already-set"},
                clear=False,
            ):
                fetch_metrics._load_dotenv_file(env_file)
                self.assertEqual(fetch_metrics.os.environ["SEMANTIC_SCHOLAR_API_KEY"], "from-dotenv")
                self.assertEqual(fetch_metrics.os.environ["SEMANTIC_SCHOLAR_MIN_INTERVAL_SECONDS"], "1.50")
                self.assertEqual(fetch_metrics.os.environ["EXISTING_VALUE"], "already-set")


if __name__ == "__main__":
    unittest.main()
