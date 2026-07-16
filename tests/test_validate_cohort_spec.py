import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from validate_cohort_spec import validate  # noqa: E402


class ValidateCohortSpecTest(unittest.TestCase):
    def test_example_spec_has_required_fields(self) -> None:
        spec_path = ROOT / "examples" / "outputs" / "v0_2_cohort_definition.yaml"
        missing = validate(spec_path.read_text(encoding="utf-8"))
        self.assertEqual([], missing)

    def test_missing_fields_are_reported(self) -> None:
        missing = validate("schema_version: '0.2'\nmetadata:\n  status: draft\n")
        self.assertIn("study_question", missing)
        self.assertIn("metadata.created_by", missing)


if __name__ == "__main__":
    unittest.main()
