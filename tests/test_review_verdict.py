"""TDD: a successful reviewer process is not an approved code review.

These use fake offline reviewers. They are NOT real independent agent acceptance.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERDICTS = ROOT / "skills/freview/scripts/review_verdict.py"
OPS = ROOT / "skills/freview/scripts/ops.py"
SHA = "a" * 40
DIGEST = "b" * 64


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


review = load(VERDICTS, "freview_review_verdict")
ops = load(OPS, "freview_ops_verdict")


def report(verdict="approve", findings=None, **extra):
    doc = {"schema_version": 1, "source_sha": SHA, "workspace_digest": DIGEST,
           "verdict": verdict, "findings": findings if findings is not None else [],
           "reviewed_paths": ["src/module.py"], "reason": "reviewed actual diff"}
    doc.update(extra)
    return doc


def finding():
    return {"id": "R1", "severity": "high", "path": "src/module.py",
            "description": "Missing handling for empty values",
            "evidence": "src/module.py:18 lacks a guard"}


class VerdictContractTests(unittest.TestCase):
    def validate(self, obj):
        return review.validate(obj, expected_sha=SHA, expected_digest=DIGEST)

    def test_explicit_approved_claim_is_not_authentication(self):
        result = self.validate(report())
        self.assertEqual(result["status"], "approved-claim")
        self.assertFalse(result["reviewer_independence_verified"])
        self.assertFalse(result["source_reading_verified"])

    def test_requested_changes_include_bounded_findings(self):
        result = self.validate(report("changes_requested", [finding()]))
        self.assertEqual(result["status"], "changes-requested")
        self.assertEqual(result["findings"][0]["id"], "R1")

    def test_silent_zero_exit_claims_are_invalid(self):
        for obj in ("looks good", "", [], "{}", {"verdict": "approve"}):
            with self.subTest(obj=obj):
                self.assertEqual(self.validate(obj)["status"], "invalid")

    def test_rejects_wrong_sha_and_snapshot_digest(self):
        self.assertEqual(self.validate(report(source_sha="c" * 40))["status"], "invalid")
        self.assertEqual(self.validate(report(workspace_digest="0" * 64))["status"], "invalid")

    def test_no_green_approval_with_outstanding_findings(self):
        self.assertEqual(self.validate(report("approve", [finding()]))["status"], "invalid")
        self.assertEqual(self.validate(report("changes_requested", []))["status"], "invalid")

    def test_rejects_duplicate_findings_and_unsafe_paths(self):
        self.assertEqual(self.validate(report("changes_requested", [finding(), finding()]))["status"], "invalid")
        broken = finding()
        broken["path"] = "../../.env"
        self.assertEqual(self.validate(report("changes_requested", [broken]))["status"], "invalid")

    def test_bounded_input_and_strict_types(self):
        self.assertEqual(self.validate("x" * 20000)["status"], "invalid")
        self.assertEqual(self.validate(report(schema_version=True))["status"], "invalid")
        self.assertEqual(self.validate(report(verdict={"approve": True}))["status"], "invalid")
        self.assertEqual(self.validate(report(unknown="bonus"))["status"], "invalid")

    def test_blocked_not_reinterpreted_as_approval(self):
        self.assertEqual(self.validate(report("blocked", [], reason="Cannot inspect tests"))["status"], "blocked")

    def test_non_json_bytes_and_duplicate_keys_block(self):
        self.assertEqual(self.validate(b"\xff")["status"], "invalid")
        duplicate = json.dumps(report()).replace('"verdict": "approve"', '"verdict": "approve", "verdict": "blocked"')
        self.assertEqual(self.validate(duplicate)["status"], "invalid")


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


class PipelineContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="freview-review-contract-")
        self.repo = Path(self.temp.name) / "repo"
        self.scratch = Path(self.temp.name) / "scratch"
        self.repo.mkdir()
        self.scratch.mkdir()
        git(self.repo, "init", "-qb", "feature/approved")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        git(self.repo, "config", "user.name", "Fixture")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "module.py").write_text("VALUE=1\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "base")
        self.sha = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self):
        self.temp.cleanup()

    def policy(self, reviewer, worker=None, rounds=3):
        flags = {"tests": True, "adversarial": True}
        cmd = {"tests": [sys.executable, "-c", "pass"],
               "adversarial": [sys.executable, "-c", reviewer]}
        if worker is not None:
            flags["implementation"] = True
            cmd["implementation"] = [sys.executable, "-c", worker]
        return ops.validate_policy({"schema_version": 1, "modules": flags,
                "commands": cmd,
                "limits": {"timeout_seconds": 10, "max_output_bytes": 8192,
                           "max_rounds": rounds}})

    def run_pipeline(self, policy, rounds=3):
        return ops.pipeline(policy, self.repo, self.scratch,
                            allow_execute=True, expected_sha=self.sha,
                            requirements="Review src/module.py, account for empty values.",
                            rounds=rounds)

    def test_reviewer_plain_output_is_not_approval_and_does_not_loop(self):
        result = self.run_pipeline(self.policy("print('Looks good!')"))
        self.assertEqual(result["verdict"], "review-invalid")
        self.assertEqual(result["review_cycles"], 1)
        self.assertIsNone(result["shipping"])

    def test_reviewer_process_failure_does_not_blindly_retry(self):
        result = self.run_pipeline(self.policy("raise SystemExit(4)"))
        self.assertEqual(result["verdict"], "review-process-failed")
        self.assertEqual(result["review_cycles"], 1)

    def test_reviewer_can_claim_approval_but_not_prove_independence(self):
        reviewer = (
          "import sys,json,re;"
          "s=sys.stdin.read();"
          "a=re.search(r'SOURCE_SHA: ([a-f0-9]{40})',s).group(1);"
          "b=re.search(r'WORKSPACE_DIGEST: ([a-f0-9]{64})',s).group(1);"
          "print(json.dumps(dict(schema_version=1,source_sha=a,workspace_digest=b,"
          "verdict='approve',findings=[],reviewed_paths=['src/module.py'],reason='inspected'))) "
        )
        result = self.run_pipeline(self.policy(reviewer))
        self.assertEqual(result["verdict"], "reviewer-approved-claim")
        self.assertEqual(result["review_cycles"], 1)
        self.assertFalse(result["independent_success_authenticated"])
        self.assertEqual(result["review"]["status"], "approved-claim")

    def test_reviewed_sha_or_digest_mismatch_blocks(self):
        reviewer = "import json;print(json.dumps(" + repr(report()) + "))"
        result = self.run_pipeline(self.policy(reviewer))
        self.assertEqual(result["verdict"], "review-invalid")

    def test_reviewer_must_not_mutate_worker_snapshot(self):
        reviewer = (
          "from pathlib import Path;Path('src/module.py').write_text('BAD=1');"
          "print('not even a valid verdict')"
        )
        result = self.run_pipeline(self.policy(reviewer))
        self.assertIn(result["verdict"], ("review-mutated-source", "review-invalid"))
        self.assertEqual(result["review_cycles"], 1)

    def test_changes_requested_feedback_reaches_worker_second_round(self):
        worker = (
          "import sys;from pathlib import Path;"
          "p=sys.stdin.read();"
          "Path('src/guard.py').write_text('fixed') if 'R1: Missing guard' in p else None"
        )
        reviewer = (
          "import sys,json,re;"
          "from pathlib import Path;"
          "s=sys.stdin.read();"
          "a=re.search(r'SOURCE_SHA: ([a-f0-9]{40})',s).group(1);"
          "b=re.search(r'WORKSPACE_DIGEST: ([a-f0-9]{64})',s).group(1);"
          "fixed=Path('src/guard.py').exists();"
          "findings=[] if fixed else [dict(id='R1',severity='high',path='src/module.py',"
          "description='Missing guard',evidence='No guard exists')];"
          "print(json.dumps(dict(schema_version=1,source_sha=a,workspace_digest=b,"
          "verdict='approve' if fixed else 'changes_requested',findings=findings,"
          "reviewed_paths=['src/module.py'],reason='inspected')))"
        )
        result = self.run_pipeline(self.policy(reviewer, worker=worker))
        self.assertEqual(result["review_cycles"], 2)
        self.assertEqual(result["verdict"], "implementation-not-integrated")
        self.assertTrue(result["workspace_modified"])
        self.assertEqual(result["review"]["status"], "approved-claim")
        self.assertIsNone(result["shipping"])

    def test_requested_changes_stop_at_three_cycles(self):
        reviewer = (
          "import sys,json,re;"
          "s=sys.stdin.read();"
          "a=re.search(r'SOURCE_SHA: ([a-f0-9]{40})',s).group(1);"
          "b=re.search(r'WORKSPACE_DIGEST: ([a-f0-9]{64})',s).group(1);"
          "print(json.dumps(dict(schema_version=1,source_sha=a,workspace_digest=b,"
          "verdict='changes_requested',"
          "findings=[dict(id='R1',severity='high',path='src/module.py',"
          "description='Missing guard',evidence='No guard')],"
          "reviewed_paths=['src/module.py'],reason='not ready')))"
        )
        result = self.run_pipeline(self.policy(reviewer))
        self.assertEqual(result["review_cycles"], 3)
        self.assertEqual(result["verdict"], "changes-requested")
        self.assertIsNone(result["shipping"])


if __name__ == "__main__":
    unittest.main()
