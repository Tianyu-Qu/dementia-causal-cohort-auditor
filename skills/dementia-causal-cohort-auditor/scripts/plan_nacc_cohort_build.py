#!/usr/bin/env python
"""Generate a v0.14 NACC design-to-code build plan.

This script turns a design packet into an implementation plan and pseudocode.
It does not read patient rows and does not construct a cohort.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEFAULT_OUTPUTS = [
    "build_plan.md",
    "build_pseudocode.py",
    "implementation_checklist.md",
    "validation_test_plan.md",
    "planner_manifest.json",
]


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8", errors="replace")


def scalar(text: str, key: str, default: str = "unresolved") -> str:
    match = re.search(rf"^\s*{re.escape(key)}:\s*\"?([^\"\n]+)\"?\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else default


def block_items(text: str, heading: str) -> list[str]:
    pattern = rf"^\s*{re.escape(heading)}:\s*\n((?:\s+- .+\n)+)"
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        return []
    return [line.split("-", 1)[1].strip() for line in match.group(1).splitlines() if line.strip().startswith("- ")]


def concept_fields(mapping_text: str) -> dict[str, dict[str, object]]:
    concepts: dict[str, dict[str, object]] = {}
    chunks = re.split(r"\n\s*-\s+concept_id:\s+", "\n" + mapping_text)
    for chunk in chunks[1:]:
        concept_id, _, rest = chunk.partition("\n")
        candidates = re.findall(r"^\s+-\s+field:\s*([A-Za-z0-9_*:.\\-]+)", rest, flags=re.MULTILINE)
        selected = scalar(rest, "selected_field", "unresolved")
        approval = scalar(rest, "approval_status", "not_approved")
        status = scalar(rest, "status", "candidate_unconfirmed")
        concepts[concept_id.strip()] = {
            "candidate_fields": candidates,
            "selected_field": selected,
            "approval_status": approval,
            "status": status,
        }
    return concepts


def unresolved_questions(cohort_text: str) -> list[str]:
    return re.findall(r"question:\s*\"([^\"]+)\"", cohort_text)


def manifest_from_aggregate(path: Path | None) -> dict[str, object]:
    if not path:
        return {}
    manifest_path = path / "aggregate_validation_manifest.json" if path.is_dir() else path
    if not manifest_path.exists():
        return {"status": "not_found", "path": str(manifest_path)}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "invalid_json", "path": str(manifest_path)}


def readiness(cohort_text: str, mapping_text: str, aggregate: dict[str, object]) -> tuple[str, list[str], list[str]]:
    blockers = []
    warnings = []
    metadata_status = scalar(cohort_text, "status", "unresolved")
    if metadata_status not in {"approved", "human_approved", "design_approved"}:
        blockers.append(f"Design packet status is not approved: {metadata_status}")
    if "selected_field: unresolved" in mapping_text:
        blockers.append("Mapping contains unresolved selected_field entries.")
    if "approval_status: not_approved" in mapping_text:
        blockers.append("Mapping contains not_approved concepts.")
    if not aggregate:
        warnings.append("No aggregate validation manifest supplied.")
    elif aggregate.get("ready_for_cohort_construction") is not False:
        warnings.append("Aggregate manifest should not itself approve cohort construction.")
    if aggregate.get("blockers"):
        blockers.append("Aggregate validation reported blockers.")
    if blockers:
        return "blocked_planner_draft", blockers, warnings
    return "planner_ready_for_human_review", blockers, warnings


def render_build_plan(cohort_text: str, mapping_text: str, aggregate: dict[str, object]) -> str:
    concepts = concept_fields(mapping_text)
    status, blockers, warnings = readiness(cohort_text, mapping_text, aggregate)
    task_type = scalar(cohort_text, "task_type", "unresolved")
    study_question = scalar(cohort_text, "study_question", "unresolved")
    attrition_stages = block_items(cohort_text, "stages") or [
        "all_core_clinical_records",
        "valid_participant_id",
        "valid_visit_order_or_date",
        "baseline_eligible",
        "outcome_ascertainable",
    ]
    lines = [
        "# NACC Cohort Build Plan",
        "",
        f"- Planner status: {status}",
        f"- Task type: {task_type}",
        f"- Study question: {study_question}",
        "- Patient-level data read: no",
        "- Cohort construction performed: no",
        "- Ready for executable cohort build: false",
        "",
        "## Inputs Expected by the Future Builder",
        "",
        "- Approved `cohort_definition.yaml` with resolved time zero, baseline window, outcome window, and missingness rules.",
        "- Approved `mapping.yaml` with selected fields and dictionary-confirmed coding.",
        "- Aggregate validation packet from v0.13.",
        "- Local NACC core clinical/UDS table path and optional module paths.",
        "",
        "## Concept-to-Field Plan",
        "",
    ]
    for concept, data in concepts.items():
        selected = data["selected_field"]
        candidates = ", ".join(data["candidate_fields"]) or "none"
        lines.append(f"- {concept}: selected={selected}; candidates={candidates}; approval={data['approval_status']}")
    lines.extend(["", "## Execution Stages", ""])
    stage_descriptions = {
        "all_core_clinical_records": "Load core NACC clinical/UDS rows with minimal selected columns.",
        "valid_participant_id": "Drop rows without a valid participant identifier; never write IDs to logs.",
        "valid_visit_order_or_date": "Create visit order and visit date; flag incomplete dates.",
        "age_eligible_if_required": "Select index candidates satisfying the approved age rule.",
        "dementia_free_baseline_if_required": "Apply the approved dementia-free baseline rule.",
        "apoe_available_if_required": "Apply the approved APOE availability rule and report attrition.",
        "follow_up_or_outcome_ascertainable": "Confirm post-index follow-up/outcome availability without temporal leakage.",
    }
    for idx, stage in enumerate(attrition_stages, 1):
        lines.append(f"{idx}. `{stage}`: {stage_descriptions.get(stage, 'Apply approved rule and report count changes.')}")
    lines.extend(
        [
            "",
            "## Required Builder Functions",
            "",
            "- `load_selected_nacc_tables(config)`",
            "- `normalize_missing_codes(df, dictionary_rules)`",
            "- `construct_visit_date(df)`",
            "- `select_index_visit(df, approved_time_zero_rule)`",
            "- `apply_baseline_eligibility(df, index_df, approved_rules)`",
            "- `derive_prediction_outcome(df, index_df, approved_outcome_rule)`",
            "- `build_feature_table(df, index_df, approved_predictor_window)`",
            "- `write_attrition_table(stage_counts)`",
            "- `write_data_quality_report(checks)`",
            "- `write_leakage_report(checks)`",
            "- `write_reproducibility_manifest(config, inputs, code_version)`",
            "",
            "## Blockers",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- None at planner level.")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- None.")
    lines.extend(
        [
            "",
            "## Gate",
            "",
            "This plan is for human review and future implementation only. Do not run patient-level cohort construction until v0.15 conditions are met.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_pseudocode(cohort_text: str, mapping_text: str) -> str:
    _ = cohort_text, mapping_text
    return '''#!/usr/bin/env python
"""Pseudocode for future NACC cohort construction.

Generated by v0.14 design-to-code planner. This file is intentionally not a
ready-to-run cohort builder.
"""


def main(config):
    assert config.design_status in {"approved", "human_approved", "design_approved"}
    assert config.mapping_all_selected_fields_confirmed is True
    assert config.real_data_execution_approved_by_user is True

    core = load_selected_nacc_tables(config)
    core = normalize_missing_codes(core, config.dictionary_rules)
    core = construct_visit_date(core)

    stage_counts = []
    stage_counts.append(count_stage("all_core_clinical_records", core))

    valid_rows = require_valid_participant_and_visit(core)
    stage_counts.append(count_stage("valid_participant_id_and_visit", valid_rows))

    index_visits = select_index_visit(valid_rows, config.time_zero_rule)
    index_visits = apply_age_rule(index_visits, config.age_rule)
    stage_counts.append(count_stage("age_eligible_if_required", index_visits))

    index_visits = apply_baseline_dementia_free_rule(
        valid_rows,
        index_visits,
        config.baseline_window,
        config.baseline_dementia_rule,
    )
    stage_counts.append(count_stage("dementia_free_baseline_if_required", index_visits))

    index_visits = apply_apoe_rule(index_visits, config.apoe_missingness_rule)
    stage_counts.append(count_stage("apoe_available_if_required", index_visits))

    outcomes = derive_prediction_outcome(
        valid_rows,
        index_visits,
        config.outcome_definition,
        config.follow_up_window,
    )
    assert all_outcomes_after_time_zero(outcomes, index_visits)

    features = build_feature_table(valid_rows, index_visits, config.predictor_window)
    assert no_post_index_predictors(features, index_visits)

    package = assemble_cohort_package(index_visits, features, outcomes)
    write_attrition_table(stage_counts)
    write_data_quality_report(run_data_quality_checks(package, valid_rows, config))
    write_leakage_report(run_leakage_checks(package, valid_rows, config))
    write_reproducibility_manifest(config)
    return package
'''


def render_checklist(cohort_text: str, mapping_text: str, aggregate: dict[str, object]) -> str:
    status, blockers, warnings = readiness(cohort_text, mapping_text, aggregate)
    checks = [
        "Human-approved time zero/index visit rule is recorded.",
        "Human-approved baseline window is recorded.",
        "Baseline dementia-free rule is selected and dictionary-confirmed.",
        "Outcome definition, threshold, and follow-up window are selected.",
        "Minimum follow-up requirement is classified as eligibility or ascertainment.",
        "APOE missingness handling and attrition reporting are approved.",
        "UDS/form-version structural missingness handling is approved.",
        "Death/dropout handling is approved.",
        "All selected mapping fields are resolved and dictionary-confirmed.",
        "v0.13 aggregate validation has no unresolved blockers.",
    ]
    lines = [
        "# NACC Build Implementation Checklist",
        "",
        f"- Planner status: {status}",
        "- Cohort construction allowed now: no",
        "",
    ]
    for item in checks:
        lines.append(f"- [ ] {item}")
    if blockers or warnings:
        lines.extend(["", "## Current Issues", ""])
        lines.extend(f"- BLOCKER: {item}" for item in blockers)
        lines.extend(f"- WARNING: {item}" for item in warnings)
    return "\n".join(lines) + "\n"


def render_test_plan() -> str:
    tests = [
        ("test_no_patient_ids_in_logs", "Builder logs and reports must not list NACCID values."),
        ("test_attrition_monotonic", "Attrition participant counts must be monotonic non-increasing."),
        ("test_unique_index_visit", "Each participant must have exactly one index visit."),
        ("test_outcome_after_time_zero", "Outcome measurements must occur after time zero."),
        ("test_no_post_index_features", "Feature table must exclude post-index variables unless explicitly approved."),
        ("test_duplicate_visit_detection", "Duplicate participant-visit rows must be detected and handled."),
        ("test_missingness_by_form_version", "Missingness report must stratify key fields by form/version context."),
        ("test_apoe_attrition_reported", "APOE restriction must produce explicit attrition and missingness counts."),
        ("test_sensitivity_hooks_present", "Approved sensitivity-analysis hooks must be represented in config."),
    ]
    lines = [
        "# NACC Cohort Builder Validation Test Plan",
        "",
        "These tests are for the future executable builder. v0.14 does not construct a cohort.",
        "",
    ]
    for name, purpose in tests:
        lines.extend([f"## {name}", "", f"- Purpose: {purpose}", "- Expected result: pass before releasing any cohort package.", ""])
    return "\n".join(lines)


def run(design_packet_dir: Path, output_dir: Path, aggregate_validation_dir: Path | None) -> None:
    cohort_text = read_text(design_packet_dir / "cohort_definition_draft.yaml")
    mapping_text = read_text(design_packet_dir / "mapping_draft.yaml")
    aggregate = manifest_from_aggregate(aggregate_validation_dir)
    status, blockers, warnings = readiness(cohort_text, mapping_text, aggregate)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "build_plan.md").write_text(render_build_plan(cohort_text, mapping_text, aggregate), encoding="utf-8")
    (output_dir / "build_pseudocode.py").write_text(render_pseudocode(cohort_text, mapping_text), encoding="utf-8")
    (output_dir / "implementation_checklist.md").write_text(render_checklist(cohort_text, mapping_text, aggregate), encoding="utf-8")
    (output_dir / "validation_test_plan.md").write_text(render_test_plan(), encoding="utf-8")
    manifest = {
        "schema_version": "0.14",
        "stage": "nacc_design_to_code_planner",
        "planner_status": status,
        "patient_level_data_read": False,
        "cohort_construction_performed": False,
        "ready_for_executable_cohort_build": False,
        "blockers": blockers,
        "warnings": warnings,
        "outputs": DEFAULT_OUTPUTS[:-1],
    }
    (output_dir / "planner_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a NACC design-to-code plan without cohort construction.")
    parser.add_argument("--design-packet-dir", required=True, help="Directory containing v0.12 cohort_definition_draft.yaml and mapping_draft.yaml.")
    parser.add_argument("--output-dir", required=True, help="Output directory for v0.14 planner files.")
    parser.add_argument("--aggregate-validation-dir", help="Optional v0.13 aggregate validation directory or manifest path.")
    args = parser.parse_args()
    run(
        Path(args.design_packet_dir),
        Path(args.output_dir),
        Path(args.aggregate_validation_dir) if args.aggregate_validation_dir else None,
    )
    print(f"Design-to-code plan written to {Path(args.output_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
