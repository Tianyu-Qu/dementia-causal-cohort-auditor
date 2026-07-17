import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts" / "build_real_nacc_prediction_pilot.py"


def write_core(path: Path) -> None:
    rows = [
        {
            "NACCID": "R001",
            "NACCVNUM": "1",
            "VISITMO": "1",
            "VISITDAY": "1",
            "VISITYR": "2020",
            "NACCAGE": "70",
            "NACCUDSD": "1",
            "NACCNE4S": "1",
            "NACCMMSE": "29",
            "SEX": "2",
            "EDUC": "16",
            "CDRGLOB": "0",
            "CDRSUM": "0",
            "FORMVER": "3",
        },
        {
            "NACCID": "R001",
            "NACCVNUM": "2",
            "VISITMO": "1",
            "VISITDAY": "1",
            "VISITYR": "2021",
            "NACCAGE": "71",
            "NACCUDSD": "1",
            "NACCNE4S": "1",
            "NACCMMSE": "27",
            "SEX": "2",
            "EDUC": "16",
            "CDRGLOB": "0",
            "CDRSUM": "0.5",
            "FORMVER": "3",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


class RealNaccGuardedPilotTest(unittest.TestCase):
    def test_requires_explicit_real_data_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            core = tmp / "investigator_ftldlbd_nacc70.csv"
            output = tmp / "blocked"
            write_core(core)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--core-file", str(core), "--output-dir", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(2, result.returncode)
            blocker = (output / "pilot_blocker_report.md").read_text(encoding="utf-8")
            self.assertIn("Missing --allow-real-data", blocker)
            self.assertFalse((output / "cohort.csv").exists())

    def test_guarded_pilot_builds_package_when_approved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            core = tmp / "investigator_ftldlbd_nacc70.csv"
            output = tmp / "pilot"
            write_core(core)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--core-file",
                    str(core),
                    "--output-dir",
                    str(output),
                    "--allow-real-data",
                    "--approved-pilot-rules",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", result.stderr)
            self.assertEqual(0, result.returncode)
            expected = [
                "cohort_index.csv",
                "feature_table.csv",
                "outcome_table.csv",
                "cohort.csv",
                "attrition_table.csv",
                "data_quality_report.md",
                "leakage_report.md",
                "reproducibility_manifest.json",
                "acceptance_report.md",
                "privacy_notice.md",
            ]
            for filename in expected:
                self.assertTrue((output / filename).exists(), filename)
            manifest = json.loads((output / "reproducibility_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("0.15.1", manifest["schema_version"])
            self.assertFalse(manifest["git_commit_allowed_for_outputs"])
            acceptance = (output / "acceptance_report.md").read_text(encoding="utf-8")
            self.assertIn("Status: PASS", acceptance)


if __name__ == "__main__":
    unittest.main()
