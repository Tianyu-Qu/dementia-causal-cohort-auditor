import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts"


class NaccLikeExecutionTest(unittest.TestCase):
    def test_generate_and_build_nacc_like_cohort(self) -> None:
        generator = SCRIPT_DIR / "generate_nacc_like_synthetic_data.py"
        builder = SCRIPT_DIR / "build_nacc_like_cohort.py"
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
            self.assertEqual(["N001", "N002", "N007"], [row["NACCID"] for row in cohort])

            with (output_dir / "attrition_table.csv").open(newline="", encoding="utf-8") as handle:
                attrition = list(csv.DictReader(handle))
            self.assertEqual(
                [
                    "all_participants",
                    "has_required_uds_visit_records",
                    "has_valid_visit_order_or_date",
                    "has_treatment_exposure_module_available",
                    "has_active_comparator_exposure",
                    "has_baseline_candidate_visit",
                    "baseline_age_eligible",
                    "baseline_dementia_free",
                    "has_required_cognitive_status_fields",
                    "has_neuropsych_outcome_available",
                    "has_apoe_or_genetics_available",
                    "has_post_index_followup_visit",
                ],
                [row["stage"] for row in attrition],
            )
            self.assertEqual("3", attrition[-1]["n"])

            dq = (output_dir / "data_quality_report.md").read_text(encoding="utf-8")
            self.assertIn("UDSv4 rows with structural NACCMMSE missing code", dq)


if __name__ == "__main__":
    unittest.main()
