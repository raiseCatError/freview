"""Test-first quality guarantees for freview's disposable verification stages.

All programs are fake local Python processes. No provider tokens or network.
"""
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/freview/scripts/ops.py"
spec = importlib.util.spec_from_file_location("freview_ops_quality", SCRIPT)
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, text=True,
                          capture_output=True, check=True).stdout.strip()


class IsolationContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="freview-quality-")
        self.repo = Path(self.temp.name) / "repo"
        self.scratch = Path(self.temp.name) / "scratch"
        self.repo.mkdir()
        self.scratch.mkdir()
        git(self.repo, "init", "-qb", "feature/isolation")
        git(self.repo, "config", "user.name", "Fixture")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "module.py").write_text("VALUE=1\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "initial")
        self.sha = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self):
        self.temp.cleanup()

    def policy(self, *, tests, reviewer=None, mutation=None, shipping=True):
        modules = {"tests": True, "shipping": shipping}
        commands = {"tests": [sys.executable, "-c", tests]}
        if reviewer:
            modules["adversarial"] = True
            commands["adversarial"] = [sys.executable, "-c", reviewer]
        if mutation:
            modules["mutation"] = True
            commands["mutation"] = [sys.executable, "-c", mutation]
        return ops.validate_policy({
            "schema_version": 1, "modules": modules, "commands": commands,
            "limits": {"timeout_seconds": 12, "max_output_bytes": 8192,
                       "max_rounds": 2}
        })

    def run(self, policy):
        return ops.pipeline(policy, self.repo, self.scratch,
                            allow_execute=True, expected_sha=self.sha,
                            requirements="Evaluate src/module.py without modifying source")

    def test_test_generated_cache_does_not_poison_candidate_or_shipping(self):
        script = ("from pathlib import Path;"
                  "Path('__pycache__').mkdir();"
                  "Path('__pycache__/module.pyc').write_bytes(b'cache');"
                  "print('pass')")
        result = self.run(self.policy(tests=script))
        self.assertEqual(result["verdict"], "checks-executed-without-authenticated-verdict")
        self.assertFalse(result["workspace_modified"])
        self.assertIsNotNone(result["shipping"])
        self.assertFalse((Path(result["scratch_workspace"]) / "__pycache__").exists())
        self.assertEqual(result["executions"][0]["status"], "passed")
        self.assertTrue(result["executions"][0]["workspace_modified"])

    def test_test_that_overwrites_source_is_not_a_valid_gate(self):
        script = ("from pathlib import Path;"
                  "Path('src/module.py').write_text('FAKE=1');"
                  "print('pass')")
        result = self.run(self.policy(tests=script))
        self.assertEqual(result["verdict"], "tests-mutated-source")
        self.assertIsNone(result["shipping"])
        self.assertFalse(result["workspace_modified"])
        candidate = Path(result["scratch_workspace"])
        self.assertEqual((candidate / "src/module.py").read_text(), "VALUE=1\n")

    def test_review_mutates_own_copy_not_worker_candidate(self):
        reviewer = ("from pathlib import Path;"
                    "Path('src/module.py').write_text('TAMPERED=1');"
                    "print('APPROVED')")
        result = self.run(self.policy(tests="pass", reviewer=reviewer))
        self.assertEqual(result["verdict"], "review-mutated-source")
        self.assertIsNone(result["shipping"])
        candidate = Path(result["scratch_workspace"])
        self.assertEqual((candidate / "src/module.py").read_text(), "VALUE=1\n")

    def test_mutator_side_effects_do_not_contaminate_candidate(self):
        mutant = ("from pathlib import Path;"
                  "Path('mutation-results.txt').write_text('survivors=2');"
                  "print('mutator invocation completed')")
        result = self.run(self.policy(tests="pass", mutation=mutant))
        self.assertEqual(result["verdict"], "checks-executed-without-authenticated-verdict")
        self.assertFalse(result["workspace_modified"])
        self.assertTrue(result["executions"][-1]["workspace_modified"])
        self.assertFalse((Path(result["scratch_workspace"]) / "mutation-results.txt").exists())

    def test_executable_bit_changes_change_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "script.sh"
            script.write_text("#!/bin/sh\nexit 0\n")
            script.chmod(0o600)
            before = ops._workspace_digest(root)
            script.chmod(0o700)
            after = ops._workspace_digest(root)
            self.assertNotEqual(before, after)

    def test_empty_directory_changes_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            before = ops._workspace_digest(root)
            (root / "created").mkdir()
            self.assertNotEqual(before, ops._workspace_digest(root))


if __name__ == "__main__":
    unittest.main()
