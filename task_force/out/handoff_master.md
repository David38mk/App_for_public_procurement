# Handoff Master

Generated: 2026-02-19 23:59:00

## Scope
Execution-ready handoff for document-handling features using manual-derived context under strict compliance controls.

## Inventory Summary
- Manuals detected: `13`
- High risk manuals: `3`
- Medium risk manuals: `5`
- Low risk manuals: `5`

## Priority Manuals (High Risk)
1. `Ð£Ð¿Ð°Ñ‚ÑÑ‚Ð²Ð°/Priracnik-za-koristenje-na-ESJN-za-Dogovorni-organi-nov2021.pdf`
2. `Ð£Ð¿Ð°Ñ‚ÑÑ‚Ð²Ð°/Priracnik-za-koristenje-na-ESJN-za-Ekonomski-operatori-nov2021.pdf`
3. `Ð£Ð¿Ð°Ñ‚ÑÑ‚Ð²Ð°/ÐšÐ¾Ñ€Ð¸ÑÐ½Ð¸Ñ‡ÐºÐ¾-ÑƒÐ¿Ð°Ñ‚ÑÑ‚Ð²Ð¾-Ð·Ð°-Ð•ÐºÐ¾Ð½Ð¾Ð¼ÑÐºÐ¸-Ð¾Ð¿ÐµÑ€Ð°Ñ‚Ð¾Ñ€Ð¸-ÐµÐŸÐ°Ð·Ð°Ñ€.pdf`

## Process Flows

### Flow A: Notice Search and Dossier Access
- Step A1: user enters keyword/filter criteria to locate notices.
  Source: `REQ-ESJN-2021-001`, citation draft pages `41, 174, 6`, confidence `medium`.
- Step A2: user opens dossier-level details from result list.
  Source: `REQ-ESJN-2021-001`, confidence `medium`.
- Step A3: system must preserve stable navigation state for subsequent actions.
  Source: inferred from same requirement, confidence `low`.

### Flow B: Document Retrieval and Download Resilience
- Step B1: user initiates retrieval from dossier context.
  Source: `REQ-ESJN-2021-002`, citation draft pages `4, 9, 11`, confidence `medium`.
- Step B2: system handles transient failures with clear error states and retry-safe behavior.
  Source: `REQ-ESJN-2021-002` and `REQ-EPAZAR-2022-003`, confidence `medium`.

### Flow C: Authentication and Role Gates
- Step C1: privileged actions require authenticated session and correct role.
  Source: `REQ-ESJN-2021-003`, citation draft pages `25, 4, 13`, confidence `medium`.
- Step C2: role-gated actions must be auditable.
  Source: `REQ-ESJN-2021-003` + `REQ-ESJN-2021-006`, confidence `medium`.

### Flow D: Submission Pack and Attachments
- Step D1: document builder validates required fields before generation.
  Source: `REQ-ESJN-2021-004`, citation draft pages `69, 5, 8`, confidence `medium`.
- Step D2: workspace pack enforces deterministic naming and completeness checklist.
  Source: `REQ-ESJN-2021-005`, citation draft pages `33, 59, 66`, confidence `medium`.
- Step D3: submission evidence metadata is captured and persisted.
  Source: `REQ-ESJN-2021-006`, citation draft pages `32, 9, 19`, confidence `medium`.

### Flow E: ESJN vs ePazar Routing
- Step E1: app must route users into process-specific path (ESJN vs ePazar).
  Source: `REQ-EPAZAR-2022-001`, citation draft pages `7, 11, 13`, confidence `medium`.
- Step E2: ePazar mandatory input set must be validated before action execution.
  Source: `REQ-EPAZAR-2022-002`, citation draft pages `17, 15, 18`, confidence `medium`.
- Step E3: corrective guidance requirement remains citation-incomplete.
  Source: `REQ-EPAZAR-2022-003`, draft citation pages `14, 20, 22`, confidence `low`.

## Template Mapping

| requirement_id | app_module | template/field focus | required attachments/checks | validation type | status |
|---|---|---|---|---|---|
| REQ-ESJN-2021-004 | doc_builder | core submission placeholders, bidder identity, procedure refs | pre-submit completeness pack | required/workflow_gate | draft |
| REQ-ESJN-2021-005 | workspace_pack | deterministic naming metadata | attachment checklist with missing-file detection | document_requirement | draft |
| REQ-ESJN-2021-006 | audit_log | evidence metadata fields (timestamp, dossier, operator) | evidence artifact persistence | audit | draft |
| REQ-ESJN-2021-002 | download | retrieval context fields (dossier id, source link) | retry log + error context capture | workflow_gate | draft |
| REQ-EPAZAR-2022-002 | validation_engine | mandatory ePazar input map | field map completeness before run | validation | draft |
| REQ-EPAZAR-2022-001 | workflow_router | process-mode selector fields | mode-specific step gating | workflow_gate | draft |
| REQ-EPAZAR-2022-003 | ux_errors | corrective guidance text map | draft citation candidate pages 14/20/22 | workflow_gate | draft_ready |

## Compliance and Freshness
- Rules present: `9` in `compliance/rules/`
- Traceability rows present: `9` in `compliance/traceability_index.csv`
- Compliance tests present: `14` in `tests/compliance/` (plus `__init__.py`)
- Current rule approval state target: all `draft` unless explicit SME+legal approval exists.
- Known blocker: none for implementation readiness; `REQ-EPAZAR-2022-003` now has draft citation candidate pages 14/20/22 and still requires SME/legal confirmation before approval.
- Linkage check: `requirement_id -> rule_id -> test_case_id` is complete (9/9).
- Rule state check: no accidental promotions (`non_draft_rules=0`).

Freshness priority for replacement/validation:
1. 2021 ESJN manuals (high risk stale)
2. 2022 ePazar operator manual (high risk stale)
3. 2023 ePazar authority + guidance docs (medium-high)

## Dependencies
1. Citation hardening for draft requirements (especially blocked requirement).
2. Stable template field dictionary for document generation.
3. Runtime rule-loader gate that ignores non-approved rules.
4. SME + legal review completion for any promotion path.

## Implementation Sequence (Next Sprint)
1. Done: preflight/checklist/retry/authorization platform (`REQ-ESJN-2021-002`, `REQ-ESJN-2021-003`, `REQ-ESJN-2021-004`, `REQ-ESJN-2021-005`).
2. Done: evidence metadata persistence (`REQ-ESJN-2021-006`).
3. Done: ESJN/ePazar router and mandatory input validation (`REQ-EPAZAR-2022-001`, `REQ-EPAZAR-2022-002`).
4. Done: search/dossier stabilization hardening (`REQ-ESJN-2021-001`).
5. Done (draft-only): corrective guidance implementation completed using draft citation candidate (`REQ-EPAZAR-2022-003`); approval remains blocked pending SME/legal confirmation.

## Current Delivery Status
- Done tickets: `TKT-PLAT-001`, `TKT-DOC-001`, `TKT-DOC-002`, `TKT-DOC-003`, `TKT-SEC-001`, `TKT-AUD-001`, `TKT-WFL-001`, `TKT-VAL-001`, `TKT-SRCH-001`, `TKT-UX-001`
- Ready tickets: none
- Blocked ticket: none (implementation); approval workflow still pending SME/legal for all draft rules

## Acceptance Criteria
- Every implemented behavior maps to a `requirement_id` with source citation text.
- `requirement_id -> rule_id -> test_case_id` chain remains complete for all rows.
- Production runtime path does not activate non-approved rules.
- Blocked requirements are tracked explicitly and excluded from activation scope.

## Open Questions (SME/Legal Required)
1. Which sections in 2021/2022 manuals remain legally valid in 2026 environment?
2. What exact source section/page confirms corrective guidance requirement (`REQ-EPAZAR-2022-003`)?
3. Are newer replacement manuals available that supersede high-risk stale sources?
4. Which template fields are legally mandatory by procedure type vs optional?



