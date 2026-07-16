# Workflow Protocol

Use this protocol to move from a natural language research question to an audit memo.

## Step 1: Classify Mode

Choose Design Critic, Cohort Spec Builder, Dataset Adapter, Execution Builder, or Validation Reviewer.

## Step 2: Restate the Study

Restate the user's objective in study-design language. If possible, draft the target trial emulation framing.

## Step 3: Extract Design Objects

List what is known and unknown for:

- population
- treatment/exposure
- comparator
- time zero
- baseline window
- outcome
- follow-up
- censoring
- covariates
- data source

## Step 4: Critique Before Building

Identify red flags first. Prioritize issues that could invalidate the estimand or create biased effect estimates.

## Step 5: Gate on Human Decisions

Ask must-answer questions before final code if unresolved items affect validity. Offer assumptions only when the user asks for a draft.

## Step 6: Produce v0.1 Audit

For Design Critic mode, produce the required sections listed in `SKILL.md`. Do not bury critical questions in prose.

## Step 7: Recommend Next Step

Recommend one concrete next step:

- answer human confirmation questions
- convert to structured cohort spec
- map to a dataset adapter
- generate code and tests
- review existing code or attrition counts
