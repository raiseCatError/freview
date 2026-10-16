"""Regression fixtures for freview's optional read-only local snapshot."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/freview/scripts/repo_snapshot.py"
SPEC = importlib.util.spec_from_file_location("freview_snapshot", SCRIPT)
SNAPSHOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SNAPSHOT)


def run(cwd, *args):
    return subprocess.run(list(args), cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="freview-test-")
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        run(self.root, "git", "init", "-q", "-b", "main")
        run(self.root, "git", "config", "user.email", "fixture@example.invalid")
        run(self.root, "git", "config", "user.name", "Fixture")
        (self.root / "README.md").write_text("Test repository\n", encoding="utf-8")
        run(self.root, "git", "add", "README.md")
        run(self.root, "git", "commit", "-qm", "initial")

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_repo_and_explicit_base(self):
        result = self.invoke("--base", "main")
        self.assertTrue(result["status"]["clean"])
        self.assertEqual(result["branch"], "main")
        self.assertEqual(result["base"]["divergence"], {"behind": 0, "ahead": 0})
        self.assertTrue(result["community"]["readme"])
        self.assertFalse(result["community"]["security"])
        self.assertEqual(len(result["worktrees"]), 1)

    def test_dirty_repo_keeps_files(self):
        (self.root / "README.md").write_text("Changed\n", encoding="utf-8")
        (self.root / "NOTES.md").write_text("Untracked\n", encoding="utf-8")
        result = self.invoke()
        self.assertEqual(result["status"]["tracked_changes"], 1)
        self.assertEqual(result["status"]["untracked"], 1)
        self.assertFalse(result["status"]["clean"])
        self.assertEqual((self.root / "NOTES.md").read_text(), "Untracked\n")

    def test_separates_staged_unstaged_and_untracked_paths(self):
        (self.root / "README.md").write_text("staged\\n")
        run(self.root, "git", "add", "README.md")
        (self.root / "README.md").write_text("unstaged\\n")
        (self.root / "local-only.txt").write_text("new work\\n")
        result = self.invoke()
        self.assertEqual(result["local_changes"]["staged"]["count"], 1)
        self.assertEqual(result["local_changes"]["unstaged"]["count"], 1)
        self.assertEqual(result["local_changes"]["untracked"]["count"], 1)
        self.assertIn("README.md", result["local_changes"]["staged"]["sample_paths"])
        self.assertIn("README.md", result["local_changes"]["unstaged"]["sample_paths"])
        self.assertIn("local-only.txt", result["local_changes"]["untracked"]["sample_paths"])
        self.assertTrue((self.root / "local-only.txt").exists())

    def test_copied_history_without_upstream_is_not_claimed_published(self):
        run(self.root, "git", "commit", "--allow-empty", "-qm", "local commit")
        result = self.invoke()
        self.assertEqual(result["publishing"]["state"], "no-configured-upstream")
        self.assertFalse(result["publishing"]["remote_publishing_verified"])

    def test_tracking_ahead_is_provisional_and_offline(self):
        remote = Path(self.tmp.name) / "remote.git"
        run(self.root, "git", "init", "-q", "--bare", str(remote))
        run(self.root, "git", "remote", "add", "origin", str(remote))
        run(self.root, "git", "push", "-q", "-u", "origin", "main")
        run(self.root, "git", "commit", "--allow-empty", "-qm", "not pushed to fixture")
        result = self.invoke()
        self.assertEqual(result["publishing"]["ahead"], 1)
        self.assertEqual(result["publishing"]["state"], "local-commits-ahead-of-cached-upstream")
        self.assertFalse(result["publishing"]["remote_publishing_verified"])

    def test_other_worktree_status_is_opt_in_and_bounded(self):
        other = Path(self.tmp.name) / "sibling"
        run(self.root, "git", "worktree", "add", "-qb", "feature/sibling", str(other))
        (other / "untracked-local.txt").write_text("local\\n")
        normal = self.invoke()
        self.assertFalse(normal["other_worktrees_scanned"])
        self.assertEqual(normal["worktree_status_checks"], [])
        inspected = self.invoke("--scan-worktrees", "--max-worktrees", "1")
        self.assertTrue(inspected["other_worktrees_scanned"])
        self.assertEqual(inspected["worktree_status_checks"][0]["status"]["untracked"], 1)

    def test_divergence_calls_are_bounded_across_branch_heads(self):
        for i in range(9):
            run(self.root, "git", "branch", "feature/" + str(i))
        result = self.invoke("--base", "main", "--max-divergences", "1")
        self.assertLessEqual(result["unique_branch_divergences_checked"], 1)
        self.assertEqual(result["branch_divergences_skipped_due_budget"], 0)

    def test_unborn_repo_is_inventoryable_without_claiming_commits(self):
        empty = Path(self.tmp.name) / "unborn"
        empty.mkdir()
        run(empty, "git", "init", "-q", "-b", "main")
        (empty / "initial.txt").write_text("not committed\\n")
        p = subprocess.run([sys.executable, str(SCRIPT), "--json"], cwd=empty,
                           text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        result = json.loads(p.stdout)
        self.assertIsNone(result["head_sha"])
        self.assertEqual(result["publishing"]["state"], "unborn-no-local-commits")
        self.assertEqual(result["local_changes"]["untracked"]["count"], 1)

    def test_multiple_worktrees_reported(self):
        other = Path(self.tmp.name) / "other"
        run(self.root, "git", "worktree", "add", "-qb", "feature/example", str(other))
        result = self.invoke("--base", "main")
        self.assertEqual(len(result["worktrees"]), 2)
        self.assertTrue(any(b["name"] == "feature/example" and b["worktrees"]
                            for b in result["branches"]))

    def test_git_common_dir_identity_is_shared_between_worktrees(self):
        other = Path(self.tmp.name) / "sibling"
        run(self.root, "git", "worktree", "add", "-qb", "feature/sibling", str(other))
        first = self.invoke()
        p = subprocess.run([sys.executable, str(SCRIPT), "--json"], cwd=other,
                           text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        sibling = json.loads(p.stdout)
        self.assertEqual(first["repo_identity"], sibling["repo_identity"])
        self.assertNotEqual(first["root"], sibling["root"])

    def test_explicit_missing_base_fails_without_fallback(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--json",
                            "--base", "definitely-not-a-ref"],
                           cwd=self.root, text=True, capture_output=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("Explicit base ref not available", p.stderr)

    def test_untrusted_fsmonitor_never_executes(self):
        marker = Path(self.tmp.name) / "executed"
        hook = Path(self.tmp.name) / "fsmonitor.sh"
        hook.write_text("#!/bin/sh\nprintf 'hit' >> '" + str(marker) + "'\nexit 0\n")
        hook.chmod(0o700)
        run(self.root, "git", "config", "core.fsmonitor", str(hook))
        result = self.invoke()
        self.assertTrue(result["status"]["clean"])
        self.assertFalse(marker.exists(), "Git fsmonitor hook was executed during read-only audit")

    def test_untrusted_clean_filter_cannot_execute_during_diff(self):
        marker = Path(self.tmp.name) / "executed-clean-filter"
        filter_program = Path(self.tmp.name) / "filter.sh"
        filter_program.write_text(
            "#!/bin/sh\nprintf 'hit' >> '" + str(marker) + "'\ncat\n"
        )
        filter_program.chmod(0o700)
        (self.root / ".gitattributes").write_text("*.data filter=evil\n")
        (self.root / "example.data").write_text("original\n")
        run(self.root, "git", "add", ".gitattributes", "example.data")
        run(self.root, "git", "commit", "-qm", "add filter fixture")
        run(self.root, "git", "config", "filter.evil.clean", str(filter_program))
        (self.root / "example.data").write_text("modified\n")
        result = self.invoke()
        self.assertGreater(result["status"]["tracked_changes"], 0)
        self.assertFalse(marker.exists(), "Git clean filter executed in read-only audit")

    def test_inherited_git_trace_and_config_cannot_execute_or_write(self):
        trace_marker = Path(self.tmp.name) / "unexpected-git-trace"
        hook_marker = Path(self.tmp.name) / "unexpected-hook"
        hook = Path(self.tmp.name) / "environment-hook.sh"
        hook.write_text("#!/bin/sh\nprintf hit >> '" + str(hook_marker) + "'\n")
        hook.chmod(0o700)
        env = os.environ.copy()
        env.update({
            "GIT_TRACE": str(trace_marker),
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.fsmonitor",
            "GIT_CONFIG_VALUE_0": str(hook),
        })
        p = subprocess.run([sys.executable, str(SCRIPT), "--json"],
                           cwd=self.root, env=env, text=True, capture_output=True,
                           timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertFalse(trace_marker.exists(), "Inherited GIT_TRACE wrote a file")
        self.assertFalse(hook_marker.exists(), "Inherited git config ran executable")

    def test_case_sensitive_forge_identity_is_not_folded(self):
        run(self.root, "git", "remote", "add", "origin",
            "https://gitlab.com/ExampleOrg/CaseSensitiveRepo.git")
        got = self.invoke()
        self.assertEqual(
            got["repo_identity"],
            "forge:gitlab.com/ExampleOrg/CaseSensitiveRepo"
        )

    def test_malformed_npm_files_return_unknown_instead_of_crash(self):
        (self.root / "package.json").write_text("[]")
        (self.root / "package-lock.json").write_text("{}")
        self.assertEqual(self.invoke()["npm_root_alignment"]["status"], "unknown")
        (self.root / "package.json").write_text('{"dependencies": []}')
        (self.root / "package-lock.json").write_text(
            '{"lockfileVersion":3,"packages":{"":{"dependencies":{}}}}')
        self.assertEqual(self.invoke()["npm_root_alignment"]["status"], "unknown")
        (self.root / "package.json").write_text('{"dependencies":{}}')
        (self.root / "package-lock.json").write_text('{"packages":{"":[]}}')
        self.assertEqual(self.invoke()["npm_root_alignment"]["status"], "unknown")

    def test_symlinked_npm_metadata_is_not_read(self):
        external = Path(self.tmp.name) / "external-package.json"
        external.write_text('{"dependencies":{"private":"secret"}}')
        (self.root / "package.json").symlink_to(external)
        (self.root / "package-lock.json").write_text(
            '{"packages":{"":{"dependencies":{}}}}')
        result = self.invoke()
        self.assertEqual(result["npm_root_alignment"]["status"], "unknown")
        self.assertNotIn("secret", json.dumps(result))
        self.assertNotIn("private", json.dumps(result["npm_root_alignment"]))

    def test_oversized_npm_metadata_is_not_read(self):
        (self.root / "package.json").write_text("{}")
        (self.root / "package-lock.json").write_text(" " * (16 * 1024 * 1024 + 1))
        result = self.invoke()
        self.assertEqual(result["npm_root_alignment"]["status"], "unknown")
        self.assertIn("size", result["npm_root_alignment"]["reason"])

    def test_npm_lock_drift(self):
        (self.root / "package.json").write_text(
            json.dumps({"dependencies": {"x": "^1.0.0"}}), encoding="utf-8")
        (self.root / "package-lock.json").write_text(
            json.dumps({"lockfileVersion": 3, "packages": {"": {"dependencies": {"x": "^2.0.0"}}}}),
            encoding="utf-8")
        result = self.invoke()
        self.assertEqual(result["npm_root_alignment"]["status"], "drift")

    def invoke(self, *args):
        p = subprocess.run([sys.executable, str(SCRIPT), "--json", *args],
                           cwd=self.root, text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)


if __name__ == "__main__":
    unittest.main()
