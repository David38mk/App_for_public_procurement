# Agent Execution Plan (Manual-Driven)

Updated: 2026-02-19 (UTC)
Scope: Retrieve context from user manuals and execute a compliance-first plan for document-handling features.

## Retrieved Manual Context Baseline

### Inventory snapshot
- Total manuals: 13 (`task_force/out/manual_inventory.csv`)
- High risk: 3
- Medium risk: 5
- Low risk: 5

### High-risk manuals (priority sources)
1. `Упатства/Priracnik-za-koristenje-na-ESJN-za-Dogovorni-organi-nov2021.pdf` (embedded date: 2021-01-08, risk: High)
2. `Упатства/Priracnik-za-koristenje-na-ESJN-za-Ekonomski-operatori-nov2021.pdf` (embedded date: 2021-01-18, risk: High)
3. `Упатства/Корисничко-упатство-за-Економски-оператори-еПазар.pdf` (embedded date: 2022-02-21, risk: High)

### Draft extracted requirement context
- Draft requirements with citations: 9 (`compliance/requirements_matrix_draft_with_citations.csv`)
- Draft extraction snippets exist for high-risk set (`compliance/extraction/high_risk_extraction_snippets.md`)
- One requirement lacks reliable keyword-match citation and must remain blocked:
`REQ-EPAZAR-2022-003`

### Compliance execution constraints
- No rule may be moved to `approved` without explicit SME + legal sign-off.
- Full chain must be preserved: `requirement_id -> source_file/source_section -> rule_id -> test_case_id`.
- Any citation ambiguity keeps rule state at `draft`.

## Agent Work Plan

## Phase 1: Manual Context Hardening
Owner agents: `Manual Ingestion Agent`, `Process Mapping Agent`

Tasks:
1. Complete context summaries for all 13 manuals in `task_force/out/manual_context_packets.md`.
2. Produce workflow maps from manuals covering:
- notice search
- dossier/document retrieval
- role/login gates
- submission and attachment flows
- digital signature and evidence capture
3. For each workflow step, add:
- source manual path
- exact section/page (or `citation_missing`)
- confidence (`high|medium|low`)

Deliverables:
- Updated `task_force/out/manual_context_packets.md`
- Updated `task_force/out/handoff_master.md` with `Process Flows` section

Done gate:
- All 13 manuals have non-placeholder context summaries.
- Every high-risk workflow requirement has at least one traceable source citation.

## Phase 2: Requirement and Rule Stabilization
Owner agents: `Compliance & Freshness Agent`, `Handoff Synthesis Agent`

Tasks:
1. Reconcile context findings into `compliance/requirements_matrix_draft_with_citations.csv`.
2. Mark rows with unresolved citations as review blockers.
3. Regenerate/align rule files in `compliance/rules/*.json`:
- `approval_state` stays `draft` until external approval
- `source_section` reflects latest citation text
- `test_case_id` linkage must remain stable
4. Update `compliance/traceability_index.csv` for all requirement rows.

Deliverables:
- Updated requirement matrix
- Updated rule pack
- Updated traceability index

Done gate:
- 100% of requirements appear in traceability index.
- No mismatch between requirement IDs, rule IDs, and test IDs.

## Phase 3: Template and Validation Mapping
Owner agent: `Template Intelligence Agent`

Tasks:
1. Map manual obligations into template/data requirements for document generation.
2. Produce matrix from manual requirement to:
- placeholder fields
- required attachments
- validation rule type
- blocking error messages
3. Identify gaps where app input model cannot satisfy required manual fields.

Deliverables:
- Update `task_force/out/handoff_master.md` with `Template Mapping`
- Backlog updates in `compliance/IMPLEMENTATION_BACKLOG.md`

Done gate:
- Each document-handling requirement maps to concrete app fields/checks.
- All blocking gaps are explicitly listed as implementation tasks.

## Phase 4: Test and Runtime Gating
Owner agents: `Compliance & Freshness Agent`, `Handoff Synthesis Agent`

Tasks:
1. Keep placeholder tests in `tests/compliance/` synchronized with matrix/rules.
2. Ensure fail-safe behavior remains enforced:
- tests assert `approval_state == approved`
- draft/pending rules are non-runnable in production policy loading
3. Add one integration gate test for runtime policy filtering (approved-only load).

Deliverables:
- Updated `tests/compliance/`
- Runtime policy loading gate noted in handoff

Done gate:
- Test suite fails for any non-approved rule attempting runtime activation.

## Phase 5: Sprint Handoff Package
Owner agent: `Handoff Synthesis Agent`

Tasks:
1. Finalize `task_force/out/handoff_master.md` with:
- priorities
- dependencies
- open questions
- acceptance criteria
2. Provide implementation sequence grouped by risk and coupling.

Deliverables:
- Sprint-ready `task_force/out/handoff_master.md`

Done gate:
- Engineering can start implementation without guessing requirement intent.
- Compliance blockers are explicit and actionable.

## Execution Order and Dependencies
1. `Manual Ingestion Agent` + `Process Mapping Agent` (Phase 1)
2. `Compliance & Freshness Agent` (Phase 2, depends on Phase 1 citations)
3. `Template Intelligence Agent` (Phase 3, depends on stabilized requirements)
4. `Compliance & Freshness Agent` (Phase 4 tests/gates)
5. `Handoff Synthesis Agent` (Phase 5 final packaging)

## Assignment Matrix
- `Manual Ingestion Agent`: completeness of manual context packets
- `Process Mapping Agent`: workflow extraction and citation tagging
- `Template Intelligence Agent`: field/attachment/validation mapping
- `Compliance & Freshness Agent`: risk posture, traceability integrity, rule/test gating
- `Handoff Synthesis Agent`: final master handoff and sprint-ready sequencing

## Immediate Next Run (first 24h)
1. Fill all placeholder context summaries in `task_force/out/manual_context_packets.md`.
2. Resolve missing citation for `REQ-EPAZAR-2022-003` or mark as explicit blocker.
3. Update `task_force/out/handoff_master.md` with Process Flows + Template Mapping sections.
4. Re-emit `compliance/traceability_index.csv` and verify 9/9 rule-test links.
