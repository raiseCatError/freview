"""Agent doctor alias/profile smoke tests; no shell execution or model calls."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/freview/scripts/agent_doctor.py"
SPEC = importlib.util.spec_from_file_location("agent_doctor", SCRIPT)
DOCTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOCTOR)


class AgentDoctorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="freview-doctor-")
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def records(self):
        return {x["command"]: x for x in DOCTOR.inspect(self.home)["commands"]}

    def test_two_claude_accounts_have_separate_skill_roots(self):
        (self.home / ".zshrc").write_text(
            "alias claude-account1='CLAUDE_CONFIG_DIR=\"$HOME/.claude-account1\" claude'\n"
            "alias claude-account2='CLAUDE_CONFIG_DIR=~/claude-private-two claude'\n")
        for profile in (".claude-account1", "claude-private-two"):
            skill = self.home / profile / "skills/freview"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: freview\n---\n")
        rows = self.records()
        self.assertEqual(rows["claude-account1"]["definition"], "alias")
        self.assertNotEqual(rows["claude-account1"]["profile_path"],
                            rows["claude-account2"]["profile_path"])
        self.assertTrue(rows["claude-account1"]["freview_visible_on_disk"])
        self.assertTrue(rows["claude-account2"]["freview_visible_on_disk"])
        self.assertFalse(rows["claude-account1"]["bundle_complete"])
        self.assertFalse(rows["claude-account1"]["activation_confirmed"])

    def test_shell_functions_disclose_custom_claude_and_opencode_profiles(self):
        (self.home / ".zshrc").write_text(
            "function claude-account1() {\n"
            "  CLAUDE_CONFIG_DIR=\"$HOME/.custom/claude1\" claude \"$@\"\n}\n"
            "opencode1() {\n"
            "  OPENCODE_CONFIG_DIR=\"$HOME/.config/open1\" opencode \"$@\"\n}\n")
        rows = self.records()
        self.assertEqual(rows["claude-account1"]["profile_path"],
                         str(self.home / ".custom/claude1"))
        self.assertEqual(rows["opencode1"]["profile_path"],
                         str(self.home / ".config/open1"))
        self.assertIn(str(self.home / ".config/open1/skills/freview"),
                      [p["path"] for p in rows["opencode1"]["skill_locations"]])

    def test_opencode_can_see_common_global_skill_but_claude_cannot(self):
        skill = self.home / ".agents/skills/freview"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("ok")
        rows = self.records()
        self.assertTrue(rows["opencode"]["freview_visible_on_disk"])
        self.assertFalse(rows["claude"]["freview_visible_on_disk"])

    def test_untrusted_shell_expression_not_evaluated_or_echoed(self):
        marker = self.home / "should-not-exist"
        (self.home / ".zshrc").write_text(
            "alias claude-account2='SECRET_TOKEN=do-not-print "
            "CLAUDE_CONFIG_DIR=$(touch " + str(marker) + ") claude'\n")
        data = DOCTOR.inspect(self.home)
        result = next(c for c in data["commands"] if c["command"] == "claude-account2")
        self.assertEqual(result["profile_resolution"], "dynamic-or-unresolved")
        self.assertFalse(marker.exists())
        self.assertNotIn("do-not-print", json.dumps(data))

    def test_rc_symlink_not_followed(self):
        external = self.home / "external"
        external.write_text("alias claude-account1='CLAUDE_CONFIG_DIR=~/one claude'\n")
        (self.home / ".zshrc").symlink_to(external)
        self.assertNotIn("claude-account1", self.records())

    def test_broken_skill_symlink_detected(self):
        target = self.home / ".codex/skills/freview"
        target.parent.mkdir(parents=True)
        target.symlink_to(self.home / "missing")
        self.assertEqual(self.records()["codex"]["skill_locations"][0]["status"], "broken-symlink")

    def test_complete_bundle_without_claiming_activation(self):
        root = self.home / ".agents/skills/freview"
        for asset in DOCTOR.BUNDLE_REQUIRED:
            location = root / asset
            location.parent.mkdir(parents=True, exist_ok=True)
            location.write_text("ok")
        report = self.records()["opencode"]
        self.assertTrue(report["bundle_complete"])
        self.assertFalse(report["activation_confirmed"])

    def test_no_shell_scan_omits_aliases(self):
        (self.home / ".zshrc").write_text(
            "alias claude-account1='CLAUDE_CONFIG_DIR=~/one claude'\n")
        rows = DOCTOR.inspect(self.home, shell_scan=False)["commands"]
        self.assertFalse(any(x["command"] == "claude-account1" for x in rows))


if __name__ == "__main__":
    unittest.main()
