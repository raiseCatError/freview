"""Report schema coverage for optional requirements and evidence provenance."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "skills/freview/scripts/report_tools.py"
SHA = "a" * 40


def report():
    return {
        "schema_version": 1, "generator": "test", "report_kind": "local-snapshot",
        "timestamp_utc": "2026-10-17T00:00:00Z", "mode_requested": "standard",
        "scope": {"included": ["git"], "excluded": []},
        "repository": {"root": None, "remote": "https://github.com/owner/project",
                       "head_sha": SHA}, "findings": [], "not_observed": ["local changes"]
    }


def evidence():
    return {
        "claim_id": "REQ-1", "lifecycle_status": "integrated-candidate",
        "evidence_state": "receipt-referenced",
        "test_quality": "not-reviewed", "source_actor": "worker", "ref_sha": SHA,
        "requirement_refs": ["specs/001/spec.md#REQ-1"],
        "implementation_refs": ["src/project.py"],
        "verification_refs": ["ci/run/123"],
        "integration_refs": [], "publication_refs": [],
        "limitations": ["no independent rerun"]
    }


class EvidenceReportTests(unittest.TestCase):
    def validate(self, obj):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_text(json.dumps(obj), encoding="utf-8")
            p = subprocess.run([sys.executable, str(REPORTS), "--format", "json",
                                str(path)], capture_output=True, text=True, timeout=30)
            return p

    def test_backward_compatible_without_new_fields(self):
        self.assertEqual(self.validate(report()).returncode, 0)

    def test_valid_spec_and_claim_metadata(self):
        obj = report()
        obj["spec_sources"] = [
            {"provider": "openspec", "path": "openspec/changes/change-1/proposal.md",
             "role": "change", "observation": "path-metadata-only", "ref_sha": SHA}]
        obj["claim_evidence"] = [evidence()]
        self.assertEqual(self.validate(obj).returncode, 0)

    def test_missing_required_provenance_field_rejected(self):
        obj = report()
        claim = evidence()
        del claim["evidence_state"]
        obj["claim_evidence"] = [claim]
        self.assertEqual(self.validate(obj).returncode, 2)

    def test_reject_fake_schema_enum_and_short_sha(self):
        obj = report()
        claim = evidence()
        claim["evidence_state"] = "magically-proven"
        claim["ref_sha"] = "abc"
        obj["claim_evidence"] = [claim]
        self.assertEqual(self.validate(obj).returncode, 2)

    def test_invalid_spec_observation_rejected(self):
        obj = report()
        obj["spec_sources"] = [
            {"provider": "spec-kit", "path": "specs/one.md",
             "observation": "code-proven"}]
        self.assertEqual(self.validate(obj).returncode, 2)

    def test_report_validation_is_not_authentication(self):
        obj = report()
        claim = evidence()
        claim.update(evidence_state="independently-reproduced",
                     source_actor="independent-auditor")
        obj["claim_evidence"] = [claim]
        # A valid shape is not a verified identity or a proof of execution.
        self.assertEqual(self.validate(obj).returncode, 0)
        reference = (ROOT / "skills/freview/references/evidence-reconciliation.md").read_text()
        self.assertIn("not independently proven by JSON validation", reference)


    def test_duplicate_claims_are_rejected(self):
        obj = report()
        obj["claim_evidence"] = [evidence(), evidence()]
        self.assertEqual(self.validate(obj).returncode, 2)

    def test_unattributed_independence_is_rejected(self):
        obj = report()
        item = evidence()
        item["evidence_state"] = "independently-reproduced"
        item["source_actor"] = "worker"
        obj["claim_evidence"] = [item]
        self.assertEqual(self.validate(obj).returncode, 2)

    def test_claim_evidence_delta_reports_changes_not_resolutions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = report()
            old["claim_evidence"] = [evidence()]
            new = report()
            item = evidence()
            item["evidence_state"] = "unverified"
            item["limitations"] = ["original CI artifact inaccessible"]
            new["claim_evidence"] = [item]
            (root / "before.json").write_text(json.dumps(old))
            (root / "after.json").write_text(json.dumps(new))
            p = subprocess.run([sys.executable, str(REPORTS), "--format", "json",
                                str(root / "before.json"), str(root / "after.json")],
                               capture_output=True, text=True, timeout=30)
            self.assertEqual(p.returncode, 0, p.stderr)
            delta = json.loads(p.stdout)["claim_evidence_delta"]
            self.assertEqual(delta["changed"][0]["after"]["evidence_state"], "unverified")
            self.assertEqual(delta["unchanged_count"], 0)
            self.assertIn("not proven", delta["warning"])

    def test_missing_evidence_in_new_report_is_not_fixed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = report()
            old["claim_evidence"] = [evidence()]
            new = report()
            new["claim_evidence"] = []
            (root / "before.json").write_text(json.dumps(old))
            (root / "after.json").write_text(json.dumps(new))
            p = subprocess.run([sys.executable, str(REPORTS), "--format", "json",
                                str(root / "before.json"), str(root / "after.json")],
                               capture_output=True, text=True, timeout=30)
            self.assertEqual(p.returncode, 0, p.stderr)
            delta = json.loads(p.stdout)["claim_evidence_delta"]
            self.assertEqual(len(delta["absent_from_new_report"]), 1)
            self.assertNotIn("resolved", delta)


if __name__ == "__main__":
    unittest.main()
