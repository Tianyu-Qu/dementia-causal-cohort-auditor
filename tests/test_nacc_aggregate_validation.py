import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts" / "run_nacc_aggregate_validation.py"
INPUT = ROOT / "examples" / "inputs" / "nacc_like_synthetic"


class NaccAggregateValidationTest(unittest.TestCase):
    def test_aggregate_validation_outputs_no_patient_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "aggregate"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input-dir",
                    str(INPUT),
                    "--output-dir",
                    str(output_dir),
                    "--real-data-mode",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", result.stderr)
            self.assertEqual(0, result.returncode)

            expected = [
                "aggregate_validation_report.md",
                "field_distribution_summary.csv",
                "missingness_by_form_version.csv",
                "visit_structure_report.md",
                "privacy_check_report.md",
                "aggregate_validation_manifest.json",
            ]
            for filename in expected:
                self.assertTrue((output_dir / filename).exists(), filename)

            report = (output_dir / "aggregate_validation_report.md").read_text(encoding="utf-8")
            self.assertIn("Ready for cohort construction: false", report)
            self.assertIn("Participants with >=2 visits", report)
            self.assertNotIn("N001", report)

            visit_report = (output_dir / "visit_structure_report.md").read_text(encoding="utf-8")
            self.assertIn("Patient rows", (output_dir / "privacy_check_report.md").read_text(encoding="utf-8"))
            self.assertNotIn("N001", visit_report)

            with (output_dir / "field_distribution_summary.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            apoe_rows = [row for row in rows if row["concept"] == "apoe"]
            self.assertTrue(apoe_rows)
            naccid_rows = [row for row in rows if row["field"].upper() == "NACCID"]
            self.assertTrue(naccid_rows)
            self.assertEqual("suppressed_identifier_field", naccid_rows[0]["top_values"])

            all_output = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in output_dir.glob("*"))
            self.assertNotIn("N001", all_output)
            self.assertIn("Auxiliary Participant-Level Evidence", report)
            self.assertIn("aggregate_supported_pending_design_approval", report)


if __name__ == "__main__":
    unittest.main()
