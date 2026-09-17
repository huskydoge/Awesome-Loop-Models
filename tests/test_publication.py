"""Offline checks for conservative publication evidence and focused YAML writes."""

import importlib.util
import contextlib
import io
import unittest
import urllib.error
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock


class PublicationTests(unittest.TestCase):
    """Only official, title-matched publication evidence can update a paper."""

    def publication(self):
        """Report the missing implementation as a deliberate failing assertion."""
        self.assertIsNotNone(importlib.util.find_spec("scripts.fetch_publication"))
        from scripts import fetch_publication
        return fetch_publication

    def test_official_landing_urls_reject_untrusted_and_pdf_targets(self):
        """Known PDF paths become metadata pages; unknown hosts never get fetched."""
        p = self.publication()
        cases = {
            "https://proceedings.mlr.press/v139/bai21b/bai21b.pdf": "https://proceedings.mlr.press/v139/bai21b.html",
            "https://aclanthology.org/2026.findings-acl.2103.pdf": "https://aclanthology.org/2026.findings-acl.2103/",
            "https://proceedings.neurips.cc/paper_files/paper/2024/file/abc-Paper-Conference.pdf": "https://proceedings.neurips.cc/paper_files/paper/2024/hash/abc-Abstract-Conference.html",
            "https://openaccess.thecvf.com/content/CVPR2024/papers/Smith_Loops_CVPR_2024_paper.pdf": "https://openaccess.thecvf.com/content/CVPR2024/html/Smith_Loops_CVPR_2024_paper.html",
            "https://openreview.net/pdf?id=abc": "https://openreview.net/forum?id=abc",
        }
        for raw, expected in cases.items():
            self.assertEqual(p.official_url(raw), expected)
        for raw in ("http://proceedings.mlr.press/v1/a.html", "https://aclanthology.org.evil.test/p", "https://u@aclanthology.org/p", "https://127.0.0.1/p", "https://aclanthology.org:444/p", "https://aclanthology.org/unknown.pdf"):
            self.assertIsNone(p.official_url(raw))

    def test_official_metadata_requires_matching_title_and_venue(self):
        """Punctuation normalization is allowed, but fuzzy-title matches are not."""
        p = self.publication()
        html = '<meta content="Loop Models: A Study" name="citation_title"><meta name="citation_conference_title" content="Proceedings of the 41st International Conference on Machine Learning">'
        result = p.verify_html("Loop Models - A Study", "https://proceedings.mlr.press/v235/a24.html", html)
        self.assertEqual(result, {"peer_reviewed": True, "venue": "ICML", "venue_source": "https://proceedings.mlr.press/v235/a24.html"})
        self.assertIsNone(p.verify_html("Loop Models: Another Study", result["venue_source"], html))
        self.assertIsNone(p.verify_html("Loop Models: A Study", result["venue_source"], '<meta name="citation_title" content="Loop Models: A Study">'))
        self.assertIsNone(p.verify_html("Loop Models: A Study", "https://example.com/p", html))

    def test_workshops_and_findings_keep_distinct_venues(self):
        """A workshop must never silently turn into the parent main conference."""
        p = self.publication()
        self.assertEqual(p.short_venue("Findings of the Association for Computational Linguistics: ACL 2026"), "Findings of ACL")
        self.assertEqual(p.short_venue("Proceedings of the ICML 2025 Workshop on Looped Models"), "ICML 2025 Workshop on Looped Models")

    def test_specific_acl_venues_precede_main_conference_without_guessing_unknowns(self):
        """Related journals and chapters remain distinct from the main ACL meeting."""
        p = self.publication()
        cases = {
            "Transactions of the Association for Computational Linguistics": "TACL",
            "Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics": "EACL",
            "Proceedings of the 4th Conference of the Asia-Pacific Chapter of the Association for Computational Linguistics": "AACL",
            "Proceedings of the 2025 Conference of the North American Chapter of the Association for Computational Linguistics": "NAACL",
            "Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics": "ACL",
            "Findings of the Association for Computational Linguistics: AACL 2025": "Findings of AACL",
            "Association for Computational Linguistics Newsletter": "Association for Computational Linguistics Newsletter",
            "Example joint ACL research meeting": "Example joint ACL research meeting",
        }
        for venue, expected in cases.items():
            with self.subTest(venue=venue):
                self.assertEqual(p.short_venue(venue), expected)

    def test_openreview_acceptance_not_submission_or_replies(self):
        """Accepted venue IDs are authoritative; submissions and reply notes are not."""
        p = self.publication()
        note = {"id": "abc", "forum": "abc", "content": {"title": {"value": "Loop Models"}, "venueid": {"value": "ICLR.cc/2025/Conference"}, "venue": {"value": "ICLR 2025 poster"}}}
        self.assertEqual(p.verify_openreview("Loop Models", note)["venue"], "ICLR")
        for venueid in ("ICLR.cc/2025/Conference/Submission", "ICLR.cc/2025/Conference/Rejected_Submission", "ICLR.cc/2025/Conference/Withdrawn_Submission", "unknown/2025/Conference"):
            altered = {**note, "content": {**note["content"], "venueid": {"value": venueid}}}
            self.assertIsNone(p.verify_openreview("Loop Models", altered))
        self.assertIsNone(p.verify_openreview("Different paper", note))
        self.assertIsNone(p.verify_openreview("Loop Models", {**note, "replyto": "parent"}))
        self.assertIsNone(p.verify_openreview("Loop Models", {**note, "forum": "parent"}))
        workshop = {**note, "content": {**note["content"], "venueid": "ICLR.cc/2025/Workshop/Loop", "venue": "ICLR 2025 Workshop on Loop Models"}}
        self.assertIn("Workshop", p.verify_openreview("Loop Models", workshop)["venue"])

    def test_blocked_host_is_not_retried_or_bypassed(self):
        """One 403 stops OpenReview requests for the remainder of the run."""
        p = self.publication()
        client = p.MetadataClient(delay=0)
        error = urllib.error.HTTPError("https://api2.openreview.net/notes", 403, "Forbidden", {}, None)
        with mock.patch.object(client.opener, "open", side_effect=error) as request:
            self.assertIsNone(client.get("https://api2.openreview.net/notes?id=a"))
            self.assertIsNone(client.get("https://api2.openreview.net/notes?id=b"))
            self.assertEqual(request.call_count, 1)
        with self.assertRaises(urllib.error.HTTPError):
            p.SafeRedirect().redirect_request(None, None, 302, "", {}, "https://evil.test/metadata")

    def test_write_preserves_unrelated_yaml_and_is_idempotent(self):
        """Only the three publication fields change; null discoveries never write."""
        p = self.publication()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "paper.yaml"
            original = "# Keep this note\ntitle: 'Loop Models'\nvenue: arXiv # checked later\ndesc: >\n  My manually formatted text.\nlinks:\n  arxiv: https://arxiv.org/abs/2501.00001\n"
            path.write_text(original)
            evidence = {"venue": "ICML", "peer_reviewed": True, "venue_source": "https://proceedings.mlr.press/v235/a24.html"}
            self.assertFalse(p.write_evidence(path, None))
            self.assertEqual(path.read_text(), original)
            self.assertTrue(p.write_evidence(path, evidence))
            updated = path.read_text()
            self.assertIn("venue: \"ICML\" # checked later\n", updated)
            self.assertIn("desc: >\n  My manually formatted text.\n", updated)
            self.assertEqual(updated.count("peer_reviewed:"), 1)
            self.assertFalse(p.write_evidence(path, evidence))

    def test_write_replaces_yaml_scalars_without_mistaking_quoted_hash_for_comment(self):
        """Quoted hashes and multiline venue values cannot corrupt the updated YAML."""
        p = self.publication()
        evidence = {"venue": "ICML", "peer_reviewed": True, "venue_source": "https://proceedings.mlr.press/v235/a24.html"}
        with TemporaryDirectory() as directory:
            path = Path(directory) / "paper.yaml"
            for original in ('venue: "Workshop #1" # keep\ntitle: Loop\n', 'venue: >\n  Some workshop\ntitle: Loop\n'):
                path.write_text(original)
                p.write_evidence(path, evidence)
                self.assertEqual(p.metrics.yaml.safe_load(path.read_text())["venue"], "ICML")
                self.assertIn("title: Loop\n", path.read_text())
            path.write_text('venue: "Workshop #1" # keep\n')
            p.write_evidence(path, evidence)
            self.assertIn('venue: "ICML" # keep\n', path.read_text())

    def test_bad_responses_and_unknown_only_are_safe(self):
        """A malformed API response is unknown, not a crash or a verified paper."""
        p = self.publication()
        client = mock.Mock()
        client.get.return_value = [{"unexpected": "response"}]
        self.assertIsNone(p.discover_publication({"title": "Loop", "links": {"openreview": "https://openreview.net/forum?id=abc"}}, {}, client))
        self.assertIsNone(p.MetadataClient(delay=0).get("https://[malformed"))
        with mock.patch.object(p.metrics, "load_papers", return_value=[]):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                p.main(["--only", "nonexistent-paper"])

    def test_two_failures_stop_host_and_large_or_pdf_responses_are_not_read(self):
        """Bound provider failures and reject document bodies before download."""
        p = self.publication()
        client = p.MetadataClient(delay=0)
        with mock.patch.object(client.opener, "open", side_effect=TimeoutError("timed out")) as request:
            for identifier in range(3):
                self.assertIsNone(client.get(f"https://arxiv.org/abs/2501.0000{identifier}"))
            self.assertEqual(request.call_count, 2)
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.headers = {"Content-Type": "application/pdf"}
        client = p.MetadataClient(delay=0)
        with mock.patch.object(client.opener, "open", return_value=response):
            self.assertIsNone(client.get("https://aclanthology.org/2025.acl-long.12/"))
            response.read.assert_not_called()

    def test_arxiv_doi_links_are_candidates_not_evidence(self):
        """An arXiv journal DOI still needs matching official proceedings metadata."""
        p = self.publication()
        paper = {"title": "Loop Models", "stem": "2501.00001", "links": {}}
        client = mock.Mock()
        responses = {
            "https://arxiv.org/abs/2501.00001": '<a href="https://doi.org/10.18653/v1/2025.acl-long.12">Journal reference</a>',
            "https://aclanthology.org/2025.acl-long.12/": '<meta name="citation_title" content="Loop Models"><meta name="citation_conference_title" content="Proceedings of ACL 2025">',
        }
        client.get.side_effect = responses.get
        evidence = p.discover_publication(paper, {}, client)
        self.assertIsNotNone(evidence)
        self.assertEqual(evidence["venue"], "ACL")

    def test_default_dry_run_does_not_write_and_skips_verified_records(self):
        """Saved evidence is retained and writes require an explicit --write flag."""
        p = self.publication()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "paper.yaml"
            original = "title: Loop Models\nvenue: arXiv\n"
            path.write_text(original)
            paper = {"stem": "sample", "title": "Loop Models", "_path": path, "links": {"paper": "https://proceedings.mlr.press/v235/a24.html"}}
            verified = {"stem": "verified", "peer_reviewed": True, "venue_source": "https://proceedings.mlr.press/v235/b24.html"}
            html = '<meta name="citation_title" content="Loop Models"><meta name="citation_conference_title" content="ICML 2024">'
            with mock.patch.object(p.metrics, "load_papers", return_value=[paper, verified]), mock.patch.object(p.MetadataClient, "get", return_value=html) as request, contextlib.redirect_stdout(io.StringIO()):
                p.main([])
                self.assertEqual(path.read_text(), original)
                self.assertEqual(request.call_count, 1)
                p.main(["--only", "sample", "--write"])
            self.assertIn("peer_reviewed: true", path.read_text())

    def test_s2_batches_are_spaced_even_without_an_api_key(self):
        """Discovery must remain rate-limited when the reused S2 helper is not."""
        p = self.publication()
        papers = [{"stem": f"2501.{index:05d}", "title": "Loop Models"} for index in range(101)]
        with mock.patch.object(p.metrics, "load_papers", return_value=papers), mock.patch.object(p.metrics, "_s2_http_post", return_value=[None] * 100) as batch, mock.patch.object(p.MetadataClient, "get", return_value=None), mock.patch.object(p.time, "sleep") as sleep, contextlib.redirect_stdout(io.StringIO()):
            p.main([])
            self.assertEqual(batch.call_count, 2)
            sleep.assert_called_once_with(1.25)

    def test_discovery_checks_official_candidates_not_s2_venue(self):
        """Secondary metadata supplies candidates, never an acceptance decision."""
        p = self.publication()
        paper = {"title": "Loop Models", "stem": "2501.00001", "links": {}}
        client = mock.Mock()
        client.get.return_value = None
        self.assertIsNone(p.discover_publication(paper, {"venue": "ICML"}, client))
        metadata = {"externalIds": {"DOI": "10.18653/v1/2025.acl-long.12"}}
        client.get.side_effect = lambda url: '<meta name="citation_title" content="Loop Models"><meta name="citation_conference_title" content="Proceedings of ACL 2025">' if "aclanthology.org" in url else None
        self.assertEqual(p.discover_publication(paper, metadata, client)["venue_source"], "https://aclanthology.org/2025.acl-long.12/")


if __name__ == "__main__":
    unittest.main()
