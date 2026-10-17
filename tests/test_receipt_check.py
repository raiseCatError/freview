"""Tests for the non-executing verification receipt consistency checker."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "skills/freview/scripts/receipt_check.py"
spec = importlib.util.spec_from_file_location("receipt_check", MODULE)
receipts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receipts)
SHA_A = "a" * 40
SHA_B = "b" * 40


def sample(actor="worker", code=0):
    return {"schema_version": 1, "repository": "owner/project",
            "head_sha": SHA_A, "checks": [{
                "id": "unit", "actor": actor, "sha": SHA_A,
                "command": "python3 -m unittest discover",
                "exit_code": code, "evidence": ["ci/run/123"]
            }]}


class ReceiptTests(unittest.TestCase):
    def test_consistent_receipt_never_claims_verification(self):
        result = receipts.validate(sample(), expected_sha=SHA_A)
        self.assertEqual(result["status"], "claimed-evidence")
        self.assertFalse(result["provenance_verified"])
        self.assertEqual(result["errors"], [])

    def test_independent_actor_untrusted(self):
        result = receipts.validate(sample(actor="independent"))
        self.assertIn("check-0:independence-claimed-not-proven", result["warnings"])

    def test_red_exit_warns_even_if_receipt_well_formed(self):
        result = receipts.validate(sample(code=1))
        self.assertIn("check-0:nonzero-exit", result["warnings"])
        self.assertFalse(result["provenance_verified"])
        self.assertEqual(result["status"], "failed")

    def test_sha_mismatch(self):
        receipt = sample()
        receipt["checks"][0]["sha"] = SHA_B
        self.assertEqual(receipts.validate(receipt)["status"], "contradictory")
        self.assertIn("check-0:mismatched-check-sha",
                      receipts.validate(receipt)["errors"])
        self.assertIn("unexpected-head-sha",
                      receipts.validate(sample(), expected_sha=SHA_B)["errors"])
        self.assertEqual(receipts.validate(sample(), expected_sha=SHA_B)["status"], "contradictory")

    def test_empty_evidence_is_flagged(self):
        receipt = sample()
        receipt["checks"][0]["evidence"] = []
        result = receipts.validate(receipt)
        self.assertIn("check-0:no-artifact-or-run-reference", result["warnings"])
        self.assertEqual(result["status"], "incomplete")

    def test_reject_invalid_claims_and_overflow(self):
        self.assertEqual(receipts.validate([])["status"], "invalid")
        receipt = sample()
        receipt["checks"][0]["exit_code"] = True
        receipt["checks"][0]["command"] = ""
        self.assertIn("check-0:invalid-exit-code", receipts.validate(receipt)["errors"])
        self.assertIn("check-0:missing-or-invalid-command",
                      receipts.validate(receipt)["errors"])
        receipt = sample()
        receipt["checks"] = receipt["checks"] * 65
        self.assertIn("invalid-check-count", receipts.validate(receipt)["errors"])

    def test_duplicate_ids(self):
        receipt = sample()
        receipt["checks"].append(dict(receipt["checks"][0]))
        self.assertIn("check-1:duplicate-id", receipts.validate(receipt)["errors"])


if __name__ == "__main__":
    unittest.main()
