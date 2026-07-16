import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts"


class RealNaccPreflightTest(unittest.TestCase):
    def test_header_only_then_real_data_dry_run(self) -> None:
        sampler = SCRIPT_DIR / "make_header_samples.py"
        scanner = SCRIPT_DIR / "scan_nacc_files.py"
        input_dir = ROOT / "examples" / "inputs" / "nacc_like_synthetic"
        with tempfile.TemporaryDirectory() as tmpdir:
            header_dir = Path(tmpdir) / "headers"
            dry_run_dir = Path(tmpdir) / "dry_run"
            sample = subprocess.run(
                [sys.executable, str(sampler), "--input-dir", str(input_dir), "--output-dir", str(header_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", sample.stderr)
            self.assertEqual(0, sample.returncode)
            participant_lines = (header_dir / "participants.csv").read_text(encoding="utf-8").splitlines()
            self.assertEqual(1, len(participant_lines))
            self.assertNotIn("N001", participant_lines[0])

            scan = subprocess.run(
                [
                    sys.executable,
                    str(scanner),
                    "--input-dir",
                    str(header_dir),
                    "--output-dir",
                    str(dry_run_dir),
                    "--sample-rows",
                    "0",
                    "--real-data-mode",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", scan.stderr)
            self.assertEqual(0, scan.returncode)
            readiness = (dry_run_dir / "nacc_readiness_report.md").read_text(encoding="utf-8")
            self.assertIn("Real data mode: true", readiness)
            self.assertIn("Ready for execution: no", readiness)
            worksheet = (dry_run_dir / "human_confirmation_worksheet.md").read_text(encoding="utf-8")
            self.assertIn("NACC release, UDS versions, and modules", worksheet)

    def test_five_row_sample_smoke_test_outputs_beginner_reports(self) -> None:
        sampler = SCRIPT_DIR / "make_header_samples.py"
        scanner = SCRIPT_DIR / "scan_nacc_files.py"
        input_dir = ROOT / "examples" / "inputs" / "nacc_like_synthetic"
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_dir = Path(tmpdir) / "sample5"
            dry_run_dir = Path(tmpdir) / "dry_run"
            sample = subprocess.run(
                [sys.executable, str(sampler), "--input-dir", str(input_dir), "--output-dir", str(sample_dir), "--rows", "5"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", sample.stderr)
            self.assertEqual(0, sample.returncode)

            scan = subprocess.run(
                [
                    sys.executable,
                    str(scanner),
                    "--input-dir",
                    str(sample_dir),
                    "--output-dir",
                    str(dry_run_dir),
                    "--sample-rows",
                    "5",
                    "--real-data-mode",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", scan.stderr)
            self.assertEqual(0, scan.returncode)
            beginner = (dry_run_dir / "nacc_beginner_report.md").read_text(encoding="utf-8")
            self.assertIn("five-row sample", beginner)
            self.assertIn("not causal-ready exposure", beginner)
            self.assertNotIn("N001", beginner)
            features = (dry_run_dir / "feature_readiness_report.md").read_text(encoding="utf-8")
            self.assertIn("Representation learning", features)
            self.assertIn("Treatment effect estimation", features)


if __name__ == "__main__":
    unittest.main()
