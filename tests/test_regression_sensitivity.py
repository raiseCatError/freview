"""TDD contract: optional baseline regression sensitivity on disposable snapshots."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/freview/scripts/ops.py"
spec = importlib.util.spec_from_file_location("freview_ops_regression", SCRIPT)
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)


def git(cwd, *argv):
    return subprocess.run(["git", *argv], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


class BaselineSensitivityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="freview-sensitivity-")
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.scratch = self.root / "scratch"
        self.repo.mkdir()
        self.scratch.mkdir()
        git(self.repo, "init", "-qb", "feature/fix")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        git(self.repo, "config", "user.name", "Fixture")
        (self.repo / "number.py").write_text("def get_number():\n    return 1\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "baseline")
        self.base = git(self.repo, "rev-parse", "HEAD")
        (self.repo / "number.py").write_text("def get_number():\n    return 2\n")
        tests = self.repo / "tests"
        tests.mkdir()
        (tests / "test_number.py").write_text(
            "import unittest\nfrom number import get_number\n"
            "class Numbers(unittest.TestCase):\n"
            "    def test_number(self): self.assertEqual(get_number(), 2)\n"
        )
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "fixed")
        self.head = git(self.repo, "rev-parse", "HEAD")
        self.policy = ops.validate_policy({"schema_version": 1,
            "modules": {"tests": True, "regression": True},
            "commands": {"tests": [sys.executable, "-m", "unittest", "discover", "-s", "tests"]},
            "limits": {"timeout_seconds": 15, "max_output_bytes": 8192, "max_rounds": 2}})

    def tearDown(self):
        self.temp.cleanup()

    def test_catches_baseline_failure_with_candidate_tests(self):
        result = ops.regression_sensitivity(
            self.policy, self.repo, self.scratch,
            base_sha=self.base, test_paths=["tests/test_number.py"],
            expected_sha=self.head, allow_execute=True)
        self.assertEqual(result["status"], "baseline-failure-observed")
        self.assertEqual(result["candidate"]["status"], "passed")
        self.assertEqual(result["baseline"]["status"], "failed")
        self.assertFalse(result["proves_test_quality"])
        self.assertEqual((self.repo / "number.py").read_text(),
                         "def get_number():\n    return 2\n")

    def test_sensitivity_requires_explicit_approval_and_test_paths(self):
        with self.assertRaises(ops.OpsError):
            ops.regression_sensitivity(self.policy, self.repo, self.scratch,
                base_sha=self.base, test_paths=["tests/test_number.py"])
        with self.assertRaises(ops.OpsError):
            ops.regression_sensitivity(self.policy, self.repo, self.scratch,
                base_sha=self.base, test_paths=["../number.py"], allow_execute=True)

    def test_missing_baseline_is_not_silently_replaced(self):
        with self.assertRaises(ops.OpsError):
            ops.regression_sensitivity(self.policy, self.repo, self.scratch,
                base_sha="0" * 40, test_paths=["tests/test_number.py"],
                allow_execute=True, expected_sha=self.head)


if __name__ == "__main__":
    unittest.main()
