# Implementation Tickets

Generated: 2026-02-19 22:55:00
Source: `task_force/out/handoff_master.md`

## P0

### TKT-PLAT-001
- Title: Runtime compliance gate approved-rules-only policy loading
- Owner: Engineering+Compliance
- Status: done (implemented 2026-02-19)
- Requirements: `REQ-ESJN-2021-001..006`, `REQ-EPAZAR-2022-001..003`
- Acceptance:
1. Runtime loader reads only rules where `approval_state=approved`.
2. Draft/pending rules remain inactive even if files exist.
3. Integration test proves gating behavior.

### TKT-DOC-001
- Title: Document builder preflight required-field validation
- Owner: Engineering
- Status: done (implemented 2026-02-19)
- Requirement: `REQ-ESJN-2021-004`
- Depends on: `TKT-PLAT-001`
- Acceptance:
1. Missing required placeholders block document generation.
2. Validation output is deterministic and actionable.
3. Linked compliance test `TC-REQ-004` is green only when rule is approved.

### TKT-DOC-002
- Title: Dossier workspace completeness and deterministic naming
- Owner: Engineering
- Status: done (implemented 2026-02-19)
- Requirement: `REQ-ESJN-2021-005`
- Depends on: `TKT-PLAT-001`
- Acceptance:
1. Workspace naming is deterministic.
2. Attachment checklist blocks incomplete packs.
3. Linked compliance test `TC-REQ-005` preserved.

### TKT-DOC-003
- Title: Document retrieval retry-safe error contract
- Owner: Engineering
- Status: done (implemented 2026-02-19)
- Requirement: `REQ-ESJN-2021-002`
- Depends on: `TKT-PLAT-001`
- Acceptance:
1. Retrieval errors map to explicit, user-facing states.
2. Retry flow keeps operation idempotent and safe.
3. Linked compliance test `TC-REQ-002` preserved.

## P1

### TKT-SEC-001
- Title: Role-gated actions for document operations
- Owner: Security+Engineering
- Status: done (implemented 2026-02-19)
- Requirement: `REQ-ESJN-2021-003`
- Depends on: `TKT-PLAT-001`
- Acceptance:
1. Unauthorized actions are blocked.
2. Authorization checks are auditable.
3. Linked compliance test `TC-REQ-003` preserved.

### TKT-AUD-001
- Title: Submission evidence metadata persistence
- Owner: Engineering+Compliance
- Status: done (implemented 2026-02-19)
- Requirement: `REQ-ESJN-2021-006`
- Depends on: `TKT-PLAT-001`
- Acceptance:
1. Evidence metadata persists per submission action.
2. Audit log fields are queryable and complete.
3. Linked compliance test `TC-REQ-006` preserved.

### TKT-WFL-001
- Title: ESJN and ePazar workflow router
- Owner: Product+Engineering
- Status: done (implemented 2026-02-19)
- Requirement: `REQ-EPAZAR-2022-001`
- Depends on: `TKT-PLAT-001`
- Acceptance:
1. System routes into ESJN or ePazar mode explicitly.
2. Mode-specific validations are applied consistently.
3. Linked compliance test `TC-REQ-007` preserved.

### TKT-VAL-001
- Title: ePazar mandatory input-set validation
- Owner: Engineering
- Status: done (implemented 2026-02-19)
- Requirement: `REQ-EPAZAR-2022-002`
- Depends on: `TKT-WFL-001`, `TKT-PLAT-001`
- Acceptance:
1. Incomplete mandatory input set blocks action execution.
2. Missing-field errors are deterministic and field-specific.
3. Linked compliance test `TC-REQ-008` preserved.

## P2

### TKT-SRCH-001
- Status: done (implemented 2026-02-19)
- Title: Notice search and dossier opening stabilization
- Owner: Engineering
- Requirement: `REQ-ESJN-2021-001`
- Depends on: `TKT-PLAT-001`
- Acceptance:
1. Search and dossier opening preserve navigation context.
2. Pagination/filtering remains stable under retries.
3. Linked compliance test `TC-REQ-001` preserved.

### TKT-UX-001 (Done)
- Status: done (implemented 2026-02-19)
- Title: Corrective guidance and retry-safe UX for failed steps
- Owner: UX+Engineering
- Requirement: `REQ-EPAZAR-2022-003`
- Depends on: `TKT-DOC-003`, `TKT-WFL-001`
- Blocker: none (draft citation candidate added; SME/legal confirmation still required for approval).
- Acceptance (post-unblock):
1. Corrective guidance appears for each failed step class.
2. User can retry without state corruption.
3. Linked compliance test `TC-REQ-009` preserved.

## Execution Order
1. `TKT-PLAT-001`
2. `TKT-DOC-001`, `TKT-DOC-002`, `TKT-DOC-003`
3. `TKT-SEC-001`, `TKT-AUD-001`
4. `TKT-WFL-001`, `TKT-VAL-001`
5. `TKT-SRCH-001`
6. `TKT-UX-001`

## Notes
- All requirement-linked tickets remain draft-governed until SME+legal approval updates rule states.
- Ticket statuses: `done` means implemented; approval-state promotion remains gated by SME/legal workflow.



