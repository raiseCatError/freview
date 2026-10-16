"""Metadata-only duplicate candidate checks; no false 'confirmed' or code scans."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/freview/scripts/duplicates.py"
SPEC = importlib.util.spec_from_file_location("freview_duplicates", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class DuplicateTests(unittest.TestCase):
    def test_identical_deliverables_remain_candidates(self):
        x = [{"id": 10, "kind": "issue", "title": "Fix narrow terminal keyboard input ownership"},
             {"id": 20, "kind": "issue", "title": "Fix narrow terminal keyboard input ownership"}]
        result = MOD.candidates(x)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "candidate-unverified")

    def test_explicit_duplicate_link_is_still_candidate(self):
        x = [{"id": 10, "kind": "issue", "title": "Git issue A"},
             {"id": 11, "kind": "issue", "title": "Other wording",
              "body": "Duplicate of #10"}]
        result = MOD.candidates(x)
        self.assertEqual(len(result), 1)
        self.assertIn("explicit-duplicate-reference", result[0]["signals"])

    def test_issue_explicitly_marks_pr_duplicate_despite_implementation_link(self):
        items = [
            {"id": 7, "kind": "pr", "title": "Add offline cache for reports",
             "body": "Closes #5"},
            {"id": 5, "kind": "issue", "title": "Caching of reports for offline use",
             "body": "This is a duplicate of #7"},
        ]
        for order in (items, list(reversed(items))):
            pairs = MOD.candidates(order)
            self.assertEqual(len(pairs), 1)
            self.assertEqual(pairs[0]["status"], "candidate-unverified")
            self.assertIn("explicit-duplicate-reference", pairs[0]["signals"])

    def test_explicit_pr_to_pr_duplicate_reference_is_candidate(self):
        items = [
            {"id": 7, "kind": "pr", "title": "Add offline cache for reports"},
            {"id": 8, "kind": "pr", "title": "Rebuild persistent report cache",
             "body": "Duplicate of #7"},
        ]
        result = MOD.candidates(items)
        self.assertEqual(len(result), 1)
        self.assertIn("explicit-duplicate-reference", result[0]["signals"])

    def test_related_issue_implementation_pr_not_duplicate(self):
        x = [{"id": 10, "kind": "issue", "title": "Add queue history"},
             {"id": 22, "kind": "pr", "title": "Implement queue history", "body": "Closes #10"}]
        self.assertEqual(MOD.candidates(x), [])

    def test_exact_title_but_pr_closes_issue_is_not_duplicate(self):
        title = "Restore queue output history from persistent session"
        items = [
            {"id": 73, "kind": "issue", "title": title},
            {"id": 95, "kind": "pr", "title": title, "body": "Closes #73"},
        ]
        self.assertEqual(MOD.candidates(items), [])

    def test_nonclosing_refs_issue_link_excludes_pr_issue_duplicate(self):
        title = "Command queue dispatch and manual approval entry"
        records = [{"id": 12, "kind": "issue", "title": title},
                   {"id": 23, "kind": "pr", "title": title, "body": "Refs #12"}]
        self.assertEqual(MOD.candidates(records), [])
        records[1]["body"] = "References: #12"
        self.assertEqual(MOD.candidates(records), [])

    def test_explicit_duplicate_statement_overrides_general_refs_link(self):
        title = "Queue approvals and command staging interaction"
        rows = [{"id": 12, "kind": "issue", "title": title},
                {"id": 23, "kind": "pr", "title": title,
                 "body": "Refs #12\\nDuplicate of #12"}]
        pairs = MOD.candidates(rows)
        self.assertEqual(len(pairs), 1)
        self.assertIn("explicit-duplicate-reference", pairs[0]["signals"])

    def test_nonclosing_refs_does_not_exclude_two_distinct_prs(self):
        title = "Command queue dispatch and manual approval entry"
        records = [{"id": 23, "kind": "pr", "title": title, "body": "Refs #12"},
                   {"id": 24, "kind": "pr", "title": title, "body": "Refs #12"}]
        self.assertEqual(len(MOD.candidates(records)), 1)

    def test_stdin_accepts_bounded_json(self):
        x = [{"id": 1, "title": "Restore queue output history from persistent session"},
             {"id": 2, "title": "Restore queue output history from persistent session"}]
        p = subprocess.run([sys.executable, str(SCRIPT), "-", "--format", "json"],
                           input=json.dumps(x), text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(len(json.loads(p.stdout)["pairs"]), 1)

    def test_stdin_rejects_oversized_input_without_writing_files(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "-", "--format", "json"],
                           input=" " * (MOD.MAX_JSON_BYTES + 1),
                           text=True, capture_output=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("Input exceeds", p.stderr)

    def test_comparison_cap_discloses_incomplete_coverage(self):
        x = [{"id": i, "title": "Unrelated title " + str(i)} for i in range(100)]
        stats = {}
        pairs = MOD.candidates(x, max_comparisons=3, stats=stats)
        self.assertEqual(pairs, [])
        self.assertEqual(stats["comparisons"], 3)
        self.assertTrue(stats["comparison_cap_reached"])

    def test_terminal_controls_are_escaped_in_markdown(self):
        x = [{"id": "1\x1b[2J", "title": "Restore queue output history from persistent session"},
             {"id": "2", "title": "Restore queue output history from persistent session"}]
        with tempfile.TemporaryDirectory(prefix="freview-controls-") as temp:
            path = Path(temp) / "inputs.json"
            path.write_text(json.dumps(x))
            p = subprocess.run([sys.executable, str(SCRIPT), str(path)],
                               text=True, capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertNotIn("\x1b", p.stdout)
            self.assertIn("u001b", p.stdout)

    def test_similar_but_distinct_tasks_not_duplicate(self):
        x = [{"id": 1, "title": "Add macOS terminal fullscreen clipboard test"},
             {"id": 2, "title": "Add Linux terminal fullscreen keyboard test"}]
        self.assertEqual(MOD.candidates(x), [])

    def test_candidate_output_cap_preserves_unverified_status(self):
        records = [
            {"id": i, "title": "Restore queue output history from persistent session"}
            for i in range(45)
        ]
        selected = MOD.candidates(records, max_pairs=12)
        self.assertEqual(len(selected), 12)
        self.assertTrue(all(item["status"] == "candidate-unverified"
                            for item in selected))

    def test_duplicate_cli_discloses_truncated_coverage(self):
        with tempfile.TemporaryDirectory(prefix="freview-capped-") as temp:
            data = Path(temp) / "items.json"
            data.write_text(json.dumps([
                {"id": i, "title": "Restore queue output history from persistent session"}
                for i in range(12)
            ]))
            p = subprocess.run([sys.executable, str(SCRIPT), str(data),
                                "--format", "json", "--max-pairs", "3"],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            report = json.loads(p.stdout)
            self.assertTrue(report["candidate_cap_reached"])
            self.assertEqual(len(report["pairs"]), 3)

    def test_json_cli_no_mutation(self):
        with tempfile.TemporaryDirectory(prefix="freview-dupe-") as temp:
            path = Path(temp) / "issues.json"
            original = '[{"id":1,"title":"A very specific keyboard input bug"},{"id":2,"title":"A very specific keyboard input bug"}]'
            path.write_text(original)
            p = subprocess.run([sys.executable, str(SCRIPT), str(path), "--format", "json"],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(p.stdout)["pairs"][0]["status"], "candidate-unverified")
            self.assertEqual(path.read_text(), original)


if __name__ == "__main__":
    unittest.main()
