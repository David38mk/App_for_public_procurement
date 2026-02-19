You are the next Codex agent continuing work in:
`C:\Users\rabota\Desktop\App for public procurements`

Mission:
Continue the compliance-first implementation for the document-handling module of a serious public procurement app.

Context you must read first (in this order):
1. `compliance/DEEP_EXTRACTION_HANDOFF.md`
2. `compliance/COMPLIANCE_HANDOFF_NEXT_AGENT.md`
3. `compliance/requirements_matrix_draft_with_citations.csv`
4. `compliance/approval_workflow.md`
5. `compliance/rule_schema.json`
6. `task_force/out/handoff_master.md`
7. `app/main.py`
8. `app/services/template_builder.py`
9. `app/services/tender_search.py`

Non-negotiable constraints:
- Treat manual-derived requirements as compliance-sensitive.
- Do NOT mark any rule production-approved without explicit SME+legal validation.
- Keep full traceability: requirement -> source citation -> rule -> test.
- Do not delete source documents.
- Assume this is a high-accountability, audit-exposed system: prefer conservative behavior over convenience.
- Never present inferred requirement text as legal truth; explicitly label inferred/draft content.
- Any missing citation or ambiguous wording must block promotion beyond `draft`.
- Preserve exact source filenames/paths in traceability artifacts (no silent normalization).
- If a requirement is not tied to a concrete source reference, create/update it as a review gap, not as an implementation fact.

Primary objectives for this session:
1. Build SME review pack:
- Create `compliance/review/sme_review_checklist.csv`
- One row per requirement_id from `requirements_matrix_draft_with_citations.csv`
- Columns: requirement_id, source_file, draft_source_section, reviewer_decision, reviewer_comment, reviewed_at

2. Build legal review pack:
- Create `compliance/review/legal_review_checklist.csv`
- Columns: requirement_id, legal_decision, legal_comment, effective_from_confirmed, reviewed_at

3. Bootstrap draft rules:
- Create `compliance/rules/` folder.
- Create JSON rule files for each requirement using `rule_schema.json`.
- Set `approval_state` = `draft`.
- Include source references from draft citation matrix.

4. Build traceability index:
- Create `compliance/traceability_index.csv`
- Columns: requirement_id, rule_id, source_file, source_section, app_module, test_case_id, approval_state

5. Add test scaffolding:
- Create `tests/compliance/` with placeholder tests for each requirement test_case_id.
- Tests should fail-safe if rule approval_state != approved.

6. Prepare implementation backlog update:
- Update or create `compliance/IMPLEMENTATION_BACKLOG.md`
- Include prioritized items for document handling, only based on draft+traceable requirements.

Quality bar:
- Prefer deterministic scripts and machine-readable outputs.
- Ensure all generated files use UTF-8.
- Run syntax checks for touched Python files.
- Keep outputs review-ready for compliance audit (clear timestamps, stable IDs, no ad-hoc formats).
- Fail closed on uncertainty: when uncertain, keep `approval_state` at `draft` and record blocker in backlog/review artifacts.

Deliverable summary expected at end:
- List all created/updated files.
- Risks/open questions requiring SME/legal input.
- Exact next step to move from draft to approved rules.
