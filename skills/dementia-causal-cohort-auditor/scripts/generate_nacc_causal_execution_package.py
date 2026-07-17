#!/usr/bin/env python
"""Generate v0.17 NACC causal inference execution package.

This is a causal-specific execution template and readiness gate. It does not
read patient-level data and does not estimate treatment effects.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_CAUSAL_DECISIONS = [
    "target_trial_protocol",
    "treatment_strategy",
    "active_comparator_or_control_strategy",
    "new_user_definition",
    "washout_window",
    "grace_period",
    "lag_window",
    "time_zero",
    "baseline_covariate_window",
    "outcome_definition_and_window",
    "censoring_and_competing_event_rules",
    "positivity_assessment",
    "confounding_adjustment_plan",
]


def render_spec(estimation_family: str) -> str:
    lines = [
        'schema_version: "0.17-causal-template"',
        "stage: nacc_causal_inference_specific_execution",
        f"estimation_family: {estimation_family}",
        "status: blocked_until_causal_design_and_exposure_temporality_confirmed",
        "patient_level_data_read: false",
        "cohort_construction_performed: false",
        "treatment_effect_estimated: false",
        "nacc_medication_warning: NACC medication records are not automatically causal-ready exposure histories.",
        "",
        "required_causal_decisions:",
    ]
    lines.extend(f"  - {item}" for item in REQUIRED_CAUSAL_DECISIONS)
    lines.extend(
        [
            "",
            "required_data_support:",
            "  - participant identifier",
            "  - visit dates or event dates",
            "  - treatment or exposure records",
            "  - treatment start timing",
            "  - treatment stop/current-use/persistence support if relevant",
            "  - baseline covariates before time zero",
            "  - post-index outcomes",
            "  - censoring/death/dropout context",
            "  - local dictionary-confirmed missing codes",
            "",
            "hard_blockers:",
            "  - medication_temporality_support_insufficient",
            "  - comparator_strategy_unresolved",
            "  - time_zero_unresolved",
            "  - outcome_window_unresolved",
            "  - baseline_covariates_include_post_index_information",
            "  - positivity_not_assessed",
        ]
    )
    return "\n".join(lines) + "\n"


def render_pseudocode(estimation_family: str) -> str:
    return f'''#!/usr/bin/env python
"""v0.17 causal inference execution pseudocode.

Template only. Do not run as a real treatment-effect estimator.
"""


def build_causal_cohort_template(config):
    assert config.design_approved
    assert config.mapping_approved
    assert config.exposure_temporality_confirmed
    assert config.estimation_family == "{estimation_family}"

    target_trial = load_target_trial_protocol(config)
    exposure_records = load_exposure_records(config)
    clinical_records = load_clinical_records(config)

    eligible_new_users = apply_new_user_and_washout_rules(
        exposure_records,
        target_trial.treatment_strategy,
        target_trial.comparator_strategy,
        target_trial.washout_window,
    )

    index = assign_time_zero(eligible_new_users, target_trial.assignment_time)
    baseline = build_baseline_covariates(clinical_records, index, target_trial.baseline_window)
    assert no_post_index_covariates(baseline, index)

    exposure = classify_treatment_strategy(
        exposure_records,
        index,
        target_trial.grace_period,
        target_trial.persistence_rule,
    )
    outcome = derive_post_index_outcome(clinical_records, index, target_trial.outcome_window)
    censoring = derive_censoring(clinical_records, index, target_trial.censoring_rules)

    checks = run_causal_design_checks(index, baseline, exposure, outcome, censoring)
    assert checks.no_immortal_time
    assert checks.positivity_supported
    assert checks.outcomes_after_time_zero

    analysis_dataset = assemble_analysis_dataset(index, baseline, exposure, outcome, censoring)
    diagnostics = run_balance_positivity_and_missingness_diagnostics(analysis_dataset)
    return analysis_dataset, diagnostics
'''


def render_target_trial_checklist() -> str:
    lines = [
        "# Target Trial Emulation Checklist",
        "",
        "- [ ] Eligibility criteria are defined at or before time zero.",
        "- [ ] Treatment strategies are well-defined and clinically meaningful.",
        "- [ ] Comparator is active comparator or justified control.",
        "- [ ] New-user definition is specified.",
        "- [ ] Washout window is specified and computable.",
        "- [ ] Grace period is specified.",
        "- [ ] Lag window is specified if treatment effect onset is delayed.",
        "- [ ] Treatment persistence/discontinuation rules are specified if relevant.",
        "- [ ] Assignment time/time zero is specified.",
        "- [ ] Baseline covariate window excludes post-index information.",
        "- [ ] Outcome start and end windows are specified.",
        "- [ ] Censoring and competing events are specified.",
        "- [ ] Confounder set is justified by domain knowledge, not variable availability alone.",
        "- [ ] Positivity diagnostics are planned.",
        "- [ ] Sensitivity analyses are planned.",
    ]
    return "\n".join(lines) + "\n"


def render_readiness_report(nacc_medication_temporality: str) -> str:
    blockers = []
    warnings = []
    if nacc_medication_temporality != "confirmed":
        blockers.append("Medication/exposure temporality is not confirmed. NACC medication records alone are insufficient for causal treatment-effect execution.")
    warnings.extend(
        [
            "DRUG1-style or ANYMEDS-style fields may indicate medication records but not start/stop histories.",
            "Treatment-effect estimation requires a target-trial protocol, not just a cohort definition.",
            "Prediction-ready NACC cohorts are not automatically causal-ready.",
        ]
    )
    status = "blocked" if blockers else "template_ready_pending_human_approval"
    lines = [
        "# NACC Causal Execution Readiness Report",
        "",
        f"- Status: {status}",
        "- Patient-level data read: false",
        "- Cohort construction performed: false",
        "- Treatment effect estimated: false",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- None at template level.")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in warnings)
    lines.extend(
        [
            "",
            "## Gate",
            "",
            "Do not build a causal treatment-effect cohort until exposure timing, comparator, washout, grace, lag, outcome window, censoring, and confounding adjustment are approved.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_validation_test_plan(estimation_family: str) -> str:
    tests = [
        "required_files_created",
        "target_trial_protocol_present",
        "new_user_washout_rule_applied",
        "active_comparator_or_control_present",
        "time_zero_not_after_exposure_assignment",
        "baseline_covariates_pre_index_only",
        "no_immortal_time",
        "outcome_after_lag_window",
        "censoring_after_time_zero",
        "positivity_diagnostics_reported",
        "balance_diagnostics_reported",
        "attrition_monotone",
        "no_patient_ids_in_logs",
    ]
    lines = [
        f"# Causal Validation Test Plan: {estimation_family}",
        "",
        "These tests apply to a future executable causal builder. v0.17 does not estimate treatment effects.",
        "",
    ]
    for test in tests:
        lines.extend([f"## {test}", "", "- Expected: pass before releasing any causal analysis dataset.", ""])
    return "\n".join(lines)


def render_manifest(estimation_family: str, nacc_medication_temporality: str) -> str:
    status = "blocked" if nacc_medication_temporality != "confirmed" else "template_ready_pending_human_approval"
    manifest = {
        "schema_version": "0.17",
        "stage": "nacc_causal_inference_specific_execution",
        "estimation_family": estimation_family,
        "nacc_medication_temporality": nacc_medication_temporality,
        "status": status,
        "patient_level_data_read": False,
        "cohort_construction_performed": False,
        "treatment_effect_estimated": False,
        "real_data_outputs_created": False,
        "github_safe": True,
        "outputs": [
            "causal_execution_spec.yaml",
            "causal_pseudocode.py",
            "target_trial_checklist.md",
            "causal_readiness_report.md",
            "causal_validation_test_plan.md",
        ],
    }
    return json.dumps(manifest, indent=2) + "\n"


def generate(output_dir: Path, estimation_family: str, nacc_medication_temporality: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "causal_execution_spec.yaml").write_text(render_spec(estimation_family), encoding="utf-8")
    (output_dir / "causal_pseudocode.py").write_text(render_pseudocode(estimation_family), encoding="utf-8")
    (output_dir / "target_trial_checklist.md").write_text(render_target_trial_checklist(), encoding="utf-8")
    (output_dir / "causal_readiness_report.md").write_text(render_readiness_report(nacc_medication_temporality), encoding="utf-8")
    (output_dir / "causal_validation_test_plan.md").write_text(render_validation_test_plan(estimation_family), encoding="utf-8")
    (output_dir / "causal_template_manifest.json").write_text(render_manifest(estimation_family, nacc_medication_temporality), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate v0.17 NACC causal execution template/readiness package.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--estimation-family", choices=["ate", "att", "per_protocol", "as_treated"], default="ate")
    parser.add_argument("--nacc-medication-temporality", choices=["insufficient", "candidate", "confirmed"], default="insufficient")
    args = parser.parse_args()
    generate(args.output_dir, args.estimation_family, args.nacc_medication_temporality)
    print(f"Wrote NACC causal execution package to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
