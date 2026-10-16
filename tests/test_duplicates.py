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

    def test_related_issue_implementation_pr_not_duplicate(self):
        x = [{"id": 10, "kind": "issue", "title": "Add queue history"},
             {"id": 22, "kind": "pr", "title": "Implement queue history", "body": "Closes #10"}]
        self.assertEqual(MOD.candidates(x), [])

    def test_similar_but_distinct_tasks_not_duplicate(self):
        x = [{"id": 1, "title": "Add macOS terminal fullscreen clipboard test"},
             {"id": 2, "title": "Add Linux terminal fullscreen keyboard test"}]
        self.assertEqual(MOD.candidates(x), [])

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
