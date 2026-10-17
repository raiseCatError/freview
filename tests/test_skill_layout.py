"""Static distribution checks for the freview Agent Skill package."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "freview"


class SkillLayoutTests(unittest.TestCase):
    def test_agent_skills_frontmatter(self):
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"))
        frontmatter = content.split("---\n", 2)[1]
        self.assertRegex(frontmatter, r"(?m)^name: freview$")
        descriptions = re.findall(r"(?m)^description: (.*)$", frontmatter)
        self.assertEqual(len(descriptions), 1)
        self.assertGreater(len(descriptions[0]), 0)
        self.assertLessEqual(len(descriptions[0]), 1024)
        self.assertRegex(frontmatter, r"(?m)^name: [a-z0-9-]+$")

    def test_references_and_helper_are_bundled(self):
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        references = re.findall(r"\]\((references/[^)]+\.md)\)", content)
        self.assertGreaterEqual(len(references), 5)
        for ref in references:
            with self.subTest(ref=ref):
                self.assertTrue((SKILL_DIR / ref).is_file())
        for tool in ("repo_snapshot.py", "review.py", "report_tools.py", "duplicates.py", "agent_doctor.py", "spec_inventory.py", "receipt_check.py", "ops.py", "review_verdict.py", "mutation_report.py", "mutmut_driver.py"):
            self.assertTrue((SKILL_DIR / "scripts" / tool).is_file())
        for asset in ("assets/schemas/freview-config.schema.json",
                      "assets/schemas/freview-report.schema.json",
                      "assets/schemas/freview-ops.schema.json",
                      "assets/catalog/specialists.json",
                      "assets/templates/github-actions/freview-daily.yml"):
            self.assertTrue((SKILL_DIR / asset).is_file())

    def test_bundled_assets_match_repository_documents(self):
        for package_path, source_path in (
            ("assets/schemas/freview-config.schema.json", "schemas/freview-config.schema.json"),
            ("assets/schemas/freview-report.schema.json", "schemas/freview-report.schema.json"),
            ("assets/schemas/freview-ops.schema.json", "schemas/freview-ops.schema.json"),
            ("assets/catalog/specialists.json", "catalog/specialists.json"),
            ("assets/templates/github-actions/freview-daily.yml",
             "templates/github-actions/freview-daily.yml"),
        ):
            with self.subTest(package_path=package_path):
                self.assertEqual((SKILL_DIR / package_path).read_bytes(),
                                 (ROOT / source_path).read_bytes())


    def test_specialist_catalog_has_only_vetted_tools(self):
        import json
        catalog = json.loads((SKILL_DIR / "assets/catalog/specialists.json").read_text())
        repos = [entry.get("url", "") for entry in catalog["tools"]]
        self.assertFalse(any("amragl/codebase-review" in url for url in repos))
        self.assertFalse(any("todogroup/repolinter" in url for url in repos))
        self.assertTrue(any("claude.com/plugins/code-review" in url for url in repos))
        self.assertTrue(any("openai/codex" in entry.get("repository", "") for entry in catalog["tools"]))
        for entry in catalog["tools"]:
            if entry.get("stars") is not None:
                self.assertGreaterEqual(entry["stars"], 1000)

    def test_no_project_specific_policy_embedded(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("raiseCatError/notMyShell", skill)
        self.assertNotIn("release/v0.20.0", skill)
        self.assertIn("read-only", skill.lower())
        self.assertIn("code-review", skill)


if __name__ == "__main__":
    unittest.main()
