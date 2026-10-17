"""Tests-first mutation report quality contracts; no external mutator installed."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "skills/freview/scripts/mutation_report.py"
spec = importlib.util.spec_from_file_location("freview_mutation_report", SRC)
mutation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mutation)


def stryker(statuses):
    return {"schemaVersion":"2", "thresholds":{"high":90,"low":60},
            "files":{"src/module.py":{"language":"python","source":"x=1","mutants":[
                {"id":str(i),"mutatorName":"ArithmeticOperator",
                 "location":{"start":{"line":i+1,"column":0},"end":{"line":i+1,"column":1}},
                 "status":status}
                for i,status in enumerate(statuses)]}}}


class MutationReportTests(unittest.TestCase):
    def test_stryker_score_and_survivors(self):
        result=mutation.summarize(stryker(["Killed","Timeout","Survived","NoCoverage",
                                           "CompileError","Ignored"]),format="auto")
        self.assertEqual(result["status"],"complete")
        self.assertEqual(result["counts"]["detected"],2)
        self.assertEqual(result["counts"]["valid"],4)
        self.assertEqual(result["counts"]["undetected"],2)
        self.assertEqual(result["score"],50.0)
        self.assertEqual(len(result["survivors"]),2)
        self.assertFalse(result["quality_pass"])
        self.assertEqual(result["source_format"],"stryker")
        self.assertTrue(result["survivors"][0]["file"].startswith("src/"))

    def test_stryker_pending_invalidates_status(self):
        result=mutation.summarize(stryker(["Killed","Pending"]),format="stryker")
        self.assertEqual(result["status"],"incomplete")
        self.assertFalse(result["quality_pass"])

    def test_stryker_empty_is_not_perfect(self):
        result=mutation.summarize(stryker([]))
        self.assertEqual(result["status"],"no-valid-mutants")
        self.assertIsNone(result["score"])
        self.assertFalse(result["quality_pass"])

    def test_all_detected_pass_at_threshold_and_limit_survivors(self):
        report=stryker(["Killed","Timeout","Survived"]*15)
        result=mutation.summarize(report,min_score=60,max_survivors=3)
        self.assertEqual(result["status"],"complete")
        self.assertEqual(len(result["survivors"]),3)
        self.assertTrue(result["quality_pass"])
        self.assertEqual(result["counts"]["valid"],45)

    def test_mutmut_stats_counts_are_consistent_and_incomplete(self):
        report={"killed":3,"survived":1,"no_tests":1,"timeout":1,"skipped":1,
                "suspicious":0,"segfault":0,"check_was_interrupted_by_user":0,"total":7}
        result=mutation.summarize(report,format="auto",min_score=60)
        self.assertEqual(result["status"],"complete")
        self.assertEqual(result["counts"]["valid"],6)
        self.assertAlmostEqual(result["score"],(4/6)*100, places=2)
        self.assertTrue(result["quality_pass"])
        report["check_was_interrupted_by_user"]=1
        report["total"]=8
        result=mutation.summarize(report)
        self.assertEqual(result["status"],"incomplete")
        self.assertFalse(result["quality_pass"])

    def test_mutmut_tampered_totals_do_not_pass(self):
        report={"killed":3,"survived":0,"no_tests":0,"timeout":0,"skipped":0,
                "suspicious":0,"segfault":0,"check_was_interrupted_by_user":0,"total":1}
        result=mutation.summarize(report)
        self.assertEqual(result["status"],"invalid")
        self.assertFalse(result["quality_pass"])

    def test_invalid_status_zero_total_and_bad_types(self):
        for report in (stryker(["Succeeded"]), {"killed":True,"total":1}, [],
                       {"killed":-1,"total":-1}, {"schemaVersion":"9","files":{}},
                       '{"killed":1,"killed":1}'):
            with self.subTest(report=report):
                result=mutation.summarize(report)
                self.assertEqual(result["status"],"invalid")
                self.assertFalse(result["quality_pass"])

    def test_fixed_report_discovery_is_bounded_and_nofollow(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            dst=root/"reports"/"mutation"
            dst.mkdir(parents=True)
            file=dst/"mutation.json"
            file.write_text(json.dumps(stryker(["Killed"])))
            good=mutation.inspect_workspace(root)
            self.assertEqual(good["status"],"complete")
            file.unlink()
            external=root/"out.json"
            external.write_text(json.dumps(stryker(["Killed"])))
            file.symlink_to(external)
            self.assertEqual(mutation.inspect_workspace(root)["status"],"invalid")
            file.unlink()
            file.write_bytes(b"x"*(mutation.MAX_REPORT_BYTES+1))
            self.assertEqual(mutation.inspect_workspace(root)["status"],"invalid")

if __name__=="__main__":
    unittest.main()
