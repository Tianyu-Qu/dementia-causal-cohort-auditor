import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts" / "generate_nacc_causal_execution_package.py"


class NaccCausalExecutionPackageTest(unittest.TestCase):
    def test_default_causal_package_blocks_on_temporality(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "causal"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--output-dir", str(output_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", result.stderr)
            self.assertEqual(0, result.returncode)
            expected = [
                "causal_execution_spec.yaml",
                "causal_pseudocode.py",
                "target_trial_checklist.md",
                "causal_readiness_report.md",
                "causal_validation_test_plan.md",
                "causal_template_manifest.json",
            ]
            for filename in expected:
                self.assertTrue((output_dir / filename).exists(), filename)
            for forbidden in ["cohort.csv", "feature_table.csv", "analysis_dataset.csv", "effect_estimates.csv"]:
                self.assertFalse((output_dir / forbidden).exists(), forbidden)

            manifest = json.loads((output_dir / "causal_template_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("0.17", manifest["schema_version"])
            self.assertEqual("blocked", manifest["status"])
            self.assertFalse(manifest["patient_level_data_read"])
            self.assertFalse(manifest["cohort_construction_performed"])
            self.assertFalse(manifest["treatment_effect_estimated"])
            self.assertFalse(manifest["real_data_outputs_created"])

            readiness = (output_dir / "causal_readiness_report.md").read_text(encoding="utf-8")
            self.assertIn("Medication/exposure temporality is not confirmed", readiness)
            self.assertIn("Do not build a causal treatment-effect cohort", readiness)

            checklist = (output_dir / "target_trial_checklist.md").read_text(encoding="utf-8")
            self.assertIn("New-user definition", checklist)
            self.assertIn("Washout window", checklist)
            self.assertIn("Grace period", checklist)
            self.assertIn("Lag window", checklist)

    def test_confirmed_temporality_changes_template_status_but_not_execution_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "causal_confirmed"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--output-dir",
                    str(output_dir),
                    "--nacc-medication-temporality",
                    "confirmed",
                    "--estimation-family",
                    "att",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", result.stderr)
            self.assertEqual(0, result.returncode)
            manifest = json.loads((output_dir / "causal_template_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("template_ready_pending_human_approval", manifest["status"])
            self.assertEqual("att", manifest["estimation_family"])
            self.assertFalse(manifest["patient_level_data_read"])
            self.assertFalse(manifest["cohort_construction_performed"])
            self.assertFalse(manifest["treatment_effect_estimated"])


if __name__ == "__main__":
    unittest.main()
