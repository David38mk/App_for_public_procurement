# Agent: Manual Ingestion

## Inputs
- All manuals from project folders.

## Steps
1. Scan files and classify manuals.
2. Capture metadata (path, type, size, dates).
3. Add quick context tags from file names.
4. Emit inventory + context packets.

## Outputs
- `task_force/out/manual_inventory.csv`
- `task_force/out/manual_context_packets.md`
