# Approval Workflow (Serious Procurement App)

## Principle
No rule is production-active unless it is traceable to source and approved by domain SME + legal reviewer.

## States
- `draft`
- `pending_sme`
- `pending_legal`
- `approved`
- `deprecated`

## Gate Criteria
1. Source Traceability Gate
- Requirement/rule references exact source file and section.
- If source page is unknown, rule cannot move past `draft`.

2. SME Gate
- Procurement SME validates interpretation and workflow correctness.
- State change: `pending_sme` -> `pending_legal`.

3. Legal Gate
- Legal reviewer validates compliance interpretation and effective dates.
- State change: `pending_legal` -> `approved`.

4. Test Gate
- At least one passing test case linked in matrix (`test_case_id`).
- Required for deployment of `approved` rules.

## Required Artifacts per Rule
- Rule entry (schema-compliant JSON)
- Matrix row (`requirements_matrix.csv`)
- Linked test case and expected result
- Reviewer identity and approval timestamp

## Release Policy
- Only `approved` rules are loaded in production policy pack.
- `draft`, `pending_*` rules are ignored at runtime.
- `deprecated` rules remain for audit history but are inactive.

## Change Control
- Any manual update triggers:
1. Risk reassessment
2. Matrix delta review
3. Re-approval for impacted rules
4. Regression test run
