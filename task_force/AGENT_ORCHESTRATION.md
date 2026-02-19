# Multi Task Force Orchestration

## Mission
Build reliable context from all user manuals and continuously produce handoff documents for the document-handling feature stream.

## Agents
1. Manual Ingestion Agent
- Collects source manuals, metadata, and machine-extracted snippets.
- Produces normalized inventory and per-manual context packets.

2. Process Mapping Agent
- Extracts user workflows from manuals (search, bid submission, signing, downloads, forms).
- Produces step maps and decision points.

3. Template Intelligence Agent
- Maps manual requirements to document templates and required fields.
- Produces placeholder/field matrix for document generation.

4. Compliance & Freshness Agent
- Scores staleness and legal/process risk.
- Flags manuals requiring updates first.

5. Handoff Synthesis Agent
- Converts outputs from all agents into sprint-ready handoff docs.
- Maintains master handoff with priorities, dependencies, and acceptance criteria.

## Work Protocol
- Every agent updates handoff artifacts as it completes a batch.
- Every artifact includes: source paths, confidence level, open questions, next actions.
- No destructive file operations.

## Output Artifacts
- `task_force/out/manual_inventory.csv`
- `task_force/out/manual_context_packets.md`
- `task_force/out/handoff_master.md`

## Runbook
1. Run context build script:
`python task_force/scripts/build_manual_context.py`
2. Manual Ingestion Agent reviews/edits `manual_context_packets.md`.
3. Process Mapping + Template Intelligence update handoff sections.
4. Compliance Agent updates risk sections.
5. Handoff Agent finalizes `handoff_master.md`.
