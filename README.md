# Dementia Causal-Cohort Auditor

A Codex skill and reference implementation for building reviewable, leakage-aware dementia cohorts from NACC-style data.

This project is intentionally not a generic medical data-cleaning agent. It is a NACC-first cohort construction copilot: it helps a user turn a natural-language dementia research or modeling idea into a critiqued design, dataset-specific mapping, reproducible cohort package, and acceptance report.

The skill is designed to behave less like a SQL generator and more like a rigorous methods collaborator. Before writing code, it asks whether the study design is valid: What is time zero? What is baseline? Is follow-up an eligibility rule or an outcome-ascertainment rule? Are APOE complete cases selected? Are MMSE/MoCA and UDS version differences handled? Is a medication field actually enough for treatment-effect estimation?

## What v0.x Can Do

The first major version now supports the full NACC workflow architecture:

```text
User states a NACC study/modeling idea
-> route task intent
-> critique design and ask blocking questions
-> generate a design approval packet
-> inspect NACC folder/header structure
-> validate aggregate feasibility
-> plan implementation
-> construct a guarded cohort package for supported tasks
-> run acceptance checks
-> return to human approval before freezing
```

The most complete executable path is currently:

```text
NACC prediction / cognitive decline
```

For that task family, the project includes synthetic/NACC-like executable examples and a guarded real-NACC pilot script.

## NACC-First Design

The project focuses first on NACC because the hard part is not generating code; it is understanding a messy longitudinal clinical dataset well enough to avoid invalid cohorts.

The skill includes tools for:

- messy local NACC folder triage
- header-only and small-sample preflight
- NACC wide-table concept detection
- variable mapping candidates
- concept coverage reports
- aggregate-only real-data validation
- human approval packets
- design-to-code planning
- executable prediction cohort construction
- acceptance checks for attrition, leakage, missingness, and temporal validity

Real NACC data are never included in this repository.

## Capability by Task Family

| Task family | Current depth |
| --- | --- |
| Prediction / cognitive decline | End-to-end path implemented. Synthetic/NACC-like execution is included in the repo. A guarded real-NACC pilot was tested locally. |
| Classification / phenotyping | Intent routing, design guidance, cohort spec drafting, and execution templates are implemented. Full real-data executable builder is not yet implemented. |
| Survival / progression | Intent routing, design guidance, cohort spec drafting, and execution templates are implemented. Full real-data executable builder is not yet implemented. |
| Biomarker-linked cohorts | Intent routing, design guidance, cohort spec drafting, and execution templates are implemented. Full biomarker module execution is not yet implemented. |
| Representation learning | Intent routing and design guidance exist, but execution support is still early. |
| Causal inference / treatment effect | Target-trial readiness and causal execution templates are implemented. The skill blocks execution when medication temporality is insufficient. It is not yet a treatment-effect estimator. |

## Real NACC Validation Status

This repository contains only synthetic or NACC-like example data.

Separately, the guarded real-NACC prediction pilot was tested locally with Codex on a private NACC extract using `investigator_ftldlbd_nacc70.csv`. The tested task was:

```text
Age 65+, baseline dementia-free, APOE available,
at least one post-index MMSE follow-up,
using baseline information to predict cognitive decline.
```

That local pilot successfully produced a cohort package and acceptance report. The real NACC outputs are private, local-only, and intentionally not committed to GitHub.

## Repository Safety Boundary

This repository should contain:

- skill instructions
- scripts
- references
- unit tests
- synthetic examples
- NACC-like synthetic examples

This repository should not contain:

- real NACC CSV files
- NACCID values from real data
- real patient-level cohort outputs
- private data dictionaries if redistribution is not allowed
- local `nacc_real_preflight` or `nacc_skill_test` outputs

When running real NACC experiments, write outputs to a private local directory outside the repository and do not paste patient rows into chat.

## Core Architecture

1. Trigger Layer: decide when the skill should activate.
2. Decision Layer: decide whether to critique, ask questions, build specs, map variables, generate code, or validate results.
3. Core Knowledge Layer: dementia SOP plus causal inference audit rules.
4. Adapter Layer: NACC-first, with synthetic examples and planned extension to other datasets.
5. Workflow Layer: protocol from research question to audit memo and approval packet.
6. Execution Layer: scripts for preflight, planning, synthetic execution, guarded real pilot, and templates.
7. Acceptance Layer: computational and methodological checks before downstream analysis.

## Install as a Codex Skill

Copy the skill folder into your local Codex skills directory:

```powershell
Copy-Item -Recurse -Force ".\skills\dementia-causal-cohort-auditor" "$env:USERPROFILE\.codex\skills\dementia-causal-cohort-auditor"
```

Then start a new Codex task and ask it to use `dementia-causal-cohort-auditor`.

Example:

```text
Use the dementia-causal-cohort-auditor skill.
I want to build a NACC cohort of participants age 65+, dementia-free at baseline,
with APOE available and at least one follow-up MMSE, to predict cognitive decline.
First critique the design and ask blocking questions before writing code.
```

## Quick Synthetic Demo

Generate NACC-like synthetic data:

```powershell
python ".\skills\dementia-causal-cohort-auditor\scripts\generate_nacc_like_synthetic_data.py" --output-dir ".\examples\inputs\nacc_like_synthetic"
```

Run the first executable prediction cohort builder:

```powershell
python ".\skills\dementia-causal-cohort-auditor\scripts\build_nacc_prediction_cohort.py" --input-dir ".\examples\inputs\nacc_like_synthetic" --output-dir ".\examples\outputs\nacc_prediction_execution"
```

Review:

```powershell
Get-Content ".\examples\outputs\nacc_prediction_execution\acceptance_report.md"
```

## Real NACC Guarded Pilot

Only run this on private local data, after you explicitly approve the conservative pilot rules:

```powershell
python ".\skills\dementia-causal-cohort-auditor\scripts\build_real_nacc_prediction_pilot.py" `
  --core-file "<REAL_NACC_DIR>\investigator_ftldlbd_nacc70.csv" `
  --output-dir "<LOCAL_PRIVATE_OUTPUT_DIR>" `
  --allow-real-data `
  --approved-pilot-rules
```

Do not commit `<LOCAL_PRIVATE_OUTPUT_DIR>`.

The guarded pilot supports only the narrow prediction/cognitive-decline task described above. It is not a general real-NACC builder and not a treatment-effect estimator.

## Template Generators

Generate generalized execution templates:

```powershell
python ".\skills\dementia-causal-cohort-auditor\scripts\generate_nacc_execution_template.py" --task-family classification --output-dir "<TEMPLATE_OUTPUT_DIR>"
python ".\skills\dementia-causal-cohort-auditor\scripts\generate_nacc_execution_template.py" --task-family survival_progression --output-dir "<TEMPLATE_OUTPUT_DIR>"
python ".\skills\dementia-causal-cohort-auditor\scripts\generate_nacc_execution_template.py" --task-family biomarker_linked --output-dir "<TEMPLATE_OUTPUT_DIR>"
```

Generate causal readiness and target-trial templates:

```powershell
python ".\skills\dementia-causal-cohort-auditor\scripts\generate_nacc_causal_execution_package.py" --output-dir "<CAUSAL_TEMPLATE_OUTPUT_DIR>"
```

## Run Tests

```powershell
python -m unittest discover -s tests
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" ".\skills\dementia-causal-cohort-auditor"
```

## Suggested Tag and Release

After committing README changes and pushing `main`, create a first major development tag:

```powershell
git tag -a v0.17.0 -m "First complete NACC-first skill workflow"
git push origin main
git push origin v0.17.0
```

If GitHub CLI is installed, create a release:

```powershell
gh release create v0.17.0 `
  --title "v0.17.0: First complete NACC-first workflow" `
  --notes "First complete NACC-first workflow for dementia cohort auditing: task routing, design approval packets, NACC preflight, aggregate validation, design-to-code planning, executable prediction cohort construction, guarded real-NACC pilot support, generalized templates, and causal readiness gates. The repository contains only synthetic/NACC-like examples; real NACC validation was performed locally and is not included."
```

If `gh` is unavailable, create the release manually on GitHub from the `v0.17.0` tag and use the same notes.

## Limitations

- The real executable path is currently strongest for prediction/cognitive decline.
- Classification, survival/progression, and biomarker-linked tasks have templates but not full real-data builders.
- Causal/treatment-effect execution is deliberately blocked unless exposure temporality and target-trial assumptions are confirmed.
- NACC field semantics and missing-code rules must be confirmed against the user's local NACC dictionary before scientific use.

## Safety

Use public, synthetic, or properly authorized local data only. Do not send protected health information or restricted NACC data to public repositories, public logs, or general-purpose chat outputs.
