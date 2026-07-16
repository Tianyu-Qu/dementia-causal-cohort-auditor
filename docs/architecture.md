# Architecture

## Purpose

The Dementia Causal-Cohort Auditor turns a general-purpose agent into a dementia cohort design critic. It should challenge the design before producing code.

## Seven Layers

1. Trigger Layer: decide when this skill should activate.
2. Decision Layer: decide whether to critique, ask questions, build spec, map dataset variables, generate code, or validate existing results.
3. Core Knowledge Layer: disease SOP plus causal inference audit rules.
4. Adapter Layer: NACC, ADNI, UKB, EHR, and synthetic dataset mappings.
5. Workflow Layer: step-by-step interaction protocol from research question to audit memo.
6. Execution Layer: SQL/Python/cohort table/data quality report/tests.
7. Acceptance Layer: check whether the output is methodologically and computationally valid.

## Design Principle

The agent must behave like a mentor or opponent first and a code generator second. In treatment effect estimation, a runnable query can still encode an invalid estimand. The skill therefore gates code generation on time zero, exposure, outcome, baseline covariate timing, leakage, and attrition checks.

## Version Boundaries

v0.1 covers layers 1, 2, 3, 5, and 7 for design critique. It contains adapter drafts for NACC and synthetic data but does not yet implement full execution.

v0.2 adds a structured cohort spec contract. It converts the critique into a `cohort_definition.yaml` that records the estimand, time zero, windows, criteria, covariates, leakage checks, attrition plan, assumptions, unresolved items, and readiness.
