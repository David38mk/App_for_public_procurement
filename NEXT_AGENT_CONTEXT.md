# Next Codex Agent Context

## Project
- Name: App for public procurements
- Location: `C:\Users\rabota\Desktop\App for public procurements`
- Date of handoff: February 19, 2026
- Current state: Document repository prepared for app implementation. No application codebase exists yet in this folder.

## User Objective
Build an app that helps users work with public procurement materials (law, guides, templates, instructions), with easy search, filtering, and access to latest relevant documents.

## What Has Already Been Done
1. Folder discovery and full file inventory completed.
2. Duplicate detection performed via SHA256.
3. Duplicate cleanup executed (with backup and log).
4. Filename normalization executed in two passes (Latin then Cyrillic, with backups and logs).
5. Freshness risk review performed using embedded PDF metadata (`CreationDate`/`ModDate`).
6. Replace-first shortlist generated for older high-risk docs.
7. Conversion workflow for legacy `.doc` files documented.

## Canonical Content Set (Current)
Main content files are now standardized and located under:
- `Закон за јавни набавки\`
- `модели на тендерска документација\`
- `Упатства\`

## Existing Review Artifacts (Read First)
- `review\01_dedup_rename_plan.md`
- `review\02_doc_to_docx_workflow.md`
- `review\03_key_pdf_content_freshness_review.md`
- `review\04_doc_conversion_commands.md`
- `review\05_replace_first_shortlist_2021_2023.md`
- `review\index.csv`
- `review\cleanup_actions.csv`
- `review\naming_standardization_actions.csv`
- `review\cyrillic_naming_standardization_actions.csv`
- `review\replace_first_shortlist_2021_2023.csv`

## High-Priority Content Risks to Address In App Logic
1. Likely outdated files (highest priority):
- `Упатства\Priracnik-za-koristenje-na-ESJN-za-Dogovorni-organi-nov2021.pdf`
- `Упатства\Priracnik-za-koristenje-na-ESJN-za-Ekonomski-operatori-nov2021.pdf`
- `Упатства\Корисничко-упатство-за-Економски-оператори-еПазар.pdf`
2. Medium-high staleness:
- 2023 docs listed in `review\05_replace_first_shortlist_2021_2023.md`
3. Legacy `.doc` still present:
- `Упатства\Zaednicki-poimnik-za-JN.doc`
- `модели на тендерска документација\Отворена постапка\Model-Otvorena-postapka-usoglasena-so-izmeni-na-ZJN-14-25-1.doc`
- `модели на тендерска документација\Поедноставена отворена постапка\POP-Izmena-ZJN-14-25-1.doc`

## Recommended MVP for the App
1. Document library screen:
- List all docs from local index (`review\index.csv` initially).
- Show title, type, category, year tag, and freshness status.
2. Search and filters:
- Full-text search on title/metadata.
- Filters: category, type (`pdf/doc/docx`), year, risk level.
3. Freshness badges:
- `Current`, `Review`, `Likely Outdated` based on rules from review reports.
4. Detail view:
- File metadata and quick actions (open file, reveal folder).
5. Admin/update panel:
- Mark document status manually.
- Replace outdated files and refresh index.

## Suggested Data Model
- `id`
- `relative_path`
- `display_name`
- `category`
- `doc_type`
- `year_tag`
- `embedded_creation_date` (if available)
- `freshness_status`
- `priority`
- `notes`

## Suggested Immediate Next Tasks for Agent
1. Create project scaffold (stack per user preference; if unspecified, ask before proceeding).
2. Import `review\index.csv` as initial dataset.
3. Add deterministic categorization from folder path.
4. Implement list/search/filter UI.
5. Encode freshness rules from `review\03_key_pdf_content_freshness_review.md` and shortlist files.
6. Add a maintenance command to regenerate index and risk flags after file updates.

## Important Constraints
- Keep file operations reversible (backup + log every rename/delete).
- Do not delete source materials without explicit user confirmation.
- Preserve Macedonian/Cyrillic filenames and paths.

## Notes for Cleanup Follow-up
- Consider renaming `Скрејпер-+-симнувач-за-e-nabavki.gov.mk-(PublicAccess).docx` to a cleaner form later, e.g. replace `-+-` with `-и-`.

## Definition of Done (for initial app version)
- User can browse all documents.
- User can search and filter quickly.
- App clearly marks stale/high-risk documents.
- App links each document entry to the real local file.
- Index refresh process is documented and repeatable.
