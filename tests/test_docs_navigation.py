"""Documentation navigation stays valid and describes the integrated state."""
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINTS = (
    ROOT / "README.md",
    ROOT / "docs" / "README.md",
    ROOT / "docs" / "audits" / "README.md",
    ROOT / "skills" / "freview" / "references" / "configuration.md",
    ROOT / "skills" / "freview" / "references" / "optional-ops.md",
    ROOT / "skills" / "freview" / "references" / "mutation-autonomy.md",
)
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


class DocumentationNavigationTests(unittest.TestCase):
    def test_entrypoint_markdown_targets_exist(self):
        for source in ENTRYPOINTS:
            with self.subTest(source=source.relative_to(ROOT)):
                self.assertTrue(source.is_file())
                content = source.read_text(encoding="utf-8")
                for raw in LINK.findall(content):
                    destination = raw.split(" #", 1)[0].strip().strip("<>")
                    if not destination or destination.startswith(
                        ("#", "http:", "https:", "mailto:", "data:")
                    ):
                        continue
                    # A link can include a title after its relative path.
                    relative = unquote(destination.split(" \"", 1)[0].split("#")[0])
                    target = (source.parent / relative).resolve()
                    with self.subTest(path=relative):
                        self.assertTrue(target.is_relative_to(ROOT.resolve()))
                        self.assertTrue(target.exists(), f"{source}: {relative}")

    def test_documentation_index_explains_both_configs(self):
        doc = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
        self.assertIn(".freview.json", doc)
        self.assertIn(".freview-ops.json", doc)
        self.assertIn("Historical", doc)
        self.assertIn("read-only", doc.lower())

    def test_readme_has_an_actionable_quickstart(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Quick start", readme)
        self.assertIn("## Features at a glance", readme)
        self.assertIn("docs/README.md", readme)
        self.assertNotIn("Pre-release read-only preview", readme)
        self.assertIn("no version has been tagged", readme.lower())


if __name__ == "__main__":
    unittest.main()
