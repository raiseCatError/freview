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
        self.assertTrue((SKILL_DIR / "scripts/repo_snapshot.py").is_file())

    def test_no_project_specific_policy_embedded(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("raiseCatError/notMyShell", skill)
        self.assertNotIn("release/v0.20.0", skill)
        self.assertIn("read-only", skill.lower())
        self.assertIn("code-review", skill)


if __name__ == "__main__":
    unittest.main()
