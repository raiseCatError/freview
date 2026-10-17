"""Standardization contract for freview's separate opt-in operations policy.

The built-in schema must reflect the validator; tests do not install jsonschema.
"""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "freview" / "scripts"
POLICY_SCHEMA = ROOT / "schemas" / "freview-ops.schema.json"
PACKAGED_SCHEMA = ROOT / "skills" / "freview" / "assets" / "schemas" / "freview-ops.schema.json"

spec = importlib.util.spec_from_file_location("freview_ops_standardization", SCRIPTS / "ops.py")
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)


class OperationsSchemaContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(POLICY_SCHEMA.read_text(encoding="utf-8"))

    def test_packaged_schema_matches_repository_copy(self):
        self.assertEqual(POLICY_SCHEMA.read_bytes(), PACKAGED_SCHEMA.read_bytes())

    def test_schema_is_strict_and_versioned(self):
        self.assertEqual(self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(self.schema["properties"]["schema_version"]["const"], 1)
        self.assertFalse(self.schema["additionalProperties"])
        self.assertIn("schema_version", self.schema["required"])
        self.assertEqual(set(self.schema["properties"]), {
            "schema_version", "modules", "commands", "limits", "pass_env",
            "mutation_quality", "autonomy"})

    def test_modules_and_stages_match_runtime_exactly(self):
        modules = self.schema["properties"]["modules"]["properties"]
        commands = self.schema["properties"]["commands"]["properties"]
        self.assertEqual(set(modules), set(ops.MODULES))
        self.assertEqual(set(commands), set(ops.STAGES))
        self.assertTrue(all(props.get("default") is False for props in modules.values()))
        self.assertFalse(self.schema["properties"]["modules"]["additionalProperties"])
        self.assertFalse(self.schema["properties"]["commands"]["additionalProperties"])

    def test_defaults_and_runtime_validation_match(self):
        sample = json.loads((ROOT / "examples" / "freview-ops.example.json").read_text())
        clean = ops.validate_policy(sample)
        self.assertFalse(any(clean["modules"][name] for name in
                             ("implementation", "tests", "adversarial", "mutation",
                              "regression", "hooks", "shipping")))
        self.assertEqual(clean["mutation_quality"], sample["mutation_quality"])
        self.assertEqual(clean["autonomy"], sample["autonomy"])
        for field in ("mutation_quality", "autonomy"):
            names = self.schema["properties"][field]["properties"]
            self.assertEqual(set(names), set(clean[field]))
            self.assertTrue(all(names[name].get("default") == clean[field][name]
                                for name in names))

    def test_readme_no_longer_calls_merged_pr_a_draft(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("In-progress enhancement:", readme)
        self.assertIn("evidence reconciliation", readme.lower())
        self.assertIn("optional operations", readme.lower())
        self.assertIn("read-only", readme.lower())


if __name__ == "__main__":
    unittest.main()
