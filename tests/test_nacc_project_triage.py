import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "dementia-causal-cohort-auditor" / "scripts"


class NaccProjectTriageTest(unittest.TestCase):
    def test_triage_messy_project_recommends_core_file(self) -> None:
        script = SCRIPT_DIR / "triage_nacc_project.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"
            output = Path(tmpdir) / "triage"
            project.mkdir()
            (project / "paper_notes.md").write_text("# not data\n", encoding="utf-8")
            (project / "investigator_ftldlbd_nacc70.csv").write_text(
                "NACCID,NACCADC,PACKET,FORMVER,VISITMO,VISITDAY,VISITYR,NACCVNUM,SEX,EDUC\n",
                encoding="utf-8",
            )
            (project / "investigator_scan_pet_nacc70.csv").write_text(
                "NACCID,NACCADC,SCANDATE,TRACER,META_TEMPORAL_SUVR,CSF_SUVR\n",
                encoding="utf-8",
            )
            with zipfile.ZipFile(project / "bundle.zip", "w") as archive:
                archive.writestr(
                    "investigator_ftldlbd_nacc70.csv",
                    "NACCID,NACCADC,PACKET,FORMVER,VISITMO,VISITDAY,VISITYR,NACCVNUM,SEX,EDUC\n",
                )

            result = subprocess.run(
                [sys.executable, str(script), "--input-dir", str(project), "--output-dir", str(output), "--include-zip-headers"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", result.stderr)
            self.assertEqual(0, result.returncode)
            report = (output / "nacc_project_triage_report.md").read_text(encoding="utf-8")
            self.assertIn("investigator_ftldlbd_nacc70.csv", report)
            self.assertIn("bundle.zip::investigator_ftldlbd_nacc70.csv", report)
            self.assertIn("pet_imaging", report)
            recommended = (output / "recommended_core_files.txt").read_text(encoding="utf-8")
            self.assertEqual("investigator_ftldlbd_nacc70.csv\n", recommended)

    def test_file_list_sampling_uses_selected_files_only(self) -> None:
        sampler = SCRIPT_DIR / "make_header_samples.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"
            output = Path(tmpdir) / "sample"
            project.mkdir()
            (project / "core.csv").write_text("NACCID,NACCVNUM\nN001,1\nN002,1\n", encoding="utf-8")
            (project / "ignore.csv").write_text("NACCID,SCANDATE\nN001,2020-01-01\n", encoding="utf-8")
            file_list = Path(tmpdir) / "recommended_core_files.txt"
            file_list.write_text("core.csv\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(sampler),
                    "--input-dir",
                    str(project),
                    "--output-dir",
                    str(output),
                    "--rows",
                    "1",
                    "--file-list",
                    str(file_list),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("", result.stderr)
            self.assertEqual(0, result.returncode)
            self.assertTrue((output / "core.csv").exists())
            self.assertFalse((output / "ignore.csv").exists())
            self.assertEqual(2, len((output / "core.csv").read_text(encoding="utf-8").splitlines()))


if __name__ == "__main__":
    unittest.main()
