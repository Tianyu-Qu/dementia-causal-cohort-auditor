# NACC Project Triage

Use this reference when the user points to a messy local project folder rather than a clean NACC table folder.

## Goal

Separate a mixed project directory into:

- likely core NACC clinical/UDS table(s)
- optional CSF, PET, MRI, imaging, biomarker, or QC modules
- archives that may duplicate already extracted tables
- irrelevant project artifacts such as papers, code, bibliography files, figures, logs, and unrelated registries

Do this before `make_header_samples.py` or `scan_nacc_files.py`.

## Preferred Workflow

1. Run metadata/header-only triage:

   ```powershell
   python skills/dementia-causal-cohort-auditor/scripts/triage_nacc_project.py --input-dir <MESSY_PROJECT_DIR> --output-dir <TRIAGE_DIR> --include-zip-headers
   ```

2. Review:

   - `nacc_project_triage_report.md`
   - `nacc_project_triage_inventory.csv`
   - `recommended_core_files.txt`

3. Create a safe five-row sample from only recommended core files:

   ```powershell
   python skills/dementia-causal-cohort-auditor/scripts/make_header_samples.py --input-dir <MESSY_PROJECT_DIR> --output-dir <SAFE_SAMPLE_DIR> --rows 5 --file-list <TRIAGE_DIR>/recommended_core_files.txt
   ```

4. Run the real-data smoke test:

   ```powershell
   python skills/dementia-causal-cohort-auditor/scripts/scan_nacc_files.py --input-dir <SAFE_SAMPLE_DIR> --output-dir <DRY_RUN_DIR> --sample-rows 5 --real-data-mode
   ```

5. Summarize beginner report, feature readiness, and next actions. Do not run cohort construction.

## Heuristics for Agents

- Start from a table with `NACCID`, `NACCVNUM`, visit date components, packet/form/version fields, demographics, and many UDS clinical columns.
- Do not start from MRI/PET/CSF files; those are downstream modules after the core clinical table is understood.
- Prefer extracted CSV files over ZIP members when both exist.
- If only ZIP files exist, inspect member names/headers first, then ask before extracting large archives.
- Never assume medication/treatment records are causal exposure variables.
- If the triage report finds no core clinical table, ask the user for the NACC clinical/UDS CSV or data dictionary.

## Why This Is Not Fully Scripted

The script provides safe, reproducible reconnaissance. The agent still decides which pathway matches the user's goal:

- classification/prediction/representation learning can often begin from the core UDS table
- biomarker or imaging studies need module linkage after core ID/visit mapping
- treatment-effect studies require an additional exposure-construction audit

Use scripts for fragile, repeatable checks; use agent reasoning for study-goal-specific routing and critique.
