# NACC Task Intent Router

Use this reference when a user describes a NACC cohort idea, modeling goal, prediction task, causal question, survival/progression analysis, biomarker-linked study, trajectory analysis, or representation learning task.

## Purpose

Route a natural-language study idea into a task profile before mapping fields or constructing cohorts.

The router should produce:

- `task_profile.yaml`
- `task_questions.md`

Do not perform cohort construction in this stage.

## Supported Task Families

- `prediction_cognitive_decline`
- `classification`
- `trajectory_modeling`
- `survival_progression`
- `biomarker_linked`
- `causal_treatment_effect`
- `representation_learning`

## Workflow

1. Parse the user’s intent.
2. Identify the primary task family and plausible alternatives.
3. Extract obvious design hints:
   - target population
   - age rule
   - dementia-free baseline request
   - minimum follow-up request
   - APOE requirement
   - candidate outcome
4. Generate task-specific must-answer questions.
5. Stop before design approval or cohort construction.

Use:

```powershell
python skills/dementia-causal-cohort-auditor/scripts/route_nacc_task_intent.py --intent "<USER_INTENT>" --output-dir <TASK_OUTPUT_DIR>
```

## Design Gate

The output must set:

```yaml
ready_for_design_approval: false
ready_for_cohort_construction: false
```

until a human resolves the design questions.

## Example

Input:

```text
I want to build a NACC cohort of people 65+, dementia-free at baseline, at least two visits, with APOE, to predict cognitive decline.
```

Expected routing:

```yaml
primary_task_type: prediction_cognitive_decline
target_population:
  age_rule: ">= 65"
  baseline_dementia_free: "requested"
  minimum_followup: ">= 2 visits requested"
  apoe_requirement: "required"
ready_for_cohort_construction: false
```

Expected must-answer questions include:

- Which field defines dementia-free baseline?
- Which outcome defines cognitive decline?
- What is time zero?
- Is two-visit follow-up an eligibility rule or outcome ascertainment rule?
- How should APOE missingness be handled?
- How should UDS/form version differences be handled?
