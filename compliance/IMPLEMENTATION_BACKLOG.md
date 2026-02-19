# Compliance Implementation Backlog

Updated: 2026-02-19 (UTC) - agent execution refresh

Scope: Document handling backlog derived only from draft, traceable requirements.

## Priority 1 (Blocking)
- `REQ-ESJN-2021-004` (TC-REQ-004): Document builder must enforce required fields before generating final submission pack. [module=doc_builder, approval_state=draft, implementation=done]
- `REQ-ESJN-2021-005` (TC-REQ-005): App must produce a dossier workspace with deterministic file naming and completeness checks. [module=workspace_pack, approval_state=draft, implementation=done]
- `REQ-ESJN-2021-002` (TC-REQ-002): App must support document retrieval from dossier with clear error states and retries. [module=download, approval_state=draft, implementation=done]

## Priority 2 (High Risk Controls)
- `REQ-ESJN-2021-003` (TC-REQ-003): Enforce authenticated role gates and audit logs in document operations. [implementation=done]
- `REQ-ESJN-2021-006` (TC-REQ-006): Persist submission evidence metadata for audit traceability. [implementation=done]

## Priority 3 (Workflow Segmentation and UX)
- `REQ-EPAZAR-2022-001` (TC-REQ-007): Separate ePazar vs ESJN flows in document handling UX. [implementation=done]
- `REQ-EPAZAR-2022-002` (TC-REQ-008): Validate ePazar mandatory inputs before document actions. [implementation=done]
- `REQ-EPAZAR-2022-003` (TC-REQ-009): Add corrective guidance and retry-safe state handling. [implementation=done_draft_citation]

## Current Ticket State
- Done: `TKT-PLAT-001`, `TKT-DOC-001`, `TKT-DOC-002`, `TKT-DOC-003`, `TKT-SEC-001`, `TKT-AUD-001`, `TKT-WFL-001`, `TKT-VAL-001`, `TKT-SRCH-001`, `TKT-UX-001`
- Ready next: none
- Blocked: none; implementation complete, SME/legal confirmation still required before any approval-state promotion

## Guardrails
- Do not activate runtime policy loading for any rule unless `approval_state=approved`.
- Every backlog item must retain traceability to requirement ID, source citation, rule ID, and test case ID.
- Any source-section update requires SME+legal re-review and regression tests.


