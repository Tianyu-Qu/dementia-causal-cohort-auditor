#!/usr/bin/env python
"""Route a natural-language NACC cohort idea into a task profile.

This script does not read patient data. It only parses a research/cohort idea
and emits a draft task profile plus human design questions.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


TASKS = {
    "prediction_cognitive_decline": {
        "label": "Prediction / cognitive decline",
        "keywords": ["predict", "prediction", "decline", "conversion", "progression", "预测", "下降", "转化", "进展"],
        "required_concepts": [
            "participant_id",
            "visit_id",
            "visit_date",
            "age_at_visit",
            "baseline_cognitive_status",
            "longitudinal_cognitive_outcome",
            "follow_up_availability",
        ],
        "recommended_concepts": ["sex", "education", "apoe", "cdr_global", "cdr_sum", "uds_version", "death_dropout"],
        "execution_family": "prediction_or_progression",
    },
    "classification": {
        "label": "Classification / phenotyping",
        "keywords": ["classify", "classification", "diagnose", "phenotype", "label", "分类", "诊断", "表型"],
        "required_concepts": ["participant_id", "visit_id", "age_at_visit", "cognitive_status_or_label"],
        "recommended_concepts": ["sex", "education", "apoe", "cdr_global", "cdr_sum", "cognitive_score", "uds_version"],
        "execution_family": "classification",
    },
    "trajectory_modeling": {
        "label": "Longitudinal trajectory modeling",
        "keywords": ["trajectory", "longitudinal", "slope", "mixed model", "轨迹", "纵向", "斜率"],
        "required_concepts": ["participant_id", "visit_id", "visit_date", "age_at_visit", "repeated_cognitive_measure"],
        "recommended_concepts": ["cognitive_status", "cdr_global", "cdr_sum", "uds_version", "death_dropout"],
        "execution_family": "trajectory",
    },
    "survival_progression": {
        "label": "Survival / progression analysis",
        "keywords": ["survival", "time-to-event", "censor", "hazard", "progression", "生存", "事件", "风险", "进展"],
        "required_concepts": ["participant_id", "time_zero", "event_definition", "event_or_censor_time"],
        "recommended_concepts": ["death_dropout", "visit_date", "age_at_visit", "sex", "education", "apoe", "uds_version"],
        "execution_family": "survival",
    },
    "biomarker_linked": {
        "label": "Biomarker/imaging-linked cohort",
        "keywords": ["biomarker", "csf", "pet", "mri", "amyloid", "tau", "imaging", "影像", "生物标志物"],
        "required_concepts": ["participant_id", "core_clinical_table", "biomarker_or_imaging_table", "measurement_date_or_visit_link"],
        "recommended_concepts": ["visit_date", "cognitive_status", "cognitive_score", "apoe", "uds_version"],
        "execution_family": "biomarker_linkage",
    },
    "causal_treatment_effect": {
        "label": "Causal inference / treatment effect",
        "keywords": ["causal", "treatment effect", "effect", "exposure", "washout", "comparator", "因果", "处理效应", "暴露", "药物"],
        "required_concepts": [
            "participant_id",
            "time_zero",
            "exposure_definition",
            "comparator_definition",
            "baseline_covariates",
            "outcome_after_time_zero",
            "medication_temporality_support",
        ],
        "recommended_concepts": ["washout", "lag", "grace_period", "death_dropout", "apoe", "uds_version"],
        "execution_family": "causal",
    },
    "representation_learning": {
        "label": "Representation learning / feature pretraining",
        "keywords": ["representation", "embedding", "pretrain", "self-supervised", "feature", "表征", "嵌入", "预训练", "特征"],
        "required_concepts": ["participant_id", "visit_id", "feature_time_anchor"],
        "recommended_concepts": ["visit_date", "age_at_visit", "sex", "education", "cognitive_status", "cognitive_score", "uds_version"],
        "execution_family": "representation_learning",
    },
}

COMMON_QUESTIONS = [
    ("time_zero", "Is time zero/index visit the first visit, the first eligible visit, or a specific measurement/event date?"),
    ("baseline_window", "What visits or time range belong to the baseline window, and which variables must be measured before time zero?"),
    ("minimum_followup", "Is the minimum follow-up requirement an eligibility criterion or an outcome-ascertainment requirement?"),
    ("missingness", "For APOE, cognitive scales, and diagnostic status, should missing values cause exclusion, be encoded as missing, or be handled through sensitivity analyses?"),
    ("uds_version", "Does the cohort mix UDS/form versions, and which fields may be structurally missing by version?"),
]

TASK_QUESTIONS = {
    "prediction_cognitive_decline": [
        ("baseline_dementia_free", "Should baseline dementia-free status use NACCUDSD, CDRGLOB, DEMENTED, or a composite rule?"),
        ("outcome_definition", "Should cognitive decline be defined by MMSE decline, MoCA decline, NACCUDSD conversion, CDR worsening, or a composite endpoint?"),
        ("outcome_window", "When does the outcome window start after time zero, and does it end at a visit number, calendar time, or fixed follow-up horizon?"),
        ("scale_harmonization", "How should MMSE/MoCA, UDS version, language, or center differences be handled?"),
        ("death_dropout", "Should death/dropout be treated as censoring, a competing event, or a missing-outcome mechanism?"),
    ],
    "classification": [
        ("label_definition", "Does the class label come from NACCUDSD, CDRGLOB, clinical diagnosis fields, or a user-defined phenotype?"),
        ("label_time", "Is the label a baseline label, visit-level label, or future-state label?"),
        ("feature_timing", "Which features may come from the same visit, and should post-label information be excluded?"),
    ],
    "trajectory_modeling": [
        ("trajectory_measure", "Should the trajectory measure be MMSE, MoCA, CDRSUM, ordinal NACCUDSD, or multiple measures?"),
        ("time_scale", "Should the time scale be visit number, age, calendar date, or years since baseline?"),
        ("irregular_visits", "How should irregular visit spacing and loss to follow-up be modeled or filtered?"),
    ],
    "survival_progression": [
        ("event_definition", "What is the event: dementia conversion, CDR worsening, death, or another progression endpoint?"),
        ("event_time", "How is event time defined: first event visit date, NACCDAYS, or visit date components?"),
        ("censoring", "How should death, loss to follow-up, and last contact be handled as censoring or competing events?"),
    ],
    "biomarker_linked": [
        ("module_selection", "Which modules are used: CSF, amyloid PET, tau PET, FDG PET, MRI, or multiple modules?"),
        ("linkage_rule", "How should biomarker/imaging measurements be aligned to clinical visits by date or visit linkage?"),
        ("temporal_order", "Is the biomarker a baseline predictor, outcome, or time-varying feature?"),
    ],
    "causal_treatment_effect": [
        ("exposure_definition", "Which medication/treatment defines exposure, and are NACC medication records sufficient to define start/current use?"),
        ("comparator", "Is the comparator non-use, an active comparator, or another treatment strategy?"),
        ("washout_lag_grace", "How are washout, lag, grace period, and exposure persistence defined?"),
        ("confounding", "Which covariates must be measured before exposure?"),
    ],
    "representation_learning": [
        ("learning_unit", "Is the learning unit participant-level, visit-level, or sequence-level?"),
        ("feature_scope", "Which feature groups enter pretraining, and should outcome/diagnosis fields be included?"),
        ("leakage_boundary", "If the representation will be used for prediction, which future information must be excluded?"),
    ],
}


def normalize(text: str) -> str:
    return text.lower()


def score_tasks(text: str) -> list[tuple[str, int]]:
    lowered = normalize(text)
    scores = []
    for task_id, spec in TASKS.items():
        score = 0
        for keyword in spec["keywords"]:
            if keyword.lower() in lowered:
                score += 2
        if "nacc" in lowered:
            score += 1
        scores.append((task_id, score))
    return sorted(scores, key=lambda item: item[1], reverse=True)


def infer_population(text: str) -> dict[str, str]:
    age_match = re.search(r"(\d{2,3})\s*(?:岁|years?|yo)?\s*(?:以上|older|over|\+)", text, re.IGNORECASE)
    return {
        "age_rule": f">= {age_match.group(1)}" if age_match else "unresolved",
        "baseline_dementia_free": "requested" if re.search(r"无\s*dementia|non[- ]?dement|dementia[- ]?free|baseline.*无", text, re.IGNORECASE) else "unresolved",
        "minimum_followup": ">= 2 visits requested" if re.search(r"至少\s*两次|two visits|2 visits|twice|两次访视", text, re.IGNORECASE) else "unresolved",
        "apoe_requirement": "required" if re.search(r"APOE|NACCNE4S|e4", text, re.IGNORECASE) else "unresolved",
    }


def infer_outcome(text: str, task_id: str) -> str:
    lowered = normalize(text)
    if "mmse" in lowered:
        return "MMSE-based cognitive decline candidate"
    if "moca" in lowered:
        return "MoCA-based cognitive decline candidate"
    if "conversion" in lowered or "转化" in lowered:
        return "diagnostic conversion candidate"
    if "cdr" in lowered:
        return "CDR worsening candidate"
    if task_id == "prediction_cognitive_decline":
        return "cognitive decline unresolved: choose MMSE, MoCA, diagnostic conversion, CDR worsening, or composite"
    return "task-specific outcome unresolved"


def yaml_list(values: list[str], indent: int) -> list[str]:
    prefix = " " * indent
    return [f"{prefix}- {value}" for value in values] if values else [f"{prefix}[]"]


def render_profile(text: str, task_id: str, alternatives: list[tuple[str, int]]) -> str:
    task = TASKS[task_id]
    population = infer_population(text)
    outcome = infer_outcome(text, task_id)
    required_concepts = list(task["required_concepts"])  # type: ignore[arg-type]
    recommended_concepts = list(task["recommended_concepts"])  # type: ignore[arg-type]
    if population["apoe_requirement"] == "required":
        if "apoe" not in required_concepts:
            required_concepts.append("apoe")
        recommended_concepts = [concept for concept in recommended_concepts if concept != "apoe"]
    lines = [
        'schema_version: "0.11-draft"',
        "dataset: nacc",
        "task_intent:",
        f"  primary_task_type: {task_id}",
        f"  label: \"{task['label']}\"",
        f"  execution_family: {task['execution_family']}",
        "  alternative_task_candidates:",
    ]
    for alt_id, score in alternatives[:4]:
        lines.append(f"    - task_type: {alt_id}")
        lines.append(f"      score: {score}")
        lines.append(f"      label: \"{TASKS[alt_id]['label']}\"")
    lines.extend(
        [
            "study_design_draft:",
            f"  original_user_intent: \"{text.replace('\"', '\\\"')}\"",
            "  target_population:",
            f"    age_rule: \"{population['age_rule']}\"",
            f"    baseline_dementia_free: \"{population['baseline_dementia_free']}\"",
            f"    minimum_followup: \"{population['minimum_followup']}\"",
            f"    apoe_requirement: \"{population['apoe_requirement']}\"",
            "  time_zero: unresolved",
            "  baseline_window: unresolved",
            f"  outcome: \"{outcome}\"",
            "required_nacc_concepts:",
        ]
    )
    lines.extend(yaml_list(required_concepts, 2))
    lines.append("recommended_nacc_concepts:")
    lines.extend(yaml_list(recommended_concepts, 2))
    lines.extend(
        [
            "readiness:",
            "  ready_for_mapping: true",
            "  ready_for_design_approval: false",
            "  ready_for_cohort_construction: false",
            "  blocking_reason: human design questions unresolved",
        ]
    )
    return "\n".join(lines) + "\n"


def render_questions(task_id: str) -> str:
    task = TASKS[task_id]
    questions = COMMON_QUESTIONS + TASK_QUESTIONS[task_id]
    lines = [
        "# NACC Task Intent Questions",
        "",
        f"Primary task: {task['label']}",
        "",
        "These questions must be answered before design approval and cohort construction.",
        "",
        "## Must-answer questions",
        "",
    ]
    for key, question in questions:
        lines.append(f"- [{key}] {question}")
    lines.extend(
        [
            "",
            "## Approval gate",
            "",
            "Do not run cohort construction until these questions are resolved and a human approves the design packet.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intent", required=True, help="Natural-language NACC cohort/research idea.")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    ranked = score_tasks(args.intent)
    primary = ranked[0][0] if ranked and ranked[0][1] > 0 else "prediction_cognitive_decline"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "task_profile.yaml").write_text(render_profile(args.intent, primary, ranked), encoding="utf-8")
    (args.output_dir / "task_questions.md").write_text(render_questions(primary), encoding="utf-8")
    print(f"Wrote NACC task intent outputs to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
