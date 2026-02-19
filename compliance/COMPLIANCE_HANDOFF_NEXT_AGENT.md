# Compliance Handoff (Next Agent)

## Scope Completed
Created compliance foundation for serious procurement app development with traceability-first approach.

## Files Created
- `compliance/requirements_matrix.csv`
- `compliance/rule_schema.json`
- `compliance/approval_workflow.md`
- Existing context assets used:
- `task_force/out/manual_inventory.csv`
- `task_force/out/manual_context_packets.md`
- `task_force/out/handoff_master.md`

## What is Verified vs Inferred
### Verified
- High-risk manuals identified from inventory/date signals:
1. `Упатства/Priracnik-za-koristenje-na-ESJN-za-Dogovorni-organi-nov2021.pdf`
2. `Упатства/Priracnik-za-koristenje-na-ESJN-za-Ekonomski-operatori-nov2021.pdf`
3. `Упатства/Корисничко-упатство-за-Економски-оператори-еПазар.pdf`
- Compliance artifacts and workflow structure exist and are runnable/editable.

### Inferred (Requires SME/Legal Validation)
- Initial requirement texts in `requirements_matrix.csv` are drafted from manual names/workflow expectations, not full section-by-section legal extraction.
- Source section strings are placeholders and must be replaced with exact section/page citations.

## Current Matrix Status
- Draft requirements added: 9
- Approval state for all: `pending_sme_legal`
- No rule is production-approved.

## Immediate Next Steps (Required)
1. Manual deep extraction pass
- For each high-risk manual, extract exact section/page references.
- Replace placeholder `source_section` with precise citations.

2. Requirement hardening
- Convert inferred statements into source-backed normative requirements.
- Split compound requirements into atomic ones.

3. Rule pack bootstrap
- Create `compliance/rules/` with JSON rule files conforming to `rule_schema.json`.
- Mark all as `draft` until review complete.

4. Test binding
- Create test IDs and acceptance tests for each matrix row.
- Link tests in matrix `test_case_id`.

5. Approval workflow execution
- Run SME review then legal review.
- Move only approved rules to runtime-active policy pack.

## Integration Guidance for Document Handling Module
- Document generation should consume only approved requirements/rules.
- Add validation checkpoints:
- required placeholders present
- mandatory attachments checklist complete
- role/workflow gates enforced
- audit metadata persisted

## Risk Note
This app is compliance-sensitive. Do not ship behavior derived only from AI inference or filename heuristics.
