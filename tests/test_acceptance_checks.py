import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts"


class AcceptanceChecksTest(unittest.TestCase):
    def test_nacc_like_execution_acceptance_warns_without_failures(self) -> None:
        script = SCRIPT_DIR / "run_acceptance_checks.py"
        package = ROOT / "examples" / "outputs" / "nacc_like_execution"
        result = subprocess.run(
            [sys.executable, str(script), str(package)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual("", result.stderr)
        self.assertEqual(0, result.returncode)
        report = (package / "acceptance_report.md").read_text(encoding="utf-8")
        self.assertIn("Status: PASS", report)
        self.assertIn("baseline_before_or_at_time_zero", report)
        self.assertIn("Package is acceptable for methodological review", report)

    def test_acceptance_fails_when_followup_precedes_time_zero(self) -> None:
        package = ROOT / "examples" / "outputs" / "nacc_like_execution"
        script = SCRIPT_DIR / "run_acceptance_checks.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_package = Path(tmpdir)
            for source in package.iterdir():
                if source.is_file():
                    (tmp_package / source.name).write_bytes(source.read_bytes())
            cohort_path = tmp_package / "cohort.csv"
            with cohort_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
                fields = handle.seek(0) or list(rows[0].keys())
            rows[0]["followup_visit_date"] = "2019-01-01"
            with cohort_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            result = subprocess.run(
                [sys.executable, str(script), str(tmp_package)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(1, result.returncode)
            report = (tmp_package / "acceptance_report.md").read_text(encoding="utf-8")
            self.assertIn("Status: FAIL", report)
            self.assertIn("followup_after_time_zero", report)


if __name__ == "__main__":
    unittest.main()
