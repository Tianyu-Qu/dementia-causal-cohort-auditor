# Dementia Causal-Cohort Auditor

A Codex skill and reference implementation for auditing dementia cohort designs before generating cohort construction code.

The project is intentionally not a generic medical data cleaning agent. It is a methodological critic for dementia, MCI, cognitive decline, Alzheimer's disease, and related real-world evidence studies. Its first job is to surface design flaws, temporal-ordering problems, leakage risks, and causal inference threats.

## Core Architecture

1. Trigger Layer: decide when this skill should activate.
2. Decision Layer: decide whether to critique, ask questions, build spec, map dataset variables, generate code, or validate existing results.
3. Core Knowledge Layer: disease SOP plus causal inference audit rules.
4. Adapter Layer: NACC, ADNI, UKB, EHR, and synthetic dataset mappings.
5. Workflow Layer: step-by-step interaction protocol from research question to audit memo.
6. Execution Layer: SQL/Python/cohort table/data quality report/tests.
7. Acceptance Layer: check whether the output is methodologically and computationally valid.

## Current Scope

v0.1 implements the Design Critic MVP:

- trigger metadata for dementia cohort, NACC, treatment effect, and leakage tasks
- decision modes for critique, spec building, adapter mapping, execution building, and validation review
- dementia SOP and causal audit rules
- NACC and synthetic adapter drafts
- v0.1 design audit output template
- a small validator for required audit sections

v0.1 does not generate final SQL/Python cohort construction code. That belongs to later versions after the design audit layer is reliable.

v0.2 adds the Structured Cohort Spec layer:

- `cohort_definition.yaml` schema guidance
- a v0.2 cohort spec example
- a validator for required cohort spec fields
- acceptance criteria for deciding whether a spec is execution-ready

v0.2 still does not generate final SQL/Python cohort construction code. It creates the reviewable contract that later code generation must follow.

v0.3 adds the first practical NACC adapter layer:

- a data-dictionary-driven NACC mapping protocol
- required dementia causal cohort concepts for NACC
- `nacc_variable_mapping.yaml` schema guidance
- a candidate mapping generator from CSV dictionaries or header files
- a validator for required NACC mapping concepts
- a NACC-like dictionary excerpt and example mapping

v0.3 still treats all NACC mappings as candidates until confirmed against the user's local NACC release, modules, and data dictionary.

v0.4 adds the first executable synthetic cohort path:

- generate a synthetic dementia treatment dataset
- build an executable cohort from CSV inputs
- output `cohort.csv`, `attrition_table.csv`, `data_quality_report.md`, `leakage_report.md`, and `reproducibility_manifest.json`
- keep real NACC execution gated behind confirmed mapping and cohort spec readiness

v0.4.1 adds a NACC-like synthetic execution path:

- generates NACC-style `NACCID`, `NACCADC`, `NACCVNUM`, `VISITMO`, `VISITDAY`, `VISITYR`, `NACCAGE`, `NACCUDSD`, `CDRGLOB`, `CDRSUM`, `NACCMMSE`, `UDSVER`, medication, death, dropout, and missing-code fields
- produces a NACC-shaped attrition table
- simulates UDS version differences and structural missingness

v0.5 adds the acceptance layer:

- validates execution packages for required files, attrition consistency, temporal ordering, duplicate IDs, baseline eligibility, APOE availability, and follow-up outcome availability
- writes `acceptance_report.md`
- treats failing acceptance checks as blockers for downstream effect estimation

v0.6 adds read-only NACC dry-run ingestion:

- scans CSV/TSV folders or header-only samples
- outputs file inventory, concept coverage, mapping candidates, readiness, and unresolved questions
- avoids row-level patient outputs
- keeps real NACC execution blocked until human confirmation

v0.7 adds pre-real-NACC safety preparation:

- creates header-only or explicitly requested small sample copies
- adds real-data mode to dry-run scans
- adds phased readiness and a human confirmation worksheet
- keeps execution readiness locked to `no` for dry-run real data

v0.8 adds a beginner-friendly real-NACC smoke-test layer:

- supports explicitly requested five-row sample scans for local NACC structure validation
- writes `nacc_beginner_report.md`, `feature_readiness_report.md`, `next_action_plan.md`, and `nacc_glossary.md`
- translates detected fields into task readiness for classification, prediction, trajectory modeling, representation learning, treatment-effect estimation, and survival/progression analysis
- treats NACC medication fields as medication/treatment records, not as causal-ready exposure variables
- keeps real-data cohort construction blocked until mapping, missing-code, UDS-version, and design gates are confirmed

v0.9 adds messy real-project triage:

- scans mixed local folders using file names, CSV/TSV headers, and ZIP member names only
- recommends likely core NACC clinical/UDS files before any five-row sampling
- separates CSF/PET/MRI/imaging modules from the initial cohort smoke test
- lets `make_header_samples.py --file-list` sample only the recommended core files
- gives the agent a project-navigation protocol instead of forcing every task through one rigid script

v0.10 adds NACC wide-table concept detection:

- recognizes NACC wide-table patterns such as `PACKET`, `FORMVER`, `UDSVER*`, `DRUG1`-style medication slots, `NACCDIED`, `NACCDAYS`, `NACCFDYS`, and `NACCAVST`
- separates exact dictionary matches from pattern-based candidates
- marks pattern candidates as needing local dictionary confirmation
- keeps medication records separate from causal-ready exposure timing

v0.11 adds the NACC task-intent router:

- routes natural-language NACC study ideas into task families such as prediction, classification, trajectory, survival/progression, biomarker-linked, causal, or representation learning
- outputs `task_profile.yaml` and `task_questions.md`
- keeps design approval and cohort construction blocked until task-specific questions are resolved

## Install Locally as a Codex Skill

Copy or symlink the skill folder into your Codex skills directory:

```powershell
Copy-Item -Recurse -Force ".\skills\dementia-causal-cohort-auditor" "$env:USERPROFILE\.codex\skills\dementia-causal-cohort-auditor"
```

Then start a new Codex task and ask for `dementia-causal-cohort-auditor` behavior on a cohort design.

## Validate an Audit Output

```powershell
python ".\skills\dementia-causal-cohort-auditor\scripts\validate_audit_output.py" ".\examples\outputs\v0_1_example_audit.md"
python ".\skills\dementia-causal-cohort-auditor\scripts\validate_cohort_spec.py" ".\examples\outputs\v0_2_cohort_definition.yaml"
python ".\skills\dementia-causal-cohort-auditor\scripts\validate_nacc_mapping.py" ".\examples\outputs\v0_3_nacc_variable_mapping.yaml"
python ".\skills\dementia-causal-cohort-auditor\scripts\suggest_nacc_mapping.py" ".\examples\inputs\nacc_dictionary_excerpt.csv"
python ".\skills\dementia-causal-cohort-auditor\scripts\generate_synthetic_dementia_data.py" --output-dir ".\examples\inputs\synthetic"
python ".\skills\dementia-causal-cohort-auditor\scripts\build_synthetic_cohort.py" --input-dir ".\examples\inputs\synthetic" --output-dir ".\examples\outputs\synthetic_execution"
python ".\skills\dementia-causal-cohort-auditor\scripts\generate_nacc_like_synthetic_data.py" --output-dir ".\examples\inputs\nacc_like_synthetic"
python ".\skills\dementia-causal-cohort-auditor\scripts\build_nacc_like_cohort.py" --input-dir ".\examples\inputs\nacc_like_synthetic" --output-dir ".\examples\outputs\nacc_like_execution"
python ".\skills\dementia-causal-cohort-auditor\scripts\run_acceptance_checks.py" ".\examples\outputs\nacc_like_execution"
python ".\skills\dementia-causal-cohort-auditor\scripts\scan_nacc_files.py" --input-dir ".\examples\inputs\nacc_like_synthetic" --output-dir ".\examples\outputs\nacc_dry_run"
python ".\skills\dementia-causal-cohort-auditor\scripts\make_header_samples.py" --input-dir ".\examples\inputs\nacc_like_synthetic" --output-dir ".\examples\outputs\nacc_header_only" --rows 0
python ".\skills\dementia-causal-cohort-auditor\scripts\scan_nacc_files.py" --input-dir ".\examples\outputs\nacc_header_only" --output-dir ".\examples\outputs\nacc_header_dry_run" --sample-rows 0 --real-data-mode
python ".\skills\dementia-causal-cohort-auditor\scripts\make_header_samples.py" --input-dir ".\examples\inputs\nacc_like_synthetic" --output-dir ".\examples\outputs\nacc_sample5" --rows 5
python ".\skills\dementia-causal-cohort-auditor\scripts\scan_nacc_files.py" --input-dir ".\examples\outputs\nacc_sample5" --output-dir ".\examples\outputs\nacc_sample5_dry_run" --sample-rows 5 --real-data-mode
python ".\skills\dementia-causal-cohort-auditor\scripts\triage_nacc_project.py" --input-dir "<MESSY_NACC_PROJECT_DIR>" --output-dir "<TRIAGE_OUTPUT_DIR>" --include-zip-headers
python ".\skills\dementia-causal-cohort-auditor\scripts\make_header_samples.py" --input-dir "<MESSY_NACC_PROJECT_DIR>" --output-dir "<SAFE_SAMPLE_DIR>" --rows 5 --file-list "<TRIAGE_OUTPUT_DIR>\recommended_core_files.txt"
python ".\skills\dementia-causal-cohort-auditor\scripts\route_nacc_task_intent.py" --intent "I want to build a NACC cohort of people 65+, dementia-free at baseline, at least two visits, with APOE, to predict cognitive decline." --output-dir ".\examples\outputs\nacc_task_intent"
```

## Create the GitHub Repo

Using GitHub CLI:

```powershell
git init
git add .
git commit -m "Initial v0.1 design critic MVP"
gh repo create dementia-causal-cohort-auditor --public --source . --remote origin --push
```

Using the GitHub website:

1. Create a new empty repo named `dementia-causal-cohort-auditor`.
2. Do not initialize it with README, license, or gitignore.
3. Run:

```powershell
git init
git add .
git commit -m "Initial v0.1 design critic MVP"
git remote add origin https://github.com/YOUR-USER/dementia-causal-cohort-auditor.git
git branch -M main
git push -u origin main
```

## Safety

Use public, synthetic, or de-identified data only. Do not send protected health information to general-purpose agents or public repositories.
