#!/usr/bin/env python
"""Generate a v0.12 NACC design approval packet from task-intent outputs.

Inputs are v0.11 `task_profile.yaml` and `task_questions.md`. Outputs are a
draft cohort spec, draft mapping, assumptions, and human approval checklist.
This script does not read patient data and must not authorize cohort execution.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


CONCEPT_FIELD_HINTS = {
    "participant_id": ["NACCID"],
    "visit_id": ["NACCVNUM"],
    "visit_date": ["VISITMO", "VISITDAY", "VISITYR"],
    "age_at_visit": ["NACCAGE"],
    "baseline_cognitive_status": ["NACCUDSD", "DEMENTED", "CDRGLOB"],
    "longitudinal_cognitive_outcome": ["NACCMMSE", "NACCMOCA", "CDRSUM", "CDRGLOB", "NACCUDSD"],
    "follow_up_availability": ["NACCVNUM", "NACCDAYS", "NACCFDYS", "NACCAVST"],
    "apoe": ["NACCNE4S", "NACCAPOE"],
    "sex": ["SEX"],
    "education": ["EDUC"],
    "cdr_global": ["CDRGLOB"],
    "cdr_sum": ["CDRSUM"],
    "uds_version": ["PACKET", "FORMVER", "UDSVER*", "NACCFORM", "NPFORMVER"],
    "death_dropout": ["NACCDIED", "NACCDAYS", "NACCFDYS", "NACCAVST", "DROPACT"],
    "cognitive_score": ["NACCMMSE", "NACCMOCA"],
    "medication_temporality_support": ["DRUG_START*", "CURRENT_USE", "start/stop/current-use medication fields"],
}


def extract_scalar(text: str, key: str, default: str = "unresolved") -> str:
    match = re.search(rf"^\s*{re.escape(key)}:\s*\"?([^\"\n]+)\"?\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else default


def extract_primary_task(text: str) -> str:
    return extract_scalar(text, "primary_task_type", "unresolved")


def extract_list_block(text: str, block_name: str) -> list[str]:
    pattern = rf"^{re.escape(block_name)}:\s*\n((?:\s+- .+\n)+)"
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        return []
    return [line.split("-", 1)[1].strip() for line in match.group(1).splitlines() if line.strip().startswith("- ")]


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_cohort_definition(task_profile: str, questions: str) -> str:
    task_type = extract_primary_task(task_profile)
    label = extract_scalar(task_profile, "label", task_type)
    original_intent = extract_scalar(task_profile, "original_user_intent")
    age_rule = extract_scalar(task_profile, "age_rule")
    baseline_dementia_free = extract_scalar(task_profile, "baseline_dementia_free")
    minimum_followup = extract_scalar(task_profile, "minimum_followup")
    apoe_requirement = extract_scalar(task_profile, "apoe_requirement")
    outcome = extract_scalar(task_profile, "outcome")
    required = extract_list_block(task_profile, "required_nacc_concepts")
    recommended = extract_list_block(task_profile, "recommended_nacc_concepts")

    unresolved_questions = extract_questions(questions)
    lines = [
        'schema_version: "0.12-draft"',
        "metadata:",
        "  status: needs_human_confirmation",
        "  created_by: dementia-causal-cohort-auditor",
        "  study_phase: nacc_design_approval_packet",
        f"  task_type: {task_type}",
        "  notes: Draft generated from v0.11 task intent routing; not approved for cohort construction.",
        "",
        f"study_question: {yaml_quote(original_intent)}",
        "",
        "estimand:",
        f"  target_population: {yaml_quote(render_population(age_rule, baseline_dementia_free, minimum_followup, apoe_requirement))}",
        "  treatment_strategy: not_applicable_for_noncausal_task_or_unresolved",
        "  comparator_strategy: not_applicable_for_noncausal_task_or_unresolved",
        "  assignment_time: unresolved",
        "  follow_up_start: unresolved; must be after time zero for predictive outcomes",
        f"  outcome: {yaml_quote(outcome)}",
        "  causal_contrast: not_applicable_unless_task_type_is_causal_treatment_effect",
        "",
        "data_source:",
        "  name: nacc",
        "  adapter: nacc",
        "  required_files:",
        "    - core_clinical_uds_table_unresolved",
        "  data_dictionary_required: true",
        "",
        f"population:",
        f"  description: {yaml_quote(render_population(age_rule, baseline_dementia_free, minimum_followup, apoe_requirement))}",
        "",
        "exposure:",
        "  name: not_applicable_or_unresolved",
        "  definition: not_applicable_or_unresolved",
        "  timing: not_applicable_or_unresolved",
        "  washout_period: not_applicable_or_unresolved",
        "  grace_period: not_applicable_or_unresolved",
        "  lag_period: not_applicable_or_unresolved",
        "",
        "comparator:",
        "  name: not_applicable_or_unresolved",
        "  definition: not_applicable_or_unresolved",
        "  timing: not_applicable_or_unresolved",
        "",
        "time_zero:",
        "  definition: unresolved",
        "  candidate_definitions:",
        "    - first NACC visit",
        "    - first eligible dementia-free visit",
        "    - task-specific anchor from human approval",
        "  rationale: Time zero anchors baseline covariates, follow-up, leakage checks, and outcome timing.",
        "",
        "baseline_window:",
        "  start: unresolved",
        "  end: time_zero",
        "  covariate_timing_rule: all predictors must be measured before or at time zero unless explicitly approved",
        "",
        "follow_up:",
        "  start: unresolved; must occur after time zero",
        "  end: unresolved prediction horizon or last eligible follow-up",
        "  censoring_events:",
        "    - loss_to_follow_up_if_applicable",
        "    - death_if_not_modeled_as_competing_event",
        "  competing_events:",
        "    - death_if_outcome_cannot_be_observed_after_death",
        "",
        "outcome:",
        "  name: task_specific_outcome",
        f"  definition: {yaml_quote(outcome)}",
        "  measurement_window: unresolved",
        "  minimum_meaningful_change: unresolved",
        "",
        "inclusion_criteria:",
    ]
    lines.extend(render_criteria(age_rule, baseline_dementia_free, minimum_followup, apoe_requirement))
    lines.extend(
        [
            "",
            "exclusion_criteria:",
            "  - id: exc_baseline_dementia_if_required",
            "    description: Exclude participants with dementia at or before time zero when dementia-free baseline is approved.",
            "    computable: true_after_mapping_confirmation",
            "    concept: baseline_cognitive_status",
            "    time_window: before_or_at_time_zero",
            "    field_mapping: unresolved",
            "    validation_check: no baseline dementia according to approved rule",
            "",
            "covariates:",
        ]
    )
    for concept in required + recommended:
        lines.extend(
            [
                f"  - name: {concept}",
                "    role: required_or_recommended_by_task_profile",
                "    timing: baseline_or_time_invariant_unless_approved_otherwise",
                "    field_mapping: unresolved",
                "    leakage_risk: requires_timing_confirmation",
            ]
        )
    lines.extend(
        [
            "",
            "missingness_plan:",
            "  required_checks:",
            "    - APOE missingness and selection effects if APOE is required.",
            "    - Cognitive outcome missingness by baseline diagnosis, age, sex, education, center, and UDS/form version.",
            "    - Structural missingness by PACKET/FORMVER/UDS version.",
            "  planned_handling: unresolved until human approval",
            "",
            "leakage_checks:",
            "  required_checks:",
            "    - Confirm all predictors are measured before or at time zero.",
            "    - Confirm outcome measurements occur after follow-up start.",
            "    - Confirm follow-up requirements do not condition on future survival or availability without bias discussion.",
            "    - Confirm diagnostic labels are not reused as both predictors and future outcomes unless explicitly intended.",
            "",
            "attrition_plan:",
            "  stages:",
            "    - all_core_clinical_records",
            "    - valid_participant_id",
            "    - valid_visit_order_or_date",
            "    - age_eligible_if_required",
            "    - dementia_free_baseline_if_required",
            "    - apoe_available_if_required",
            "    - follow_up_or_outcome_ascertainable",
            "  count_field: participant_id",
            "",
            "sensitivity_analyses:",
            "  - Compare alternative baseline dementia-free definitions.",
            "  - Compare alternative cognitive decline outcomes or thresholds.",
            "  - Compare APOE complete-case restriction with missingness-aware handling.",
            "  - Evaluate the impact of requiring minimum follow-up visits.",
            "  - Stratify or adjust checks by UDS/form version and center when available.",
            "",
            "assumptions:",
            "  - This is a design approval draft, not an executable cohort definition.",
            "  - Core NACC clinical/UDS table and dictionary binding remain unresolved.",
            "  - Field mappings must be confirmed before execution.",
            "",
            "unresolved_items:",
        ]
    )
    for item_id, question in unresolved_questions:
        lines.extend(
            [
                f"  - id: q_{item_id}",
                "    severity: blocking",
                f"    question: {yaml_quote(question)}",
                "    why_it_matters: Required for design approval and leakage-safe cohort construction.",
            ]
        )
    lines.extend(
        [
            "",
            "readiness:",
            "  ready_for_execution: false",
            "  ready_for_design_approval: false",
            "  blocking_issues:",
            "    - human_design_questions_unresolved",
            "    - field_mappings_unresolved",
            "    - data_dictionary_binding_unresolved",
            "    - aggregate_validation_not_run",
        ]
    )
    return "\n".join(lines) + "\n"


def render_population(age_rule: str, baseline_dementia_free: str, minimum_followup: str, apoe_requirement: str) -> str:
    parts = []
    if age_rule != "unresolved":
        parts.append(f"age {age_rule}")
    if baseline_dementia_free == "requested":
        parts.append("dementia-free at baseline")
    if minimum_followup != "unresolved":
        parts.append(minimum_followup)
    if apoe_requirement == "required":
        parts.append("APOE available")
    return "NACC participants with " + ", ".join(parts) if parts else "NACC target population unresolved"


def render_criteria(age_rule: str, baseline_dementia_free: str, minimum_followup: str, apoe_requirement: str) -> list[str]:
    criteria = []
    if age_rule != "unresolved":
        criteria.extend(
            [
                "  - id: inc_age_rule",
                f"    description: Age at time zero satisfies {age_rule}.",
                "    computable: true_after_mapping_confirmation",
                "    concept: age_at_visit",
                "    time_window: at_time_zero",
                "    field_mapping: unresolved",
                f"    validation_check: age_at_time_zero {age_rule}",
            ]
        )
    if baseline_dementia_free == "requested":
        criteria.extend(
            [
                "  - id: inc_dementia_free_baseline",
                "    description: Participant is dementia-free at baseline according to approved definition.",
                "    computable: true_after_mapping_confirmation",
                "    concept: baseline_cognitive_status",
                "    time_window: baseline_window",
                "    field_mapping: unresolved",
                "    validation_check: baseline_dementia == false under approved rule",
            ]
        )
    if minimum_followup != "unresolved":
        criteria.extend(
            [
                "  - id: inc_follow_up_availability",
                f"    description: Follow-up requirement: {minimum_followup}.",
                "    computable: true_after_mapping_confirmation",
                "    concept: follow_up_availability",
                "    time_window: after_time_zero",
                "    field_mapping: unresolved",
                "    validation_check: approved follow-up rule is satisfied",
            ]
        )
    if apoe_requirement == "required":
        criteria.extend(
            [
                "  - id: inc_apoe_available",
                "    description: APOE information is available.",
                "    computable: true_after_mapping_confirmation",
                "    concept: apoe",
                "    time_window: time_invariant_but_availability_bias_must_be_checked",
                "    field_mapping: unresolved",
                "    validation_check: apoe is not missing under approved missingness rule",
            ]
        )
    return criteria or [
        "  - id: inc_target_population_unresolved",
        "    description: Target population criteria unresolved.",
        "    computable: false",
        "    concept: unresolved",
        "    time_window: unresolved",
        "    field_mapping: unresolved",
        "    validation_check: unresolved",
    ]


def extract_questions(text: str) -> list[tuple[str, str]]:
    questions = []
    for line in text.splitlines():
        match = re.match(r"- \[([A-Za-z0-9_]+)\]\s+(.+)", line.strip())
        if match:
            questions.append((match.group(1), match.group(2)))
    return questions or [("design_questions", "Task-specific design questions are unresolved.")]


def render_mapping_draft(task_profile: str) -> str:
    required = extract_list_block(task_profile, "required_nacc_concepts")
    recommended = extract_list_block(task_profile, "recommended_nacc_concepts")
    lines = [
        'schema_version: "0.12-draft"',
        "adapter: nacc",
        "mapping_metadata:",
        "  status: draft_needs_dictionary_confirmation",
        "  created_by: dementia-causal-cohort-auditor",
        "  selected_core_table: unresolved",
        "  data_dictionary_bound: false",
        "concept_mappings:",
    ]
    for concept in required + recommended:
        role = "required" if concept in required else "recommended"
        lines.extend(
            [
                f"  - concept_id: {concept}",
                f"    role: {role}",
                "    status: candidate_unconfirmed",
                "    candidate_fields:",
            ]
        )
        hints = CONCEPT_FIELD_HINTS.get(concept, [])
        if hints:
            for hint in hints:
                lines.extend(
                    [
                        f"      - field: {hint}",
                        "        evidence: NACC field-name hint; must verify in local dictionary",
                    ]
                )
        else:
            lines.append("      []")
        lines.extend(
            [
                "    selected_field: unresolved",
                "    requires_dictionary_confirmation: true",
                "    approval_status: not_approved",
            ]
        )
    lines.extend(
        [
            "readiness:",
            "  ready_for_cohort_construction: false",
            "  blocking_issues:",
            "    - selected_fields_unresolved",
            "    - local_dictionary_not_bound",
        ]
    )
    return "\n".join(lines) + "\n"


def render_assumptions(task_profile: str, questions: str) -> str:
    task_type = extract_primary_task(task_profile)
    return "\n".join(
        [
            "# Design Packet Assumptions",
            "",
            f"- Task type is currently routed as `{task_type}`.",
            "- The packet is a draft for human approval, not an executable cohort specification.",
            "- The core NACC clinical/UDS table has not been selected inside this packet unless provided elsewhere.",
            "- Local NACC dictionary binding is required before confirming any mapping.",
            "- Time zero, baseline window, outcome definition, follow-up window, missingness handling, and version harmonization remain unresolved unless explicitly answered by the user.",
            "- Minimum follow-up requirements may introduce selection bias if treated as baseline eligibility without justification.",
            "- APOE availability may introduce selection bias and must be reported in attrition if required.",
            "- No patient-level data should be output before explicit cohort-construction approval.",
            "",
            "## Source questions carried into this packet",
            "",
            *[f"- `{item_id}`: {question}" for item_id, question in extract_questions(questions)],
        ]
    ) + "\n"


def render_checklist(task_profile: str, questions: str) -> str:
    task_type = extract_primary_task(task_profile)
    lines = [
        "# Human Approval Checklist",
        "",
        f"Task type: `{task_type}`",
        "",
        "Approve every item before cohort construction.",
        "",
        "## Design decisions",
        "",
    ]
    for item_id, question in extract_questions(questions):
        lines.append(f"- [ ] `{item_id}` resolved: {question}")
    lines.extend(
        [
            "",
            "## Mapping and data gates",
            "",
            "- [ ] Core NACC clinical/UDS table selected.",
            "- [ ] Local NACC data dictionary reviewed.",
            "- [ ] Required field mappings confirmed and selected.",
            "- [ ] Missing codes and structural missingness rules documented.",
            "- [ ] UDS/form version compatibility reviewed.",
            "- [ ] Aggregate validation planned before patient-level cohort output.",
            "",
            "## Execution gate",
            "",
            "- [ ] I approve this design packet for the next stage.",
            "- [ ] I understand this approval is not final approval of the constructed cohort output.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-profile", type=Path, required=True)
    parser.add_argument("--task-questions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    task_profile = args.task_profile.read_text(encoding="utf-8")
    questions = args.task_questions.read_text(encoding="utf-8")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "cohort_definition_draft.yaml").write_text(render_cohort_definition(task_profile, questions), encoding="utf-8")
    (args.output_dir / "mapping_draft.yaml").write_text(render_mapping_draft(task_profile), encoding="utf-8")
    (args.output_dir / "assumptions.md").write_text(render_assumptions(task_profile, questions), encoding="utf-8")
    (args.output_dir / "human_approval_checklist.md").write_text(render_checklist(task_profile, questions), encoding="utf-8")
    print(f"Wrote NACC design approval packet to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
