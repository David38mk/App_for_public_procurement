# Deep Extraction Handoff (Draft Citations)

## What was completed
Performed automated page-level extraction for the 3 high-risk manuals and generated draft citations tied to existing requirement IDs.

## New artifacts
- `compliance/extract_high_risk_context.py`
- `compliance/requirements_matrix_draft_with_citations.csv`
- `compliance/extraction/high_risk_extraction_snippets.md`

## Coverage summary
- Requirements processed: 9
- Requirements with draft page citations: 8
- Requirements without reliable keyword match: 1
  - `REQ-EPAZAR-2022-003` (error-handling/guidance)

## Important reliability note
Citations are **draft, machine-generated candidates**.
They are not legally approved references yet.
Each row still requires:
1. exact section/page confirmation by SME
2. legal interpretation approval

## Key extracted draft page candidates
- `REQ-ESJN-2021-001`: pages 41, 174, 6
- `REQ-ESJN-2021-002`: pages 4, 9, 11
- `REQ-ESJN-2021-003`: pages 25, 4, 13
- `REQ-ESJN-2021-004`: pages 69, 5, 8
- `REQ-ESJN-2021-005`: pages 33, 59, 66
- `REQ-ESJN-2021-006`: pages 32, 9, 19
- `REQ-EPAZAR-2022-001`: pages 7, 11, 13
- `REQ-EPAZAR-2022-002`: pages 17, 15, 18

## Next required actions (serious-app path)
1. SME review pass
- Confirm each draft citation maps to the intended functional requirement.
- Replace "Draft citation" text with exact section/page references.

2. Legal review pass
- Confirm normative interpretation and effective applicability.
- Move approval state from `pending_sme_legal` to formal workflow states.

3. Rule pack bootstrap
- Convert validated matrix rows into `compliance/rules/*.json` entries conforming to `rule_schema.json`.

4. Test binding
- Add deterministic acceptance tests for each approved requirement.
- Link tests back to matrix `test_case_id`.

## Risks and constraints
- Automated extraction may miss context where wording differs from keyword set.
- OCR-free extraction quality depends on PDF text layer quality.
- Do not treat these citations as production compliance truth without human approval.
