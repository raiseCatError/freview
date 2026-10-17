"""Run the labeled, deliberately misleading repository-evidence scenarios.

This fixture suite exercises deterministic *metadata* checks. It is not an
end-to-end benchmark of an autonomous agent or an independent test runner.
"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "tests/fixtures/evidence_scenarios.json"


def load(name):
    path = ROOT / f"skills/freview/scripts/{name}.py"
    spec = importlib.util.spec_from_file_location("scenario_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


receipts = load("receipt_check")
inventory = load("spec_inventory")


class AdversarialScenarios(unittest.TestCase):
    def test_labeled_fixtures(self):
        cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
        self.assertGreaterEqual(len(cases), 10)
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertTrue(case["limit"], "Every fixture must disclose its limits")
                if case["kind"] == "receipt":
                    result = receipts.validate(
                        case["receipt"], expected_sha=case.get("expected_sha"))
                    self.assertEqual(result["status"], case["expected_status"])
                    self.assertFalse(result["provenance_verified"])
                    if "expected_warning" in case:
                        self.assertIn(case["expected_warning"], result["warnings"])
                elif case["kind"] == "inventory":
                    with tempfile.TemporaryDirectory() as temp:
                        root = Path(temp)
                        for relative in case["paths"]:
                            path = root / relative
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.write_text("# fixture\n", encoding="utf-8")
                        result = inventory.discover(root)
                        self.assertEqual(result["status"], case["expected_status"])
                        providers = {a["provider"] for a in result["artifacts"]}
                        if case["expected_provider"]:
                            self.assertIn(case["expected_provider"], providers)
                        else:
                            self.assertEqual(providers, set())
                else:
                    self.fail("Unknown scenario kind")

    def test_known_undetectable_traps_stay_documented(self):
        cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
        known = {c["id"]: c for c in cases if "KNOWN " in c["limit"]}
        self.assertIn("tests-rewritten-to-pass", known)
        self.assertIn("ambiguous-specs-directory", known)
        self.assertEqual(known["tests-rewritten-to-pass"]["expected_status"],
                         "claimed-evidence")


if __name__ == "__main__":
    unittest.main()
