import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from validate_audit_output import validate  # noqa: E402


class ValidateAuditOutputTest(unittest.TestCase):
    def test_example_audit_has_required_sections(self) -> None:
        audit_path = ROOT / "examples" / "outputs" / "v0_1_example_audit.md"
        missing = validate(audit_path.read_text(encoding="utf-8"))
        self.assertEqual([], missing)

    def test_missing_sections_are_reported(self) -> None:
        missing = validate("## Mode\n\nDesign Critic\n")
        self.assertIn("Study Design Restatement", missing)


if __name__ == "__main__":
    unittest.main()
