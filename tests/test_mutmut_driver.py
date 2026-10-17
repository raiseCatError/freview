"""Offline fake mutmut CLI: adapter must run and then export CI JSON."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
DRIVER=ROOT/"skills/freview/scripts/mutmut_driver.py"


class MutmutDriverTests(unittest.TestCase):
    def test_driver_runs_then_exports_without_shell(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            fake=base/"fake-mutmut"
            fake.write_text(
                "#!"+sys.executable+"\n"
                "import sys\nfrom pathlib import Path\n"
                "root=Path.cwd()\n"
                "if sys.argv[1]=='run': (root/'started').write_text('yes')\n"
                "if sys.argv[1]=='export-cicd-stats':\n"
                " assert (root/'started').exists()\n"
                " path=root/'mutants'/'mutmut-cicd-stats.json'\n"
                " path.parent.mkdir(exist_ok=True)\n"
                " path.write_text('{\"killed\":1,\"survived\":0,\"no_tests\":0,\"timeout\":0,\"skipped\":0,\"suspicious\":0,\"segfault\":0,\"check_was_interrupted_by_user\":0,\"total\":1}')\n")
            fake.chmod(0o700)
            p=subprocess.run([sys.executable,str(DRIVER),"--binary",str(fake),
                              "--timeout-seconds","5"],cwd=base,
                             capture_output=True,text=True,timeout=15)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertTrue((base/"started").exists())
            self.assertEqual(json.loads((base/"mutants"/"mutmut-cicd-stats.json").read_text())["killed"],1)

    def test_driver_fails_when_export_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            fake=base/"fake-mutmut"
            fake.write_text("#!"+sys.executable+"\nimport sys\nsys.exit(0)\n")
            fake.chmod(0o700)
            p=subprocess.run([sys.executable,str(DRIVER),"--binary",str(fake),
                              "--timeout-seconds","5"],cwd=base,
                             capture_output=True,text=True,timeout=15)
            self.assertNotEqual(p.returncode,0)

if __name__=="__main__":
    unittest.main()
