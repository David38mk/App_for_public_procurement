# Next Agent Tasklist

## 1. Setup
- Confirm app stack with user (if not specified).
- Create new project in `C:\Users\rabota\Desktop\App for public procurements\app`.

## 2. Data Ingestion
- Load `review\index.csv` as initial document dataset.
- Map fields: `relative_path`, `canonical_name`, `document_type`, `year_tag`.
- Derive category from folder path.

## 3. Core UI (MVP)
- Build document list page.
- Add search by filename/title.
- Add filters: category, type, year, freshness status.
- Add detail panel with file path + open action.

## 4. Freshness Logic
- Apply risk/freshness rules from:
- `review\03_key_pdf_content_freshness_review.md`
- `review\05_replace_first_shortlist_2021_2023.md`
- Mark documents as: `Current`, `Review`, `Likely Outdated`.

## 5. Priority Flags
- Highlight these first:
- `Упатства\Priracnik-za-koristenje-na-ESJN-za-Dogovorni-organi-nov2021.pdf`
- `Упатства\Priracnik-za-koristenje-na-ESJN-za-Ekonomski-operatori-nov2021.pdf`
- `Упатства\Корисничко-упатство-за-Економски-оператори-еПазар.pdf`

## 6. Maintenance Utilities
- Add command/script to regenerate index from filesystem.
- Add command/script to recompute freshness flags.
- Log all file rename/delete operations to `review\` CSV.

## 7. Legacy Conversion Follow-up
- Plan conversion of remaining `.doc` files using:
- `review\04_doc_conversion_commands.md`
- Keep backups before conversion.

## 8. Deliverables for User
- Working MVP app with list/search/filter.
- Freshness indicators visible in UI.
- README with run instructions + refresh workflow.

## 9. Guardrails
- Do not delete source docs without explicit user approval.
- Keep operations reversible (backup + action log).
- Preserve Macedonian/Cyrillic filenames and paths.
