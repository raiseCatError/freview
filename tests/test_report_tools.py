"""Portable report comparison regression tests."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/freview/scripts/report_tools.py"


def sample(findings=(), mode="standard", kind="local-snapshot", included=("git",)):
    return {
        "schema_version": 1, "generator": "test",
        "report_kind": kind, "timestamp_utc": "2026-01-01T00:00:00+00:00",
        "mode_requested": mode,
        "scope": {"included": list(included), "excluded": []},
        "repository": {"root": "/tmp/same-repo", "remote": None},
        "findings": list(findings), "not_observed": ["CI not checked"]
    }


def finding(name):
    return {"id": name, "severity": "P1", "category": "git",
            "summary": name + " has unresolved issues", "status": "observed", "evidence": ["fixture"]}


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="freview-reports-")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, document):
        p = self.root / name
        p.write_text(json.dumps(document))
        return str(p)

    def invoke(self, *files, ok=True):
        p = subprocess.run([sys.executable, str(SCRIPT), "--format", "json", *files],
                           text=True, capture_output=True, timeout=20)
        if ok:
            self.assertEqual(p.returncode, 0, p.stderr)
        return p

    def test_valid_report(self):
        result = json.loads(self.invoke(self.write("a.json", sample())).stdout)
        self.assertTrue(result["valid"])

    def test_new_and_absent_needs_reverification(self):
        before = self.write("old.json", sample([finding("a"), finding("b")]))
        after = self.write("new.json", sample([finding("b"), finding("c")]))
        out = json.loads(self.invoke(before, after).stdout)
        self.assertEqual([x["id"] for x in out["new"]], ["c"])
        self.assertEqual([x["id"] for x in out["absent_from_new_report"]], ["a"])
        self.assertEqual(out["unchanged_count"], 1)

    def test_utc_field_rejects_non_utc_offset(self):
        data = sample()
        data["timestamp_utc"] = "2026-10-17T03:00:00+05:30"
        self.assertEqual(self.invoke(self.write("nonutc.json", data), ok=False).returncode, 2)

    def test_empty_audit_categories_cannot_claim_full(self):
        data = sample(kind="full-audit", mode="full", included=())
        data["duplicate_clusters"] = []
        data["remediation_plan"] = []
        data["verification_manifest"] = []
        self.assertEqual(self.invoke(self.write("empty.json", data), ok=False).returncode, 2)

    def test_report_symlink_is_refused(self):
        original = Path(self.write("actual.json", sample()))
        link = self.root / "linked.json"
        link.symlink_to(original)
        result = self.invoke(str(link), ok=False)
        self.assertEqual(result.returncode, 2)

    def test_oversized_input_refused_before_json_parse(self):
        path = self.root / "huge.json"
        with path.open("wb") as stream:
            stream.truncate(16 * 1024 * 1024 + 1)
        result = self.invoke(str(path), ok=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("exceeds 16 MiB", result.stderr)

    def test_report_markdown_renders_untrusted_controls_literally(self):
        left = sample([finding("one")])
        right = sample([finding("one")])
        right["findings"][0]["summary"] = "Bad\\x1b[2J injection"
        p = subprocess.run([sys.executable, str(SCRIPT),
                            self.write("m-left.json", left),
                            self.write("m-right.json", right)],
                           text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("\\x1b", p.stdout)
        self.assertIn("u001b", p.stdout)

    def test_incompatible_coverage_refuses(self):
        before = self.write("old.json", sample())
        after = self.write("new.json", sample(included=("git", "ci")))
        self.assertEqual(self.invoke(before, after, ok=False).returncode, 2)

    def test_full_audit_requires_plan_and_duplicate_inventory(self):
        bad = sample(kind="full-audit", mode="full")
        self.assertEqual(self.invoke(self.write("bad.json", bad), ok=False).returncode, 2)
        bad["remediation_plan"] = []
        bad["duplicate_clusters"] = []
        bad["verification_manifest"] = [{
            "category": "git", "status": "verified",
            "evidence": ["git metadata at fixture SHA"]
        }]
        self.assertEqual(self.invoke(self.write("good.json", bad)).returncode, 0)

    def test_agent_action_needs_approval(self):
        bad = sample(kind="partial-audit")
        bad["duplicate_clusters"] = []
        bad["remediation_plan"] = [{"requires_approval": False, "verification": []}]
        self.assertEqual(self.invoke(self.write("bad.json", bad), ok=False).returncode, 2)

    def test_report_schema_rejects_unknown_fields_and_bad_nested_types(self):
        invalid = sample()
        invalid["unexpected"] = "must reject"
        self.assertEqual(self.invoke(self.write("extra.json", invalid), ok=False).returncode, 2)
        invalid = sample()
        invalid["scope"]["included"] = ["git", 10]
        self.assertEqual(self.invoke(self.write("bad-scope.json", invalid), ok=False).returncode, 2)
        invalid = sample()
        invalid["timestamp_utc"] = "yesterday"
        self.assertEqual(self.invoke(self.write("bad-time.json", invalid), ok=False).returncode, 2)
        invalid = sample([finding("a")])
        invalid["findings"][0]["remediation"] = {
            "summary": "propose fix", "steps": ["review"], "verification": [],
            "confidence": "high", "requires_approval": False
        }
        self.assertEqual(self.invoke(self.write("bad-remediation.json", invalid), ok=False).returncode, 2)

    def test_same_repository_multiple_worktree_paths_can_compare(self):
        old = sample([finding("a")])
        new = sample([finding("b")])
        old["repository"]["identity"] = "forge:github.com/owner/project"
        new["repository"]["identity"] = "forge:github.com/owner/project"
        new["repository"]["root"] = "/tmp/different-worktree"
        result = json.loads(self.invoke(
            self.write("old.json", old), self.write("new.json", new)).stdout)
        self.assertEqual(result["new"][0]["id"], "b")
        self.assertEqual(result["absent_from_new_report"][0]["id"], "a")

    def test_missing_repository_identity_never_compares_as_equal(self):
        left = sample()
        right = sample()
        for report in (left, right):
            report["repository"] = {"root": None, "remote": None}
        self.assertEqual(self.invoke(
            self.write("left.json", left), self.write("right.json", right),
            ok=False).returncode, 2)

    def test_report_scope_baseline_changes_are_not_comparable(self):
        old = sample()
        new = sample()
        old["repository"]["base_ref"] = "main"
        new["repository"]["base_ref"] = "dev"
        self.assertEqual(self.invoke(
            self.write("old.json", old), self.write("new.json", new),
            ok=False).returncode, 2)

    def test_full_audit_cannot_claim_unchecked_category(self):
        bad = sample(kind="full-audit", mode="full", included=("git", "code-review"))
        bad["duplicate_clusters"] = []
        bad["remediation_plan"] = []
        bad["verification_manifest"] = [
            {"category": "git", "status": "verified", "evidence": ["SHA"]},
            {"category": "code-review", "status": "not-observed", "evidence": []}
        ]
        self.assertEqual(self.invoke(self.write("bad.json", bad), ok=False).returncode, 2)
        bad["verification_manifest"][1] = {
            "category": "code-review", "status": "verified",
            "evidence": ["official read-only reviewer receipt"]
        }
        self.assertEqual(self.invoke(self.write("good.json", bad)).returncode, 0)

    def test_partial_audit_needs_manifest_for_all_selected_categories(self):
        partial = sample(kind="partial-audit", included=("git", "ci"))
        partial["duplicate_clusters"] = []
        partial["remediation_plan"] = []
        partial["verification_manifest"] = [
            {"category": "git", "status": "verified", "evidence": ["SHA"]}
        ]
        self.assertEqual(self.invoke(self.write("bad.json", partial), ok=False).returncode, 2)
        partial["verification_manifest"].append(
            {"category": "ci", "status": "not-observed", "evidence": []})
        self.assertEqual(self.invoke(self.write("good.json", partial)).returncode, 0)

    def test_missing_evidence_refuses(self):
        bad = sample([finding("x")])
        del bad["findings"][0]["evidence"]
        self.assertEqual(self.invoke(self.write("bad.json", bad), ok=False).returncode, 2)

    def test_duplicate_ids_refuse(self):
        bad = sample([finding("x"), finding("x")])
        self.assertEqual(self.invoke(self.write("bad.json", bad), ok=False).returncode, 2)


if __name__ == "__main__":
    unittest.main()
