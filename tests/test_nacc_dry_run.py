import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts"


class NaccDryRunTest(unittest.TestCase):
    def test_scan_nacc_like_synthetic_outputs(self) -> None:
        script = SCRIPT_DIR / "scan_nacc_files.py"
        input_dir = ROOT / "examples" / "inputs" / "nacc_like_synthetic"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "dry_run"
            result = subprocess.run(
                [sys.executable, str(script), "--input-dir", str(input_dir), "--output-dir", str(output_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", result.stderr)
            self.assertEqual(0, result.returncode)
            expected = [
                "nacc_file_inventory.csv",
                "nacc_file_inventory.md",
                "nacc_concept_coverage.yaml",
                "nacc_variable_mapping_candidates.yaml",
                "nacc_readiness_report.md",
                "unresolved_human_questions.md",
            ]
            for filename in expected:
                self.assertTrue((output_dir / filename).exists(), filename)
            v08_expected = [
                "nacc_beginner_report.md",
                "feature_readiness_report.md",
                "next_action_plan.md",
                "nacc_glossary.md",
            ]
            for filename in v08_expected:
                self.assertTrue((output_dir / filename).exists(), filename)
            coverage = (output_dir / "nacc_concept_coverage.yaml").read_text(encoding="utf-8")
            self.assertIn("concept_id: participant_id", coverage)
            self.assertIn("field: NACCID", coverage)
            self.assertIn("concept_id: medication_records", coverage)
            self.assertIn("concept_id: medication_temporality_support", coverage)
            readiness = (output_dir / "nacc_readiness_report.md").read_text(encoding="utf-8")
            self.assertIn("Status: needs_human_confirmation", readiness)
            inventory = (output_dir / "nacc_file_inventory.md").read_text(encoding="utf-8")
            self.assertIn("unique_in_sample", inventory)
            self.assertNotIn("N001", inventory)
            beginner = (output_dir / "nacc_beginner_report.md").read_text(encoding="utf-8")
            self.assertIn("not causal-ready exposure", beginner)
            features = (output_dir / "feature_readiness_report.md").read_text(encoding="utf-8")
            self.assertIn("Treatment effect estimation", features)


if __name__ == "__main__":
    unittest.main()
