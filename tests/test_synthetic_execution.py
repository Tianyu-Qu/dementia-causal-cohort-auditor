import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts"


class SyntheticExecutionTest(unittest.TestCase):
    def test_generate_and_build_synthetic_cohort(self) -> None:
        generator = SCRIPT_DIR / "generate_synthetic_dementia_data.py"
        builder = SCRIPT_DIR / "build_synthetic_cohort.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            gen = subprocess.run(
                [sys.executable, str(generator), "--output-dir", str(input_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", gen.stderr)
            self.assertEqual(0, gen.returncode)

            built = subprocess.run(
                [sys.executable, str(builder), "--input-dir", str(input_dir), "--output-dir", str(output_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", built.stderr)
            self.assertEqual(0, built.returncode)

            expected_files = [
                "cohort.csv",
                "attrition_table.csv",
                "data_quality_report.md",
                "leakage_report.md",
                "reproducibility_manifest.json",
            ]
            for filename in expected_files:
                self.assertTrue((output_dir / filename).exists(), filename)

            with (output_dir / "cohort.csv").open(newline="", encoding="utf-8") as handle:
                cohort = list(csv.DictReader(handle))
            self.assertEqual(["S001", "S002", "S007", "S008"], [row["participant_id"] for row in cohort])

            with (output_dir / "attrition_table.csv").open(newline="", encoding="utf-8") as handle:
                attrition = list(csv.DictReader(handle))
            self.assertEqual("followup_available", attrition[-1]["stage"])
            self.assertEqual("4", attrition[-1]["n"])


if __name__ == "__main__":
    unittest.main()
