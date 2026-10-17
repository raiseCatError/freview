"""TDD optional autonomy budget and mutation-quality gates with fake local tools."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"skills/freview/scripts/ops.py"
spec=importlib.util.spec_from_file_location("freview_mutation_autonomy_ops",SCRIPT)
ops=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)


def git(repo,*args):
    return subprocess.run(["git",*args],cwd=repo,capture_output=True,
                          text=True,check=True).stdout.strip()


REPORT={"schemaVersion":"2","thresholds":{"high":80,"low":60},
        "files":{"src/a.py":{"language":"python","source":"a=1",
        "mutants":[{"id":"0","mutatorName":"Arithmetic","status":"Killed",
                    "location":{"start":{"line":1,"column":0},"end":{"line":1,"column":1}}}]}}}

class AutonomyMutationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="freview-mutate-autonomy-")
        self.repo=Path(self.tmp.name)/"repo"
        self.scratch=Path(self.tmp.name)/"scratch"
        self.repo.mkdir(); self.scratch.mkdir()
        git(self.repo,"init","-qb","feature/test")
        git(self.repo,"config","user.name","Fixture")
        git(self.repo,"config","user.email","fixture@example.invalid")
        (self.repo/"src").mkdir()
        (self.repo/"src"/"a.py").write_text("a=1\n")
        git(self.repo,"add",".");git(self.repo,"commit","-qm","initial")
        self.sha=git(self.repo,"rev-parse","HEAD")

    def tearDown(self):
        self.tmp.cleanup()

    def policy(self,*,mutation=True,agent=False,report=True,quality_mode="advisory",
               min_score=60,max_stage_runs=12):
        modules={"tests":True,"mutation":mutation,"shipping":True}
        commands={"tests":[sys.executable,"-c","pass"]}
        if mutation:
            payload=repr(json.dumps(REPORT))
            write=("from pathlib import Path; "
                   "p=Path('reports/mutation/mutation.json');"
                   "p.parent.mkdir(parents=True,exist_ok=True);"
                   f"p.write_text({payload})")
            commands["mutation"]=[sys.executable,"-c",write if report else "print('done')"]
        if agent:
            modules["implementation"]=True
            modules["adversarial"]=True
            commands["implementation"]=[sys.executable,"-c","pass"]
            # A deliberately zero-exit but unusable reviewer output.
            commands["adversarial"]=[sys.executable,"-c","print('not a verdict')"]
        return ops.validate_policy({"schema_version":1,"modules":modules,
            "commands":commands,
            "mutation_quality":{"mode":quality_mode,"min_score":min_score,
                                "format":"stryker"},
            "autonomy":{"max_stage_runs":max_stage_runs,"stop_on_no_progress":True,
                        "require_mutation_for_shipping":False},
            "limits":{"timeout_seconds":12,"max_rounds":3,"max_output_bytes":8192}})

    def run_pipeline(self, policy):
        return ops.pipeline(policy,self.repo,self.scratch,allow_execute=True,
                            expected_sha=self.sha,requirements="Exercise tests accurately")

    def test_default_off_and_no_token_consumption(self):
        settings=ops.validate_policy({"schema_version":1})
        self.assertFalse(any(settings["modules"].values()))
        self.assertEqual(settings["mutation_quality"]["mode"],"advisory")
        self.assertEqual(settings["autonomy"]["max_stage_runs"],12)
        self.assertEqual(list(self.scratch.iterdir()),[])

    def test_mutation_report_required_even_when_command_succeeds(self):
        result=self.run_pipeline(self.policy(report=False))
        self.assertEqual(result["verdict"],"mutation-inconclusive")
        self.assertFalse(result["mutation_quality"]["quality_pass"])
        self.assertIsNone(result["shipping"])

    def test_standalone_mutation_needs_report_as_well(self):
        missing=self.policy(report=False)
        result=ops.run_stage("mutation",missing,self.repo,self.scratch,
            allow_execute=True,expected_sha=self.sha)
        self.assertEqual(result["status"],"mutation-inconclusive")
        self.assertFalse(result["mutation_quality"]["quality_pass"])
        present=self.policy()
        second=ops.run_stage("mutation",present,self.repo,self.scratch,
            allow_execute=True,expected_sha=self.sha)
        self.assertEqual(second["status"],"passed")
        self.assertEqual(second["mutation_quality"]["score"],100.0)

    def test_mutation_advisory_reports_score_and_allows_handoff(self):
        result=self.run_pipeline(self.policy())
        self.assertEqual(result["mutation_quality"]["status"],"complete")
        self.assertEqual(result["mutation_quality"]["score"],100.0)
        self.assertEqual(result["verdict"],"checks-executed-without-authenticated-verdict")
        self.assertIsNotNone(result["shipping"])
        self.assertFalse(result["workspace_modified"])

    def test_checkpoint_preserves_mutation_quality_evidence(self):
        result=self.run_pipeline(self.policy())
        summary=ops.inspect_checkpoint(Path(result["checkpoint_path"]))
        stage=next(item for item in summary["stage_receipts"] if item["stage"]=="mutation")
        self.assertEqual(stage["mutation_quality"]["score"],100.0)
        self.assertTrue(stage["mutation_report_fresh"])
        self.assertEqual(stage["mutation_quality"]["counts"]["valid"],1)

    def test_mutation_gate_blocks_if_below_threshold(self):
        report=json.loads(json.dumps(REPORT))
        report["files"]["src/a.py"]["mutants"][0]["status"]="Survived"
        settings=self.policy(quality_mode="gate",min_score=70)
        payload=repr(json.dumps(report))
        settings["commands"]["mutation"]=[sys.executable,"-c",
            "from pathlib import Path;"
            "p=Path('reports/mutation/mutation.json');p.parent.mkdir(parents=True,exist_ok=True);"
            f"p.write_text({payload})"]
        result=self.run_pipeline(settings)
        self.assertEqual(result["verdict"],"mutation-threshold-failed")
        self.assertEqual(result["mutation_quality"]["score"],0.0)
        self.assertIsNone(result["shipping"])

    def test_enabled_mutation_does_not_require_global_stage_budget_override(self):
        result=self.run_pipeline(self.policy(max_stage_runs=2))
        self.assertEqual(len(result["executions"]),2)
        self.assertNotEqual(result["verdict"],"budget-exhausted")

    def test_budget_exhaustion_stops_before_next_process(self):
        result=self.run_pipeline(self.policy(agent=True,max_stage_runs=2))
        self.assertEqual(result["verdict"],"budget-exhausted")
        self.assertEqual(len(result["executions"]),2)
        self.assertIsNone(result["shipping"])

    def test_committed_stale_mutation_report_does_not_count_as_new_execution(self):
        cached=self.repo/"reports"/"mutation"
        cached.mkdir(parents=True)
        (cached/"mutation.json").write_text(json.dumps(REPORT))
        git(self.repo,"add",".")
        git(self.repo,"commit","-qm","cached old mutation report")
        self.sha=git(self.repo,"rev-parse","HEAD")
        policy=self.policy()
        policy["commands"]["mutation"]=[sys.executable,"-c","pass"]
        result=self.run_pipeline(policy)
        self.assertEqual(result["verdict"],"mutation-inconclusive")
        self.assertFalse(result["mutation_quality"]["quality_pass"])
        self.assertEqual(result["mutation_quality"]["reason_code"],"report-not-updated")
        self.assertIsNone(result["shipping"])

    def test_optional_shipping_mutation_requirement_blocks_missing_module(self):
        policy=self.policy(mutation=False)
        policy["autonomy"]["require_mutation_for_shipping"]=True
        result=self.run_pipeline(policy)
        self.assertEqual(result["verdict"],"mutation-required")
        self.assertIsNone(result["shipping"])

    def test_policy_rejects_unknown_formats_and_invalid_limits(self):
        for patch in ({"mutation_quality":{"format":"unknown"}},
                      {"autonomy":{"max_stage_runs":33}},
                      {"autonomy":{"stop_on_no_progress":"yes"}},
                      {"mutation_quality":{"min_score":-1}}):
            with self.subTest(patch=patch):
                with self.assertRaises(ops.OpsError):
                    ops.validate_policy({"schema_version":1,**patch})

if __name__=="__main__":
    unittest.main()
