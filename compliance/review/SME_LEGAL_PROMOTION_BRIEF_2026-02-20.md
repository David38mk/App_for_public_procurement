# SME + Legal Promotion Brief (Wave 1)

Date: 2026-02-20
Scope: Prepare rule-promotion workflow artifacts for first document-handling wave.

## Wave 1 Candidates
- `REQ-ESJN-2021-002` -> `RULE-ESJN-2021-002` (`download`, `TC-REQ-002`)
- `REQ-ESJN-2021-004` -> `RULE-ESJN-2021-004` (`doc_builder`, `TC-REQ-004`)
- `REQ-ESJN-2021-005` -> `RULE-ESJN-2021-005` (`workspace_pack`, `TC-REQ-005`)

## Current State
- All candidate rules remain `draft`.
- Runtime gate remains fail-closed for non-approved rules.
- Implementation and tests exist for all three candidate modules.

## Required SME Inputs (Before State Can Move Past `draft`)
1. Confirm exact normative section/page references in source manuals for each requirement.
2. Confirm interpretation-to-behavior mapping:
- `REQ-ESJN-2021-002`: retrieval/retry behavior and error-state obligations.
- `REQ-ESJN-2021-004`: mandatory preflight fields for generation.
- `REQ-ESJN-2021-005`: required attachment/completeness obligations.
3. Record `reviewer_decision`, `reviewer_comment`, and `reviewed_at` in:
- `compliance/review/sme_review_checklist.csv`

## Required Legal Inputs (After SME Confirmation)
1. Confirm legal interpretation of SME-validated text.
2. Confirm effective dates and applicability.
3. Record `legal_decision`, `legal_comment`, `effective_from_confirmed`, `reviewed_at` in:
- `compliance/review/legal_review_checklist.csv`

## Promotion Rule
- Do not set any rule to `approved` without explicit SME and legal sign-off recorded in review files.
- If any citation remains ambiguous or draft-only, keep state at `draft` and log blocker.
