"""A recovered pipeline checkpoint is an observation, never a replay permission."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/freview/scripts/ops.py"
spec = importlib.util.spec_from_file_location("ops_checkpoint_contract", SCRIPT)
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, text=True, check=True,
                          capture_output=True).stdout.strip()


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="freview-checkpoint-")
        self.repo = Path(self.tmp.name) / "repo"
        self.scratch = Path(self.tmp.name) / "scratch"
        self.repo.mkdir()
        self.scratch.mkdir()
        git(self.repo, "init", "-qb", "feature/checkpoint")
        git(self.repo, "config", "user.name", "Fixture")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        (self.repo / "src.py").write_text("def get(): return 1\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "start")
        self.sha = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self):
        self.tmp.cleanup()

    def policy(self, fail=False):
        return ops.validate_policy({"schema_version": 1,
            "modules": {"tests": True},
            "commands": {"tests": [sys.executable, "-c",
                                  "raise SystemExit(4)" if fail else "print('pass')"]},
            "limits": {"timeout_seconds": 10, "max_output_bytes": 4096,
                       "max_rounds": 2}})

    def test_success_pipeline_leaves_atomic_readable_summary(self):
        result = ops.pipeline(self.policy(), self.repo, self.scratch,
                              allow_execute=True, expected_sha=self.sha,
                              requirements="Return correct value", rounds=2)
        path = Path(result["checkpoint_path"])
        self.assertTrue(path.is_file())
        # macOS can canonicalize /var to /private/var for scratch.
        self.assertTrue(path.resolve().is_relative_to(self.scratch.resolve()))
        summary = ops.inspect_checkpoint(path)
        self.assertEqual(summary["source_sha"], self.sha)
        self.assertEqual(summary["status"], "complete")
        self.assertEqual(summary["verdict"], result["verdict"])
        self.assertEqual(len(summary["stage_receipts"]), 1)
        self.assertTrue(summary["untrusted_metadata"])
        self.assertFalse(summary["resumes_execution"])
        self.assertFalse(summary["attested"])

    def test_failed_pipeline_preserves_diagnostic_without_resuming(self):
        result = ops.pipeline(self.policy(fail=True), self.repo, self.scratch,
                              allow_execute=True, expected_sha=self.sha,
                              requirements="Return correct value")
        summary = ops.inspect_checkpoint(Path(result["checkpoint_path"]))
        self.assertEqual(summary["verdict"], "tests-failed")
        self.assertEqual(summary["stage_receipts"][0]["status"], "failed")
        self.assertFalse(summary["resumes_execution"])
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_no_policy_can_run_or_write_checkpoint(self):
        disabled = ops.validate_policy({"schema_version": 1})
        with self.assertRaises(ops.OpsError):
            ops.pipeline(disabled, self.repo, self.scratch, allow_execute=True,
                         requirements="not authorized")
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_bad_checkpoint_symlink_invalid_and_oversized_are_rejected(self):
        file = self.scratch / "manifest.json"
        file.write_text('{"status":"complete"}')
        with self.assertRaises(ops.OpsError):
            ops.inspect_checkpoint(file)
        link = self.scratch / "link.json"
        link.symlink_to(file)
        with self.assertRaises(ops.OpsError):
            ops.inspect_checkpoint(link)
        file.write_bytes(b"x" * 70000)
        with self.assertRaises(ops.OpsError):
            ops.inspect_checkpoint(file)

    def test_status_cli_does_not_create_scratch_or_execute_tests(self):
        output = subprocess.run([sys.executable, str(SCRIPT), "status",
                                 "--repo", str(self.repo)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(output.returncode, 0, output.stderr)
        self.assertEqual(list(self.scratch.iterdir()), [])

if __name__ == "__main__":
    unittest.main()
