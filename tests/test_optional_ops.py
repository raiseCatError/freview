"""TDD contract for opt-in freview operations (implementation deliberately follows)."""
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
spec = importlib.util.spec_from_file_location("freview_ops", SCRIPT)
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


class OptionalOperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="freview-ops-")
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.scratch = self.base / "scratch"
        self.repo.mkdir()
        self.scratch.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "Fixture")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        (self.repo / "README.md").write_text("fixtures\n")
        (self.repo / "spec.md").write_text("# Title\n## Acceptance\n- test")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "fixture")
        self.head = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self):
        self.temp.cleanup()

    def policy(self, **modules):
        obj = {
            "schema_version": 1,
            "modules": {**{x: False for x in ops.MODULES}, **modules},
            "commands": {},
            "limits": {"timeout_seconds": 8, "max_rounds": 3,
                       "max_output_bytes": 4096},
        }
        return ops.validate_policy(obj)

    def test_default_off_and_zero_side_effects(self):
        policy = ops.validate_policy({"schema_version": 1})
        self.assertTrue(all(v is False for v in policy["modules"].values()))
        self.assertEqual(ops.status(policy)["enabled"], [])
        with self.assertRaises(ops.OpsError):
            ops.run_stage("tests", policy, self.repo, self.scratch, allow_execute=True)
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_policy_rejects_unknown_modules_and_shell_strings(self):
        with self.assertRaises(ops.OpsError):
            ops.validate_policy({"schema_version": 1, "modules": {"magic": True}})
        with self.assertRaises(ops.OpsError):
            ops.validate_policy({"schema_version": 1, "commands": {"tests": "echo ok"}})
        with self.assertRaises(ops.OpsError):
            ops.validate_policy({"schema_version": 1, "limits": {"max_rounds": 4}})

    def test_agent_credentials_are_never_forwarded_implicitly(self):
        payload = {"schema_version": 1, "modules": {"adversarial": True},
                   "commands": {"adversarial": [sys.executable, "-c", "pass"]},
                   "pass_env": ["HOME"]}
        policy = ops.validate_policy(payload)
        with self.assertRaises(ops.OpsError):
            ops.run_stage("adversarial", policy, self.repo, self.scratch,
                          allow_execute=True, expected_sha=self.head)
        report = ops.run_stage("adversarial", policy, self.repo, self.scratch,
                               allow_execute=True, allow_credentials=True,
                               expected_sha=self.head)
        self.assertEqual(report["status"], "passed")
        with self.assertRaises(ops.OpsError):
            ops.validate_policy({"schema_version": 1, "pass_env": ["GITHUB_TOKEN"]})

    def test_policy_disallows_shell_and_package_installs_by_default(self):
        for command in (["sh", "-c", "echo hi"], ["bash", "-lc", "true"],
                        ["pip", "install", "something"], ["npm", "install"],
                        ["python3", "-m", "pip", "install", "what"]):
            with self.subTest(command=command):
                with self.assertRaises(ops.OpsError):
                    ops.validate_policy({"schema_version": 1, "commands": {"tests": command}})

    def test_explicit_execution_and_clean_committed_head_required(self):
        policy = self.policy(tests=True)
        policy["commands"]["tests"] = [sys.executable, "-c", "print('PASSED')"]
        with self.assertRaises(ops.OpsError):
            ops.run_stage("tests", policy, self.repo, self.scratch)
        result = ops.run_stage("tests", policy, self.repo, self.scratch,
                               allow_execute=True, expected_sha=self.head)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["sha"], self.head)
        self.assertEqual(result["exit_code"], 0)
        self.assertTrue(Path(result["log_path"]).is_file())
        self.assertEqual((self.repo / "README.md").read_text(), "fixtures\n")

    def test_dirty_tree_or_wrong_sha_blocks(self):
        policy = self.policy(tests=True)
        policy["commands"]["tests"] = [sys.executable, "-c", "pass"]
        with self.assertRaises(ops.OpsError):
            ops.run_stage("tests", policy, self.repo, self.scratch,
                          allow_execute=True, expected_sha="a" * 40)
        (self.repo / "README.md").write_text("changed")
        with self.assertRaises(ops.OpsError):
            ops.run_stage("tests", policy, self.repo, self.scratch,
                          allow_execute=True, expected_sha=self.head)

    def test_output_budget_stops_noisy_command(self):
        policy = self.policy(tests=True)
        policy["commands"]["tests"] = [sys.executable, "-c",
                                       "import sys;sys.stdout.write('Z'*1000000)"]
        result = ops.run_stage("tests", policy, self.repo, self.scratch,
                               allow_execute=True, expected_sha=self.head)
        self.assertEqual(result["status"], "output-limit")
        self.assertTrue(result["output_truncated"])
        self.assertLessEqual(Path(result["log_path"]).stat().st_size, 4096)

    def test_pipeline_uses_bounded_review_rounds(self):
        policy = self.policy(implementation=True, tests=True, adversarial=True)
        policy["commands"]["implementation"] = [sys.executable, "-c",
                                                  "print('WORKER_SUMMARY')"]
        policy["commands"]["tests"] = [sys.executable, "-c", "pass"]
        policy["commands"]["adversarial"] = [sys.executable, "-c",
                                              "raise SystemExit(2)"]
        result = ops.pipeline(policy, self.repo, self.scratch,
                              allow_execute=True, expected_sha=self.head,
                              requirements="Implement the spec", rounds=3)
        self.assertEqual(result["review_cycles"], 3)
        self.assertEqual(result["verdict"], "review-process-failed")
        self.assertEqual(len(result["executions"]), 9)
        self.assertFalse(result["independent_success_authenticated"])

    def test_plan_and_shipping_in_opted_pipeline_are_human_gated(self):
        policy = self.policy(specs=True, planning=True, tests=True, shipping=True)
        policy["commands"]["tests"] = [sys.executable, "-c", "pass"]
        result = ops.pipeline(policy, self.repo, self.scratch,
                              allow_execute=True, expected_sha=self.head,
                              requirements="Meet the expected contract")
        self.assertEqual(result["plan"]["head_sha"], self.head)
        self.assertEqual(result["shipping"]["status"], "handoff-only")
        self.assertFalse(result["shipping"]["merged"])

    def test_noisy_agent_cannot_leave_child_running_after_output_cap(self):
        marker = self.scratch / "unexpected-child"
        child = ("import time;time.sleep(1);"
                 "from pathlib import Path;Path(" + repr(str(marker)) + ").write_text('oops')")
        source = ("import subprocess,sys;"
                  "subprocess.Popen([sys.executable,'-c'," + repr(child) + "]);"
                  "sys.stdout.write('Z'*1000000)")
        policy = self.policy(tests=True)
        policy["commands"]["tests"] = [sys.executable, "-c", source]
        result = ops.run_stage("tests", policy, self.repo, self.scratch,
                               allow_execute=True, expected_sha=self.head)
        self.assertEqual(result["status"], "output-limit")
        import time
        time.sleep(1.25)
        self.assertFalse(marker.exists(), "Orphan child escaped process-group termination")

    def test_git_archive_stream_never_writes_beyond_byte_budget(self):
        archive = self.scratch / "bounded.tar"
        saved = ops.MAX_ARCHIVE
        ops.MAX_ARCHIVE = 1024
        try:
            with self.assertRaises(ops.OpsError):
                ops._limited_archive(self.repo, archive, self.head)
            self.assertLessEqual(archive.stat().st_size, 1024)
        finally:
            ops.MAX_ARCHIVE = saved

    def test_failing_test_and_evidence_not_green(self):
        policy = self.policy(tests=True)
        policy["commands"]["tests"] = [sys.executable, "-c", "raise SystemExit(7)"]
        result = ops.run_stage("tests", policy, self.repo, self.scratch,
                               allow_execute=True, expected_sha=self.head)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["exit_code"], 7)

    def test_optional_mutation_regression_and_review_disabled_independently(self):
        policy = self.policy(tests=True)
        policy["commands"]["tests"] = [sys.executable, "-c", "pass"]
        for stage in ("mutation", "regression", "adversarial", "implementation"):
            with self.subTest(stage=stage):
                with self.assertRaises(ops.OpsError):
                    ops.run_stage(stage, policy, self.repo, self.scratch, allow_execute=True)

    def test_approved_mutation_uses_separate_stage_not_fake_builtin_mutator(self):
        policy = self.policy(mutation=True)
        policy["commands"]["mutation"] = [sys.executable, "-c", "print('MUTATION COMPLETE')"]
        result = ops.run_stage("mutation", policy, self.repo, self.scratch,
                               allow_execute=True, expected_sha=self.head)
        self.assertEqual(result["status"], "passed")
        self.assertFalse(result["proves_test_quality"])

    def test_adversarial_review_no_worker_summary_first_and_three_round_cap(self):
        policy = self.policy(adversarial=True)
        policy["commands"]["adversarial"] = [sys.executable, "-c",
            "import sys; t=sys.stdin.read(); print('clean' if 'WORKER_SUMMARY' not in t else 'leak')"]
        result = ops.run_stage("adversarial", policy, self.repo, self.scratch,
                               allow_execute=True, expected_sha=self.head,
                               prompt="Review spec.md and the implementation")
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["stage"], "adversarial")
        self.assertLessEqual(policy["limits"]["max_rounds"], 3)

    def test_branch_protection_and_push_updates(self):
        policy = self.policy(hooks=True)
        self.assertFalse(ops.hook_allowed("pre-commit", policy, branch="main"))
        self.assertTrue(ops.hook_allowed("pre-commit", policy, branch="feature/x"))
        self.assertFalse(ops.hook_allowed("pre-push", policy,
                                          branch="feature/x",
                                          updates=["refs/heads/x refs/heads/main"]))
        self.assertTrue(ops.hook_allowed("pre-push", policy,
                                         branch="feature/x",
                                         updates=["refs/heads/x refs/heads/feature/x"]))

    def test_ship_requires_authorized_verified_gate_and_never_pushes(self):
        policy = self.policy(shipping=True)
        with self.assertRaises(ops.OpsError):
            ops.ship_plan(policy, self.repo, verified=False)
        result = ops.ship_plan(policy, self.repo, verified=True)
        self.assertEqual(result["status"], "handoff-only")
        self.assertFalse(result["pushed"])
        self.assertFalse(result["merged"])

    def test_plan_generation_does_not_modify_project(self):
        policy = self.policy(planning=True, specs=True)
        result = ops.plan(policy, "Support pass/fail evaluation", self.head)
        self.assertIn("acceptance", result)
        self.assertIn("tasks", result)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_scratch_inside_checkout_refused(self):
        policy = self.policy(tests=True)
        policy["commands"]["tests"] = [sys.executable, "-c", "pass"]
        inside = self.repo / "scratch"
        inside.mkdir()
        with self.assertRaises(ops.OpsError):
            ops.run_stage("tests", policy, self.repo, inside,
                          allow_execute=True, expected_sha=self.head)

    def test_pipeline_cannot_claim_shipping_without_any_test_execution(self):
        policy = self.policy(shipping=True)
        with self.assertRaises(ops.OpsError):
            ops.pipeline(policy, self.repo, self.scratch,
                         allow_execute=True, expected_sha=self.head,
                         requirements="Ship safely")
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_missing_enabled_stage_argv_does_not_create_workspace(self):
        policy = self.policy(tests=True)
        with self.assertRaises(ops.OpsError):
            ops.run_stage("tests", policy, self.repo, self.scratch,
                          allow_execute=True, expected_sha=self.head)
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_optional_planning_agent_command_executes_only_in_scratch(self):
        policy = self.policy(planning=True)
        policy["commands"]["planning"] = [sys.executable, "-c",
                                            "from pathlib import Path;Path('plan.md').write_text('approved draft')"]
        report = ops.run_stage("planning", policy, self.repo, self.scratch,
                               allow_execute=True, expected_sha=self.head,
                               prompt="Spec-first planning")
        self.assertEqual(report["status"], "passed")
        self.assertFalse((self.repo / "plan.md").exists())
        self.assertTrue((Path(report["log_path"]).parent / "work" / "plan.md").exists())

    def test_hooks_install_and_uninstall_never_touch_other_hooks(self):
        policy = self.policy(hooks=True)
        path = self.repo / ".freview-ops.json"
        path.write_text(json.dumps(policy))
        git(self.repo, "add", ".freview-ops.json")
        git(self.repo, "commit", "-qm", "opt in hooks")
        untouched = self.repo / ".git" / "hooks" / "post-commit"
        untouched.write_text("#!/bin/sh\\nexit 0\\n")
        installed = ops.install_hooks(policy, self.repo, allow_install=True)
        self.assertEqual(len(installed), 2)
        for hook in installed:
            self.assertIn(ops.MARKER, Path(hook).read_text())
        removed = ops.uninstall_hooks(self.repo)
        self.assertEqual(set(installed), set(removed))
        self.assertTrue(untouched.exists())
        self.assertFalse((self.repo / ".git" / "hooks" / "pre-commit").exists())

    def test_opted_in_prepush_runs_tests_only_with_explicit_scratch(self):
        git(self.repo, "checkout", "-qb", "feature/test-hooks")
        policy = self.policy(hooks=True, tests=True)
        policy["commands"]["tests"] = [sys.executable, "-c", "print('gate passed')"]
        (self.repo / ".freview-ops.json").write_text(json.dumps(policy))
        git(self.repo, "add", ".freview-ops.json")
        git(self.repo, "commit", "-qm", "enable optional push gate")
        latest = git(self.repo, "rev-parse", "HEAD")
        update = ("refs/heads/feature/test-hooks " + latest +
                  " refs/heads/feature/test-hooks " + "0" * 40 + "\\n")
        command = [sys.executable, str(SCRIPT), "hook", "pre-push", "--repo", str(self.repo)]
        env = os.environ.copy()
        env.pop("FREVIEW_OPS_SCRATCH", None)
        blocked = subprocess.run(command, input=update, text=True, env=env,
                                 capture_output=True, timeout=20)
        self.assertEqual(blocked.returncode, 2)
        env["FREVIEW_OPS_SCRATCH"] = str(self.scratch)
        granted = subprocess.run(command, input=update, text=True, env=env,
                                 capture_output=True, timeout=30)
        self.assertEqual(granted.returncode, 0, granted.stdout + granted.stderr)
        result = json.loads(granted.stdout)
        self.assertTrue(result["allowed"])
        self.assertEqual(result["test_gate"]["status"], "passed")

    def test_existing_branch_push_checks_actual_fast_forward(self):
        policy = self.policy(hooks=True)
        before = self.head
        git(self.repo, "commit", "--allow-empty", "-qm", "fast forward")
        after = git(self.repo, "rev-parse", "HEAD")
        forward = ["refs/heads/feature/x " + after + " refs/heads/feature/x " + before]
        reverse = ["refs/heads/feature/x " + before + " refs/heads/feature/x " + after]
        self.assertTrue(ops.hook_allowed("pre-push", policy, branch="feature/x",
                                        updates=forward, repo=self.repo))
        self.assertFalse(ops.hook_allowed("pre-push", policy, branch="feature/x",
                                         updates=reverse, repo=self.repo))

    def test_hook_rejects_existing_remote_updates_without_proven_ancestry(self):
        policy = self.policy(hooks=True)
        self.assertFalse(ops.hook_allowed("pre-push", policy, branch="feature/x",
            updates=["refs/heads/feature/x " + "a" * 40 + " refs/heads/feature/x " + "b" * 40]))
        self.assertTrue(ops.hook_allowed("pre-push", policy, branch="feature/x",
            updates=["refs/heads/feature/x " + "a" * 40 + " refs/heads/feature/x " + "0" * 40]))

    def test_unapproved_hook_install_refused_and_existing_hook_preserved(self):
        policy = self.policy(hooks=True)
        with self.assertRaises(ops.OpsError):
            ops.install_hooks(policy, self.repo, allow_install=False)
        directory = self.repo / ".git" / "hooks"
        original = directory / "pre-commit"
        original.write_text("#!/bin/sh\nexit 0\n")
        with self.assertRaises(ops.OpsError):
            ops.install_hooks(policy, self.repo, allow_install=True)
        self.assertEqual(original.read_text(), "#!/bin/sh\nexit 0\n")


if __name__ == "__main__":
    unittest.main()
