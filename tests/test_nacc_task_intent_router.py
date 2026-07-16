import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts"


class NaccTaskIntentRouterTest(unittest.TestCase):
    def run_router(self, intent: str) -> tuple[str, str]:
        script = SCRIPT_DIR / "route_nacc_task_intent.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "task"
            result = subprocess.run(
                [sys.executable, str(script), "--intent", intent, "--output-dir", str(output_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", result.stderr)
            self.assertEqual(0, result.returncode)
            return (
                (output_dir / "task_profile.yaml").read_text(encoding="utf-8"),
                (output_dir / "task_questions.md").read_text(encoding="utf-8"),
            )

    def test_prediction_cognitive_decline_intent(self) -> None:
        profile, questions = self.run_router(
            "我想用 NACC 构建 65 岁以上、基线无 dementia、至少两次访视、有 APOE，"
            "用来预测 cognitive decline 的 cohort。"
        )
        self.assertIn("primary_task_type: prediction_cognitive_decline", profile)
        self.assertIn('age_rule: ">= 65"', profile)
        self.assertIn('baseline_dementia_free: "requested"', profile)
        self.assertIn('minimum_followup: ">= 2 visits requested"', profile)
        self.assertIn('apoe_requirement: "required"', profile)
        self.assertIn("longitudinal_cognitive_outcome", profile)
        required_block = profile.split("required_nacc_concepts:", 1)[1].split("recommended_nacc_concepts:", 1)[0]
        recommended_block = profile.split("recommended_nacc_concepts:", 1)[1].split("readiness:", 1)[0]
        self.assertIn("- apoe", required_block)
        self.assertNotIn("- apoe", recommended_block)
        self.assertIn("[baseline_dementia_free]", questions)
        self.assertIn("MMSE decline", questions)
        self.assertIn("ready_for_cohort_construction: false", profile)

    def test_causal_treatment_effect_intent(self) -> None:
        profile, questions = self.run_router(
            "Use NACC to estimate treatment effect of a medication exposure with washout and active comparator."
        )
        self.assertIn("primary_task_type: causal_treatment_effect", profile)
        self.assertIn("medication_temporality_support", profile)
        self.assertIn("washout", questions)
        self.assertIn("[comparator]", questions)
        self.assertIn("ready_for_cohort_construction: false", profile)


if __name__ == "__main__":
    unittest.main()
