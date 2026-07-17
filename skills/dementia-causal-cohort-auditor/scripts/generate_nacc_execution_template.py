#!/usr/bin/env python
"""Generate v0.16 NACC execution templates.

This script generalizes execution templates beyond prediction/cognitive decline
without constructing cohorts or reading patient-level data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TASKS = {
    "classification": {
        "label": "Cognitive-status / dementia classification cohort",
        "goal": "Build an index-visit feature table and label for baseline or near-baseline phenotype classification.",
        "required_concepts": [
            "participant_id",
            "index_visit",
            "visit_date",
            "age_at_visit",
            "sex",
            "education",
            "classification_label",
            "uds_or_form_version",
        ],
        "outputs": ["cohort_index.csv", "feature_table.csv", "label_table.csv", "attrition_table.csv"],
        "risks": [
            "Do not use the same diagnostic field as both predictor and label unless explicitly approved.",
            "Clarify whether MCI, normal cognition, dementia, FTLD, and LBD labels are mutually exclusive.",
            "Check structural missingness by UDS/form version before model training.",
        ],
    },
    "survival_progression": {
        "label": "Survival / progression cohort",
        "goal": "Build time-to-event data for progression, conversion, death, or censoring analyses.",
        "required_concepts": [
            "participant_id",
            "index_visit",
            "visit_date",
            "baseline_status",
            "event_definition",
            "event_date_or_visit",
            "censoring_date_or_last_contact",
            "death_dropout_context",
        ],
        "outputs": ["cohort_index.csv", "time_to_event_table.csv", "censoring_table.csv", "attrition_table.csv"],
        "risks": [
            "Define whether death is an event, competing event, censoring event, or missing-outcome mechanism.",
            "Ensure event dates occur strictly after time zero.",
            "Avoid immortal time by not conditioning eligibility on future event-free follow-up.",
        ],
    },
    "biomarker_linked": {
        "label": "Biomarker-linked cohort",
        "goal": "Build a clinical cohort linked to CSF/PET/MRI biomarker modules around a defined index window.",
        "required_concepts": [
            "participant_id",
            "clinical_index_visit",
            "biomarker_module",
            "biomarker_measure_date_or_visit",
            "biomarker_value",
            "allowable_linkage_window",
            "baseline_clinical_status",
        ],
        "outputs": ["cohort_index.csv", "biomarker_link_table.csv", "feature_table.csv", "attrition_table.csv"],
        "risks": [
            "Biomarker availability is highly selected and must be reported in attrition.",
            "Confirm whether biomarker measurement occurs before, at, or after clinical index.",
            "Do not combine CSF, PET, and MRI modules without module-specific missingness and timing rules.",
        ],
    },
}


def render_yaml(task: str) -> str:
    spec = TASKS[task]
    lines = [
        'schema_version: "0.16-template"',
        f"task_family: {task}",
        f"label: {quote(spec['label'])}",
        "status: template_not_execution_ready",
        "patient_level_data_read: false",
        "cohort_construction_performed: false",
        "required_concepts:",
    ]
    lines.extend(f"  - {concept}" for concept in spec["required_concepts"])
    lines.extend(
        [
            "approved_design_required:",
            "  - time_zero",
            "  - baseline_window",
            "  - outcome_or_label_definition",
            "  - missing_code_rules",
            "  - uds_form_version_handling",
            "  - selected_field_mappings",
            "expected_outputs:",
        ]
    )
    lines.extend(f"  - {name}" for name in spec["outputs"])
    return "\n".join(lines) + "\n"


def quote(value: str) -> str:
    return '"' + value.replace('"', '\\"') + '"'


def render_pseudocode(task: str) -> str:
    if task == "classification":
        body = """
def build_classification_template(config):
    assert config.design_approved
    rows = load_selected_core_table(config)
    index = select_index_visit(rows, config.time_zero_rule)
    index = apply_population_rules(index, config.inclusion_rules)
    labels = derive_classification_label(index, config.label_rule)
    features = build_baseline_feature_table(index, config.predictor_rules)
    assert no_label_leakage(features, labels, config)
    return assemble_template_outputs(index, features, labels)
"""
    elif task == "survival_progression":
        body = """
def build_survival_progression_template(config):
    assert config.design_approved
    rows = load_selected_core_table(config)
    index = select_index_visit(rows, config.time_zero_rule)
    index = apply_population_rules(index, config.inclusion_rules)
    events = derive_events_after_time_zero(rows, index, config.event_rule)
    censoring = derive_censoring(rows, index, config.censoring_rule)
    assert all_events_after_time_zero(events, index)
    assert no_future_followup_conditioning(index, config)
    return assemble_time_to_event_outputs(index, events, censoring)
"""
    else:
        body = """
def build_biomarker_linked_template(config):
    assert config.design_approved
    clinical = load_selected_core_table(config)
    biomarkers = load_selected_biomarker_modules(config)
    index = select_clinical_index_visit(clinical, config.time_zero_rule)
    linked = link_biomarkers_to_index(index, biomarkers, config.linkage_window)
    linked = apply_biomarker_quality_rules(linked, config.biomarker_rules)
    assert biomarker_timing_matches_design(linked, config)
    return assemble_biomarker_linked_outputs(index, linked)
"""
    header = '''#!/usr/bin/env python
"""v0.16 NACC execution template pseudocode.

This file is a template and must not be treated as an executable cohort builder.
"""
'''
    return header + body.lstrip()


def render_checklist(task: str) -> str:
    spec = TASKS[task]
    lines = [
        f"# {spec['label']} Checklist",
        "",
        "- [ ] Human-approved task definition is recorded.",
        "- [ ] Time zero/index visit is approved.",
        "- [ ] Baseline window is approved.",
        "- [ ] Local NACC dictionary confirms selected field semantics.",
        "- [ ] Missing-code rules are approved.",
        "- [ ] UDS/form-version structural missingness is handled.",
        "- [ ] Attrition stages are defined before execution.",
        "- [ ] Leakage checks are defined before execution.",
        "",
        "## Task-specific risks",
        "",
    ]
    lines.extend(f"- [ ] {risk}" for risk in spec["risks"])
    return "\n".join(lines) + "\n"


def render_test_plan(task: str) -> str:
    shared = [
        "required_files_created",
        "attrition_monotone",
        "unique_index_per_participant",
        "no_patient_ids_in_logs",
        "missingness_report_present",
        "leakage_report_present",
    ]
    task_specific = {
        "classification": ["label_not_used_as_predictor", "class_counts_reported", "phenotype_rule_confirmed"],
        "survival_progression": ["event_after_time_zero", "censoring_after_time_zero", "competing_event_handling_reported"],
        "biomarker_linked": ["biomarker_linkage_window_respected", "module_specific_missingness_reported", "biomarker_selection_attrition_reported"],
    }
    lines = [
        f"# v0.16 Validation Test Plan: {task}",
        "",
        "These tests apply to the future executable builder for this template.",
        "",
    ]
    for name in shared + task_specific[task]:
        lines.extend([f"## {name}", "", "- Expected: pass before releasing a cohort package.", ""])
    return "\n".join(lines)


def render_readme(task: str) -> str:
    spec = TASKS[task]
    lines = [
        f"# {spec['label']}",
        "",
        spec["goal"],
        "",
        "This directory contains v0.16 execution templates only. It does not contain patient-level data or cohort outputs.",
        "",
        "## Files",
        "",
        "- `template_spec.yaml`",
        "- `template_pseudocode.py`",
        "- `implementation_checklist.md`",
        "- `validation_test_plan.md`",
        "- `template_manifest.json`",
    ]
    return "\n".join(lines) + "\n"


def generate(task: str, output_dir: Path) -> None:
    if task not in TASKS:
        raise ValueError(f"Unsupported task family: {task}")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "template_spec.yaml").write_text(render_yaml(task), encoding="utf-8")
    (output_dir / "template_pseudocode.py").write_text(render_pseudocode(task), encoding="utf-8")
    (output_dir / "implementation_checklist.md").write_text(render_checklist(task), encoding="utf-8")
    (output_dir / "validation_test_plan.md").write_text(render_test_plan(task), encoding="utf-8")
    (output_dir / "README.md").write_text(render_readme(task), encoding="utf-8")
    manifest = {
        "schema_version": "0.16",
        "stage": "generalized_nacc_execution_template",
        "task_family": task,
        "patient_level_data_read": False,
        "cohort_construction_performed": False,
        "real_data_outputs_created": False,
        "github_safe": True,
        "outputs": [
            "template_spec.yaml",
            "template_pseudocode.py",
            "implementation_checklist.md",
            "validation_test_plan.md",
            "README.md",
        ],
    }
    (output_dir / "template_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate v0.16 NACC execution templates.")
    parser.add_argument("--task-family", choices=sorted(TASKS), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    generate(args.task_family, args.output_dir)
    print(f"Wrote {args.task_family} execution template to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
