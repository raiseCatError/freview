"""Config, mode and JSON report fixtures; no external packages or network calls."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / "skills/freview/scripts/review.py"


def run(cwd, *args, ok=True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=20)
    if ok and p.returncode:
        raise AssertionError(p.stderr)
    return p


class ReviewCLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="freview-review-")
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        run(self.root, "git", "init", "-q", "-b", "main")
        run(self.root, "git", "config", "user.email", "fixture@example.invalid")
        run(self.root, "git", "config", "user.name", "Fixture")
        (self.root / "README.md").write_text("Hello\n")
        run(self.root, "git", "add", "README.md")
        run(self.root, "git", "commit", "-qm", "initial")

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, *args, ok=True):
        return run(self.root, sys.executable, str(CLI), *args, ok=ok)

    def report(self, *args):
        return json.loads(self.call("--format", "json", *args).stdout)

    def test_standard_default_has_no_code_review(self):
        report = self.report()
        self.assertEqual(report["report_kind"], "local-snapshot")
        self.assertEqual(report["mode_requested"], "standard")
        self.assertNotIn("code-review", report["scope"]["included"])
        self.assertNotIn("security-scan", report["scope"]["included"])
        self.assertTrue(report["not_observed"])

    def test_full_includes_code_but_does_not_run_it(self):
        report = self.report("--mode", "full")
        self.assertIn("code-review", report["scope"]["included"])
        self.assertEqual(report["scope"]["specialists"]["code-review"], "agent-review-required")
        self.assertEqual(report["report_kind"], "local-snapshot")

    def test_project_config_and_precedence(self):
        policy = {"schema_version": 1,
                  "repository": {"development_branch": "main"},
                  "defaults": {"mode": "full", "exclude": ["ci"]},
                  "specialists": {"code_review": "off"}}
        (self.root / ".freview.json").write_text(json.dumps(policy))
        report = self.report()
        self.assertEqual(report["mode_requested"], "full")
        self.assertNotIn("code-review", report["scope"]["included"])
        self.assertNotIn("ci", report["scope"]["included"])
        report = self.report("--mode", "standard", "--with", "code-review")
        self.assertEqual(report["mode_requested"], "standard")
        self.assertIn("code-review", report["scope"]["included"])
        report = self.report("--mode", "full", "--with", "code-review", "--exclude", "code-review")
        self.assertNotIn("code-review", report["scope"]["included"])

    def test_only_selection(self):
        report = self.report("--only", "git,releases")
        self.assertEqual(report["scope"]["included"], ["git", "releases"])

    def test_unknown_keys_fail_and_no_output_written(self):
        (self.root / ".freview.json").write_text('{"schema_version":1,"execute":"rm -rf"}')
        p = self.call("--format", "json", ok=False)
        self.assertEqual(p.returncode, 2)
        self.assertIn("Unexpected top-level", p.stderr)
        self.assertEqual(list(self.root.glob("freview*.json")), [])

    def test_invalid_values_fail(self):
        (self.root / ".freview.json").write_text(
            '{"schema_version": 1, "limits": {"max_branches": 0}}')
        self.assertEqual(self.call(ok=False).returncode, 2)

    def test_explicit_output_requires_new_path(self):
        outfile = Path(self.tmp.name) / "report.json"
        self.call("--format", "json", "--output", str(outfile))
        self.assertEqual(json.loads(outfile.read_text())["report_kind"], "local-snapshot")
        self.assertEqual(self.call("--output", str(outfile), ok=False).returncode, 2)

    def test_unknown_category_refuses(self):
        self.assertEqual(self.call("--exclude", "wizardry", ok=False).returncode, 2)

    def test_no_repo_mutation_in_default_mode(self):
        before = run(self.root, "git", "status", "--porcelain").stdout
        self.call("--mode", "standard")
        after = run(self.root, "git", "status", "--porcelain").stdout
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
