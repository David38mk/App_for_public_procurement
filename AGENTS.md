# AGENTS.md

## Purpose
Project-level operating rules for all agents working in `C:\Users\rabota\Desktop\App for public procurements`.

## Compliance Posture
- Treat all procurement manuals, laws, and templates as compliance-sensitive source documents.
- Work in an audit-first mode: every requirement must be traceable to source and review status.
- Prefer conservative outcomes; unresolved ambiguity means "not approved."

## Mandatory Document Rules
- Do not delete or overwrite source documents.
- Do not change rule `approval_state` to `approved` without explicit SME + legal sign-off recorded in project artifacts.
- Do not convert inferred statements into production behavior without source citation and review.
- Keep the chain intact: `requirement_id -> source_file/source_section -> rule_id -> test_case_id`.
- When a citation is missing or weak, record a review gap and keep related rules/tests in draft-safe state.

## Output Standards
- Use UTF-8 for generated files.
- Prefer deterministic scripts over one-off manual edits.
- Keep IDs stable and machine-readable (`REQ-*`, `RULE-*`, `TC-*`).
- Ensure tests fail-safe for non-approved rules.

## Change Control
- For compliance artifacts, preserve history and traceability in every update.
- If a requirement source changes, mark impacted rules for re-review and re-test.
