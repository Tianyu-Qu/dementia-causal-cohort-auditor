import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts" / "generate_nacc_execution_template.py"


class NaccGeneralizedExecutionTemplatesTest(unittest.TestCase):
    def test_generates_templates_without_cohort_outputs(self) -> None:
        for task in ["classification", "survival_progression", "biomarker_linked"]:
            with self.subTest(task=task), tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir) / task
                result = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "--task-family",
                        task,
                        "--output-dir",
                        str(output_dir),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual("", result.stderr)
                self.assertEqual(0, result.returncode)
                expected = [
                    "template_spec.yaml",
                    "template_pseudocode.py",
                    "implementation_checklist.md",
                    "validation_test_plan.md",
                    "template_manifest.json",
                    "README.md",
                ]
                for filename in expected:
                    self.assertTrue((output_dir / filename).exists(), filename)
                for forbidden in ["cohort.csv", "feature_table.csv", "cohort_index.csv", "outcome_table.csv"]:
                    self.assertFalse((output_dir / forbidden).exists(), forbidden)

                manifest = json.loads((output_dir / "template_manifest.json").read_text(encoding="utf-8"))
                self.assertEqual("0.16", manifest["schema_version"])
                self.assertEqual(task, manifest["task_family"])
                self.assertFalse(manifest["patient_level_data_read"])
                self.assertFalse(manifest["cohort_construction_performed"])
                self.assertFalse(manifest["real_data_outputs_created"])
                self.assertTrue(manifest["github_safe"])

                spec = (output_dir / "template_spec.yaml").read_text(encoding="utf-8")
                self.assertIn("status: template_not_execution_ready", spec)
                self.assertIn("required_concepts:", spec)

                test_plan = (output_dir / "validation_test_plan.md").read_text(encoding="utf-8")
                self.assertIn("attrition_monotone", test_plan)
                if task == "survival_progression":
                    self.assertIn("event_after_time_zero", test_plan)
                if task == "biomarker_linked":
                    self.assertIn("biomarker_linkage_window_respected", test_plan)
                if task == "classification":
                    self.assertIn("label_not_used_as_predictor", test_plan)


if __name__ == "__main__":
    unittest.main()
