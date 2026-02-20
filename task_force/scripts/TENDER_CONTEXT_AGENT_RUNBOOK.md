# Tender Context Agent Runbook

## Purpose
Extract draft context from downloaded tender documentation and surface likely `Услови` obligations for upload preparation.

## Script
- `task_force/scripts/extract_tender_context.py`

## Run
```powershell
cd "C:\Users\rabota\Desktop\App for public procurements"
C:\Users\rabota\AppData\Local\Programs\Python\Python314\python.exe task_force\scripts\extract_tender_context.py --input-dir downloads --out-dir task_force\out\tender_context --max-files 10
```

## Outputs
- `task_force/out/tender_context/tender_context_<timestamp>.json`
- `task_force/out/tender_context/tender_context_<timestamp>.md`
- `task_force/out/tender_context/upload_hints_<timestamp>.csv`

## How to Use the Output
1. Open `upload_hints_*.csv`.
2. Map each `tag` candidate to an actual upload slot on `#/submit-bid/<procurement_id>`.
3. Treat all extracted hints as draft until confirmed against source text (`Услови`) by human review.

## Notes
- PDF extraction uses `pypdf` when available.
- DOCX extraction is done from OOXML text nodes.
- Script excludes `downloads/debug` artifacts automatically.
