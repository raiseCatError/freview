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

    def test_multiple_worktrees_reported(self):
        other = Path(self.tmp.name) / "other"
        run(self.root, "git", "worktree", "add", "-qb", "feature/example", str(other))
        result = self.invoke("--base", "main")
        self.assertEqual(len(result["worktrees"]), 2)
        self.assertTrue(any(b["name"] == "feature/example" and b["worktrees"]
                            for b in result["branches"]))

    def test_explicit_missing_base_fails_without_fallback(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--json",
                            "--base", "definitely-not-a-ref"],
                           cwd=self.root, text=True, capture_output=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("Explicit base ref not available", p.stderr)

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
