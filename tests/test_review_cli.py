"""Config, mode and JSON report fixtures; no external packages or network calls."""
import json
import stat
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

    def test_python_isolated_mode_loads_bundled_snapshot_without_path_fallback(self):
        # Regression: python -I removes CLI's sibling script directory from
        # sys.path, so ordinary 'from repo_snapshot import ...' used to fail.
        for mode in ("quick", "standard", "full"):
            with self.subTest(mode=mode):
                result = run(self.root, sys.executable, "-I", str(CLI),
                             "--mode", mode, "--format", "json")
                report = json.loads(result.stdout)
                self.assertEqual(report["mode_requested"], mode)
                self.assertEqual(report["report_kind"], "local-snapshot")
                self.assertIn("head_sha", report["repository"])
                self.assertIn("local_snapshot", report)

    def test_isolated_cli_from_unrelated_directory_does_not_import_repo_modules(self):
        # The CLI should load its paired helper, not anything from cwd.
        (self.root / "repo_snapshot.py").write_text(
            "raise RuntimeError('untrusted working directory imported')\\n")
        result = run(self.root, sys.executable, "-I", str(CLI),
                     "--mode", "quick", "--format", "json")
        report = json.loads(result.stdout)
        self.assertEqual(report["report_kind"], "local-snapshot")
        self.assertNotIn("untrusted working directory imported", result.stderr)

    def test_standard_default_has_no_code_review(self):
        report = self.report()
        self.assertEqual(report["report_kind"], "local-snapshot")
        self.assertEqual(report["mode_requested"], "standard")
        self.assertNotIn("code-review", report["scope"]["included"])
        self.assertNotIn("implementation", report["scope"]["included"])
        self.assertNotIn("security-scan", report["scope"]["included"])
        self.assertTrue(report["not_observed"])

    def test_full_includes_code_but_does_not_run_it(self):
        report = self.report("--mode", "full")
        self.assertIn("code-review", report["scope"]["included"])
        self.assertIn("implementation", report["scope"]["included"])
        self.assertEqual(report["scope"]["specialists"]["code-review"], "agent-review-required")
        self.assertEqual(report["report_kind"], "local-snapshot")

    def test_project_config_and_precedence(self):
        policy = {"schema_version": 1,
                  "repository": {"development_branch": "main"},
                  "defaults": {"mode": "full", "exclude": ["ci"]},
                  "specialists": {"code_review": "off"}}
        (self.root / ".freview.json").write_text(json.dumps(policy))
        report = self.report()
        self.assertEqual(report["mode_requested"], "standard")
        self.assertNotIn("code-review", report["scope"]["included"])
        self.assertNotIn("implementation", report["scope"]["included"])
        self.assertNotIn("ci", report["scope"]["included"])
        report = self.report("--mode", "full")
        self.assertIn("code-review", report["scope"]["included"])
        report = self.report("--mode", "standard", "--with", "code-review")
        self.assertEqual(report["mode_requested"], "standard")
        self.assertIn("code-review", report["scope"]["included"])
        report = self.report("--mode", "full", "--with", "code-review", "--exclude", "code-review")
        self.assertNotIn("code-review", report["scope"]["included"])

    def test_implementation_suggestions_are_explicit_opt_in(self):
        self.assertFalse(self.report()["implementation_suggestions_requested"])
        with_suggestions = self.report("--suggest-implementation")
        self.assertTrue(with_suggestions["implementation_suggestions_requested"])
        self.assertEqual(with_suggestions["report_kind"], "local-snapshot")

    def test_local_findings_include_non_executed_fix_plan(self):
        (self.root / "NOTES.md").write_text("Work in progress\n")
        report = self.report()
        self.assertTrue(report["remediation_plan"])
        self.assertTrue(report["remediation_plan"][0]["requires_approval"])
        self.assertTrue(report["findings"][0]["remediation"]["steps"])

    def test_repo_cannot_enable_implementation_in_daily_mode(self):
        (self.root / ".freview.json").write_text(json.dumps({
            "schema_version": 1,
            "defaults": {"include": ["implementation", "code-review", "security-scan"]}
        }))
        report = self.report()
        self.assertNotIn("implementation", report["scope"]["included"])
        self.assertNotIn("code-review", report["scope"]["included"])
        self.assertNotIn("security-scan", report["scope"]["included"])
        requested = self.report("--with", "implementation")
        self.assertIn("implementation", requested["scope"]["included"])
        scanner = self.report("--with", "security-scan")
        self.assertIn("security-scan", scanner["scope"]["included"])

    def test_explicit_full_not_narrowed_by_project_config(self):
        (self.root / ".freview.json").write_text(json.dumps({
            "schema_version": 1,
            "defaults": {"exclude": ["ci", "security-posture", "tracking"]}
        }))
        default_report = self.report()
        self.assertNotIn("ci", default_report["scope"]["included"])
        full = self.report("--mode", "full")
        for check in ("ci", "security-posture", "tracking", "code-review"):
            self.assertIn(check, full["scope"]["included"])
        explicit_standard = self.report("--mode", "standard")
        self.assertIn("ci", explicit_standard["scope"]["included"])
        excluded = self.report("--mode", "full", "--exclude", "ci")
        self.assertNotIn("ci", excluded["scope"]["included"])

    def test_remote_identity_never_leaks_credentials(self):
        run(self.root, "git", "remote", "add", "origin",
            "https://hidden-token@example.com/company/project.git")
        unknown = self.report()
        self.assertIsNone(unknown["repository"]["remote"])
        self.assertNotIn("hidden-token", json.dumps(unknown))
        run(self.root, "git", "remote", "set-url", "origin",
            "git@github.com:ExampleOrg/ExampleRepo.git")
        known = self.report()
        self.assertEqual(known["repository"]["identity"],
                         "forge:github.com/exampleorg/examplerepo")
        self.assertEqual(known["repository"]["remote"],
                         "https://github.com/ExampleOrg/ExampleRepo")

    def test_project_full_default_cannot_escalate_unattended_mode(self):
        (self.root / ".freview.json").write_text(json.dumps({
            "schema_version": 1,
            "defaults": {"mode": "full", "include": ["implementation", "code-review", "security-scan"]}
        }))
        report = self.report()
        self.assertEqual(report["mode_requested"], "standard")
        self.assertNotIn("code-review", report["scope"]["included"])
        self.assertNotIn("implementation", report["scope"]["included"])
        self.assertNotIn("security-scan", report["scope"]["included"])
        full = self.report("--mode", "full")
        self.assertIn("code-review", full["scope"]["included"])

    def test_project_config_symlink_requires_explicit_selection(self):
        outside = Path(self.tmp.name) / "outside.json"
        outside.write_text('{"schema_version": 1}')
        (self.root / ".freview.json").symlink_to(outside)
        denied = self.call("--format", "json", ok=False)
        self.assertEqual(denied.returncode, 2)
        self.assertIn("symlink", denied.stderr)
        approved = self.report("--config", str(outside))
        self.assertEqual(approved["mode_requested"], "standard")

    def test_explicit_only_security_scan_beats_project_preference(self):
        (self.root / ".freview.json").write_text(json.dumps({
            "schema_version": 1, "specialists": {"security_scan": "off"}
        }))
        report = self.report("--only", "security-scan")
        self.assertEqual(report["scope"]["included"], ["security-scan"])
        self.assertEqual(report["scope"]["specialists"]["security-scan"], "agent-review-required")

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
        self.assertEqual(stat.S_IMODE(outfile.stat().st_mode), 0o600)
        self.assertEqual(self.call("--output", str(outfile), ok=False).returncode, 2)

    def test_only_git_skips_dependency_and_community_file_inspection(self):
        (self.root / "package.json").write_text('{"dependencies":{"x":"1"}}')
        (self.root / "package-lock.json").write_text('{"packages":{"":{"dependencies":{"x":"2"}}}}')
        git_only = self.report("--only", "git")
        self.assertEqual(git_only["scope"]["included"], ["git"])
        self.assertTrue(git_only["local_snapshot"]["npm_root_alignment"]["not_checked"])
        self.assertEqual(git_only["local_snapshot"]["ecosystems_root_only"], {})
        self.assertEqual(git_only["local_snapshot"]["community"], {})
        with_deps = self.report("--only", "dependencies")
        self.assertEqual(with_deps["local_snapshot"]["npm_root_alignment"]["status"], "drift")

    def test_unknown_category_refuses(self):
        self.assertEqual(self.call("--exclude", "wizardry", ok=False).returncode, 2)

    def test_no_repo_mutation_in_default_mode(self):
        before = run(self.root, "git", "status", "--porcelain").stdout
        self.call("--mode", "standard")
        after = run(self.root, "git", "status", "--porcelain").stdout
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
