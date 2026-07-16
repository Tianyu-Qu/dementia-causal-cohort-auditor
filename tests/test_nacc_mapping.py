import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from validate_nacc_mapping import validate  # noqa: E402


class NaccMappingTest(unittest.TestCase):
    def test_example_mapping_has_required_concepts(self) -> None:
        mapping_path = ROOT / "examples" / "outputs" / "v0_3_nacc_variable_mapping.yaml"
        missing = validate(mapping_path.read_text(encoding="utf-8"))
        self.assertEqual([], missing)

    def test_missing_concepts_are_reported(self) -> None:
        missing = validate('schema_version: "0.3"\nadapter: nacc\n')
        self.assertIn("concept:participant_id", missing)

    def test_suggest_mapping_generates_valid_surface(self) -> None:
        dictionary_path = ROOT / "examples" / "inputs" / "nacc_dictionary_excerpt.csv"
        script_path = SCRIPT_DIR / "suggest_nacc_mapping.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mapping.yaml"
            result = subprocess.run(
                [sys.executable, str(script_path), str(dictionary_path), "--output", str(output_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual("", result.stderr)
            self.assertEqual(0, result.returncode)
            missing = validate(output_path.read_text(encoding="utf-8"))
            self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
