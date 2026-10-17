"""Contract tests for bounded, passive specification discovery."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "skills/freview/scripts/spec_inventory.py"
spec = importlib.util.spec_from_file_location("spec_inventory", MODULE)
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class SpecInventoryTests(unittest.TestCase):
    def test_empty_repository(self):
        with tempfile.TemporaryDirectory() as folder:
            result = inventory.discover(Path(folder))
            self.assertEqual(result["status"], "no-known-artifacts")
            self.assertEqual(result["artifacts"], [])

    def test_both_frameworks_metadata_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for rel in ("openspec/changes/example/proposal.md",
                        "openspec/specs/api/spec.md",
                        "specs/003-feature/spec.md",
                        ".specify/templates/plan.md"):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("do not execute this", encoding="utf-8")
            output = inventory.discover(root)
            self.assertEqual(len(output["artifacts"]), 4)
            self.assertEqual(output["status"], "inventory-only")
            self.assertTrue(all(x["evidence"] == "path-metadata-only"
                                for x in output["artifacts"]))
            self.assertTrue(all("do not execute" not in str(x)
                                for x in output["artifacts"]))

    def test_skips_directory_symlinks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            outside = root / "outside"
            outside.mkdir()
            (outside / "secret.md").write_text("do not expose", encoding="utf-8")
            (root / "specs").symlink_to(outside, target_is_directory=True)
            result = inventory.discover(root)
            self.assertEqual(result["artifacts"], [])
            self.assertTrue(any("symlink-skipped" in x for x in result["warnings"]))

    def test_rejects_symlinked_parent_of_source_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            outside = root / "elsewhere"
            (outside / "specs").mkdir(parents=True)
            (outside / "specs" / "secret.md").write_text("private", encoding="utf-8")
            (root / "openspec").symlink_to(outside, target_is_directory=True)
            result = inventory.discover(root)
            self.assertEqual(result["artifacts"], [])
            self.assertTrue(any("openspec/specs" in w for w in result["warnings"]))
            self.assertEqual(result["status"], "partial")

    def test_limits_and_oversized(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            directory = root / "specs"
            directory.mkdir()
            for n in range(4):
                (directory / f"{n}.md").write_text("x")
            output = inventory.discover(root, max_files=2)
            self.assertTrue(output["truncated"])
            self.assertEqual(len(output["artifacts"]), 2)
            (directory / "huge.md").write_bytes(b"x" * (inventory.MAX_BYTES + 1))
            output = inventory.discover(root)
            self.assertTrue(any("oversized" in warning for warning in output["warnings"]))

    def test_many_irrelevant_files_hit_traversal_cap(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            directory = root / "specs"
            directory.mkdir()
            for n in range(inventory.MAX_VISITED + 2):
                (directory / f"{n:05}.bin").touch()
            result = inventory.discover(root)
            self.assertTrue(result["truncated"])
            self.assertEqual(result["status"], "partial")
            self.assertIn("entry-scan-budget-exceeded", result["warnings"])
            self.assertEqual(result["artifacts"], [])

    def test_no_file_content_and_invalid_limits(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "specs").mkdir()
            (root / "specs" / "odd.py").write_text("raise Exception()")
            self.assertEqual(inventory.discover(root)["artifacts"], [])
            with self.assertRaises(ValueError):
                inventory.discover(root, max_depth=0)


if __name__ == "__main__":
    unittest.main()
