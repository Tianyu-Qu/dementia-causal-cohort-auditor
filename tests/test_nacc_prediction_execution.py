import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts" / "build_nacc_prediction_cohort.py"
INPUT = ROOT / "examples" / "inputs" / "nacc_like_synthetic"


class NaccPredictionExecutionTest(unittest.TestCase):
    def test_prediction_cohort_package_and_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "prediction"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input-dir",
                    str(INPUT),
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
                "cohort_index.csv",
                "feature_table.csv",
                "outcome_table.csv",
                "cohort.csv",
                "attrition_table.csv",
                "data_quality_report.md",
                "leakage_report.md",
                "reproducibility_manifest.json",
                "acceptance_report.md",
            ]
            for filename in expected:
                self.assertTrue((output_dir / filename).exists(), filename)

            manifest = json.loads((output_dir / "reproducibility_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("0.15", manifest["schema_version"])
            self.assertEqual("prediction_cognitive_decline", manifest["cohort_task"])

            with (output_dir / "attrition_table.csv").open(newline="", encoding="utf-8") as handle:
                attrition = list(csv.DictReader(handle))
            counts = [int(row["n"]) for row in attrition]
            self.assertTrue(all(left >= right for left, right in zip(counts, counts[1:])))

            with (output_dir / "cohort.csv").open(newline="", encoding="utf-8") as handle:
                cohort = list(csv.DictReader(handle))
            self.assertEqual(counts[-1], len(cohort))
            self.assertGreater(len(cohort), 0)
            self.assertIn("cognitive_decline_label", cohort[0])
            self.assertTrue(all(row["outcome_visit_date"] > row["index_visit_date"] for row in cohort))

            acceptance = (output_dir / "acceptance_report.md").read_text(encoding="utf-8")
            self.assertIn("Status: PASS", acceptance)
            self.assertIn("cognitive_decline_label_rule", acceptance)


if __name__ == "__main__":
    unittest.main()
