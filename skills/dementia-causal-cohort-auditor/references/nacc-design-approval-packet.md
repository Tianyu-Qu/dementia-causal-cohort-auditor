# NACC Design Approval Packet

Use this reference after v0.11 task-intent routing and before any cohort construction.

## Purpose

Convert `task_profile.yaml` and `task_questions.md` into a human-reviewable design packet:

- `cohort_definition_draft.yaml`
- `mapping_draft.yaml`
- `assumptions.md`
- `human_approval_checklist.md`

This stage must not read patient-level data or run cohort construction.

## Workflow

1. Generate or receive v0.11 task-intent outputs.
2. Run:

   ```powershell
   python skills/dementia-causal-cohort-auditor/scripts/generate_nacc_design_packet.py --task-profile <TASK_PROFILE_YAML> --task-questions <TASK_QUESTIONS_MD> --output-dir <DESIGN_PACKET_DIR>
   ```

3. Review the packet with the user.
4. Stop at the human approval gate.

## Required Gates

The draft cohort definition must keep:

```yaml
metadata:
  status: needs_human_confirmation
readiness:
  ready_for_design_approval: false
  ready_for_execution: false
```

The mapping draft must keep:

```yaml
data_dictionary_bound: false
selected_field: unresolved
ready_for_cohort_construction: false
```

## Agent Behavior

- Explain the design packet in plain language.
- Highlight unresolved questions carried from `task_questions.md`.
- Do not promote candidate fields to selected fields.
- Do not run aggregate validation or cohort construction yet.
- Ask the user to approve or revise the design packet before moving to v0.13.

## Why This Exists

This packet creates the first formal approval boundary:

```text
intent -> design draft -> human approval -> validation/planning
```

It prevents the agent from jumping from a natural-language idea directly to patient-level cohort output.
