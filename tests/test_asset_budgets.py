"""Contract tests for deterministic static-site asset budgets."""

from __future__ import annotations

import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from scripts import check_asset_budgets


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "build-papers.yml"
UPDATE_METRICS_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "update-metrics.yml"


def write_json(path: Path, payload: object) -> None:
    """Write a deterministic JSON fixture to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def valid_briefing(date: str = "2026-07-10") -> dict:
    """Return the minimal complete browser briefing schema."""
    return {
        "date": date,
        "title": "Latest briefing",
        "status": "published",
        "summary": "A concise reader-facing summary.",
        "source_path": f"briefings/{date[:4]}/{date[5:7]}/{date}.md",
        "highlights": [],
        "candidates": [],
    }


def valid_papers_payload() -> dict:
    """Return the minimal complete browser catalog schema."""
    return {
        "meta": {},
        "categories": {},
        "mechanism_tags": [],
        "focus_tags": [],
        "papers": [],
        "blogs": [],
        "briefings": [valid_briefing()],
    }


def write_valid_fixture(root: Path) -> None:
    """Create the smallest valid repository fixture for the budget checker."""
    write_json(root / "papers.json", valid_papers_payload())
    write_json(
        root / "submission-meta.json",
        {
            "existing_paths": [],
            "tag_inventories": {
                "mechanism": [],
                "focus": [],
                "domain": [],
            },
        },
    )
    favicon_path = root / "assets" / "favicon.png"
    favicon_path.parent.mkdir(parents=True, exist_ok=True)
    favicon_path.write_bytes(b"fixture favicon")


def deterministic_noise(length: int) -> str:
    """Return deterministic, poorly compressible ASCII text of ``length`` characters."""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    state = 0xC0FFEE
    characters = []
    for _ in range(length):
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        characters.append(alphabet[state % len(alphabet)])
    return "".join(characters)


def measurement(report: check_asset_budgets.AssetBudgetReport, name: str) -> int | None:
    """Return the measured value for ``name`` from an asset-budget report."""
    return next(item.measured for item in report.measurements if item.name == name)


class AssetBudgetContractTests(unittest.TestCase):
    """Exercise every byte and schema contract enforced by the checker."""

    def test_valid_fixture_passes_every_budget(self):
        """A minimal valid fixture should satisfy every configured budget."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_valid_fixture(root)

            report = check_asset_budgets.check_asset_budgets(root)

        self.assertTrue(report.ok, report.violations)
        self.assertEqual(
            {item.name for item in report.measurements},
            {
                "papers.json deterministic gzip bytes",
                "papers.json briefing count",
                "papers.json briefing content fields",
                "submission-meta.json raw bytes",
                "assets/favicon.png raw bytes",
            },
        )

    def test_rejects_papers_gzip_bytes_over_limit(self):
        """The deterministic gzip budget should catch a high-entropy catalog."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_valid_fixture(root)
            payload = valid_papers_payload()
            payload["padding"] = deterministic_noise(140_000)
            write_json(root / "papers.json", payload)

            report = check_asset_budgets.check_asset_budgets(root)

        self.assertGreater(
            measurement(report, "papers.json deterministic gzip bytes"),
            check_asset_budgets.PAPERS_GZIP_BYTES_LIMIT,
        )
        self.assertIn("papers.json deterministic gzip bytes", "\n".join(report.violations))

    def test_rejects_submission_metadata_over_limit(self):
        """Oversized but schema-valid submission metadata should fail its byte budget."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_valid_fixture(root)
            write_json(
                root / "submission-meta.json",
                {
                    "existing_paths": [f"papers/{index:05d}.yaml" for index in range(1_500)],
                    "tag_inventories": {
                        "mechanism": [],
                        "focus": [],
                        "domain": [],
                    },
                },
            )

            report = check_asset_budgets.check_asset_budgets(root)

        self.assertGreater(
            measurement(report, "submission-meta.json raw bytes"),
            check_asset_budgets.SUBMISSION_META_BYTES_LIMIT,
        )
        self.assertIn("submission-meta.json raw bytes", "\n".join(report.violations))

    def test_rejects_favicon_over_limit(self):
        """An oversized favicon should fail without affecting JSON validation."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_valid_fixture(root)
            (root / "assets" / "favicon.png").write_bytes(
                b"x" * (check_asset_budgets.FAVICON_BYTES_LIMIT + 1)
            )

            report = check_asset_budgets.check_asset_budgets(root)

        self.assertIn("assets/favicon.png raw bytes", "\n".join(report.violations))

    def test_rejects_more_than_one_browser_briefing(self):
        """The browser payload should contain at most the latest briefing."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_valid_fixture(root)
            payload = valid_papers_payload()
            payload["briefings"] = [valid_briefing("2026-07-10"), valid_briefing("2026-07-09")]
            write_json(
                root / "papers.json",
                payload,
            )

            report = check_asset_budgets.check_asset_budgets(root)

        self.assertEqual(measurement(report, "papers.json briefing count"), 2)
        self.assertIn("papers.json briefing count", "\n".join(report.violations))

    def test_rejects_briefing_content_field(self):
        """Rendered briefing Markdown must stay out of the browser catalog."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_valid_fixture(root)
            payload = valid_papers_payload()
            payload["briefings"][0]["content"] = "Too much text"
            write_json(root / "papers.json", payload)

            report = check_asset_budgets.check_asset_budgets(root)

        self.assertEqual(measurement(report, "papers.json briefing content fields"), 1)
        self.assertIn("must not contain a 'content' field", "\n".join(report.violations))

    def test_rejects_nested_briefing_content_field(self):
        """No nested candidate or metadata object may restore full briefing content."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_valid_fixture(root)
            payload = valid_papers_payload()
            payload["briefings"][0]["candidates"] = [
                {"title": "Candidate", "details": {"content": "Hidden Markdown"}}
            ]
            write_json(root / "papers.json", payload)

            report = check_asset_budgets.check_asset_budgets(root)

        self.assertEqual(measurement(report, "papers.json briefing content fields"), 1)
        self.assertIn("must not contain a 'content' field", "\n".join(report.violations))

    def test_rejects_missing_required_browser_root_fields(self):
        """Every browser-consumed top-level catalog field must be present."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_valid_fixture(root)
            write_json(root / "papers.json", {"briefings": []})

            report = check_asset_budgets.check_asset_budgets(root)

        violations = "\n".join(report.violations)
        for field in ("meta", "categories", "mechanism_tags", "focus_tags", "papers", "blogs"):
            with self.subTest(field=field):
                self.assertIn(f"papers.json.{field}", violations)

    def test_rejects_wrong_browser_root_field_types(self):
        """Browser-consumed objects and arrays must retain their expected root types."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_valid_fixture(root)
            payload = valid_papers_payload()
            payload.update(
                {
                    "meta": [],
                    "categories": [],
                    "mechanism_tags": {},
                    "focus_tags": {},
                    "papers": {},
                    "blogs": {},
                    "briefings": {},
                }
            )
            write_json(root / "papers.json", payload)

            report = check_asset_budgets.check_asset_budgets(root)

        violations = "\n".join(report.violations)
        self.assertIn("papers.json.meta must be an object", violations)
        self.assertIn("papers.json.categories must be an object", violations)
        for field in ("mechanism_tags", "focus_tags", "papers", "blogs", "briefings"):
            with self.subTest(field=field):
                self.assertIn(f"papers.json.{field} must be an array", violations)

    def test_rejects_invalid_briefing_field_types(self):
        """Required briefing scalar, highlight, and candidate fields must match the UI schema."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_valid_fixture(root)
            payload = valid_papers_payload()
            payload["briefings"] = [
                {
                    "date": 20260710,
                    "title": None,
                    "status": [],
                    "summary": {},
                    "source_path": False,
                    "highlights": ["valid", 3],
                    "candidates": [{"title": "valid"}, "invalid"],
                }
            ]
            write_json(root / "papers.json", payload)

            report = check_asset_budgets.check_asset_budgets(root)

        violations = "\n".join(report.violations)
        for field in ("date", "title", "status", "summary", "source_path"):
            with self.subTest(field=field):
                self.assertIn(f"papers.json.briefings[0].{field} must be a string", violations)
        self.assertIn("papers.json.briefings[0].highlights[1] must be a string", violations)
        self.assertIn("papers.json.briefings[0].candidates[1] must be an object", violations)

    def test_reports_missing_and_malformed_json_clearly(self):
        """Missing and malformed JSON files should be reported in one run."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_valid_fixture(root)
            (root / "papers.json").unlink()
            (root / "submission-meta.json").write_text("{not-json", encoding="utf-8")

            report = check_asset_budgets.check_asset_budgets(root)

        violations = "\n".join(report.violations)
        self.assertIn("papers.json: missing required file", violations)
        self.assertIn("submission-meta.json: invalid JSON", violations)

    def test_reports_all_schema_violations_in_one_run(self):
        """Invalid top-level and submission schemas should not stop later checks."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_valid_fixture(root)
            write_json(root / "papers.json", [])
            write_json(root / "submission-meta.json", {"existing_paths": "not-a-list"})

            report = check_asset_budgets.check_asset_budgets(root)

        violations = "\n".join(report.violations)
        self.assertIn("papers.json: top-level JSON value must be an object", violations)
        self.assertIn("submission-meta.json.existing_paths must be an array", violations)
        self.assertIn("submission-meta.json.tag_inventories must be an object", violations)

    def test_cli_prints_measurements_and_returns_zero_on_success(self):
        """The CLI should print measured/limit rows and return zero on success."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_valid_fixture(root)
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                exit_code = check_asset_budgets.main(["--root", str(root)])

        rendered = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("measured=", rendered)
        self.assertIn("limit=", rendered)
        self.assertIn("Asset budgets: PASS", rendered)

    def test_cli_lists_all_violations_and_returns_nonzero(self):
        """The CLI should aggregate failures and return nonzero when any budget fails."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_valid_fixture(root)
            payload = valid_papers_payload()
            first = valid_briefing()
            first["content"] = "first"
            second = valid_briefing("2026-07-09")
            second["content"] = "second"
            payload["briefings"] = [first, second]
            write_json(
                root / "papers.json",
                payload,
            )
            (root / "assets" / "favicon.png").write_bytes(
                b"x" * (check_asset_budgets.FAVICON_BYTES_LIMIT + 1)
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                exit_code = check_asset_budgets.main(["--root", str(root)])

        rendered = output.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("papers.json briefing count", rendered)
        self.assertIn("must not contain a 'content' field", rendered)
        self.assertIn("assets/favicon.png raw bytes", rendered)
        self.assertIn("Asset budgets: FAIL", rendered)

    def test_workflow_runs_generation_budgets_and_tests_on_pull_requests(self):
        """PR CI should run offline generation and gates while keeping network and writes guarded."""
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        steps = workflow["jobs"]["build"]["steps"]
        steps_by_name = {step["name"]: step for step in steps}

        offline_gate_commands = {
            "Build papers.json, submission-meta.json, README.md, and TAGS.md": "python3 scripts/build.py",
            "Check static asset budgets": "python3 scripts/check_asset_budgets.py",
            "Run unit tests": "python3 -m unittest discover -s tests -t . -p 'test_*.py'",
        }
        for name, command in offline_gate_commands.items():
            with self.subTest(step=name):
                self.assertEqual(steps_by_name[name]["run"], command)
                self.assertNotIn("if", steps_by_name[name])

        for name in (
            "Require Semantic Scholar API key",
            "Fetch citation counts and GitHub stars",
        ):
            with self.subTest(step=name):
                self.assertEqual(
                    steps_by_name[name]["if"],
                    "${{ github.event_name != 'pull_request' }}",
                )
        commit_condition = steps_by_name["Commit metrics and generated files (on main only)"]["if"]
        self.assertIn("github.event_name != 'pull_request'", commit_condition)
        self.assertIn("github.ref == 'refs/heads/main'", commit_condition)
        self.assertIn(
            "git add -f papers.json submission-meta.json README.md TAGS.md",
            steps_by_name["Commit metrics and generated files (on main only)"]["run"],
        )

    def test_metric_workflow_commits_submission_metadata(self):
        """Scheduled rebuilds should publish every generated browser dependency."""
        workflow = yaml.safe_load(UPDATE_METRICS_WORKFLOW_PATH.read_text(encoding="utf-8"))
        steps = workflow["jobs"]["update-metrics"]["steps"]
        commit_step = next(step for step in steps if step["name"] == "Commit updated metrics")

        self.assertIn(
            "git add -f papers.json submission-meta.json README.md TAGS.md",
            commit_step["run"],
        )


if __name__ == "__main__":
    unittest.main()
