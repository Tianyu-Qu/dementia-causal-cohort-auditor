import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from validate_cohort_spec import validate  # noqa: E402


class NaccDesignPacketTest(unittest.TestCase):
    def test_generate_design_packet_from_task_intent(self) -> None:
        router = SCRIPT_DIR / "route_nacc_task_intent.py"
        packet = SCRIPT_DIR / "generate_nacc_design_packet.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir) / "task"
            packet_dir = Path(tmpdir) / "packet"
            route = subprocess.run(
                [
                    sys.executable,
                    str(router),
                    "--intent",
                    "I want to build a NACC cohort of people 65+, dementia-free at baseline, at least two visits, with APOE, to predict cognitive decline.",
                    "--output-dir",
                    str(task_dir),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", route.stderr)
            self.assertEqual(0, route.returncode)

            result = subprocess.run(
                [
                    sys.executable,
                    str(packet),
                    "--task-profile",
                    str(task_dir / "task_profile.yaml"),
                    "--task-questions",
                    str(task_dir / "task_questions.md"),
                    "--output-dir",
                    str(packet_dir),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", result.stderr)
            self.assertEqual(0, result.returncode)
            expected = [
                "cohort_definition_draft.yaml",
                "mapping_draft.yaml",
                "assumptions.md",
                "human_approval_checklist.md",
            ]
            for filename in expected:
                self.assertTrue((packet_dir / filename).exists(), filename)

            cohort = (packet_dir / "cohort_definition_draft.yaml").read_text(encoding="utf-8")
            self.assertEqual([], validate(cohort))
            self.assertIn('schema_version: "0.12-draft"', cohort)
            self.assertIn("status: needs_human_confirmation", cohort)
            self.assertIn("ready_for_execution: false", cohort)
            self.assertIn("ready_for_design_approval: false", cohort)
            self.assertIn("inc_apoe_available", cohort)
            self.assertIn("inc_follow_up_availability", cohort)

            mapping = (packet_dir / "mapping_draft.yaml").read_text(encoding="utf-8")
            self.assertIn("concept_id: apoe", mapping)
            self.assertIn("selected_field: unresolved", mapping)
            self.assertIn("ready_for_cohort_construction: false", mapping)

            checklist = (packet_dir / "human_approval_checklist.md").read_text(encoding="utf-8")
            self.assertIn("Approve every item before cohort construction", checklist)
            self.assertIn("Core NACC clinical/UDS table selected", checklist)
            self.assertIn("I approve this design packet", checklist)


if __name__ == "__main__":
    unittest.main()
