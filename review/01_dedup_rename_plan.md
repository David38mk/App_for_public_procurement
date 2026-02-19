# Dedup and Rename Plan

## Scope
- Root: `C:\Users\rabota\Desktop\App for public procurements`
- Files reviewed: 24
- Types: 15 PDF, 6 DOCX, 3 DOC

## High Priority Deduplication

### Exact duplicates (same SHA256)
- Keep: `Упатства\Upatstvo-za-popolnuvanje-na-finansiskiot-obrazec.pdf`
- Remove/archive: `Упатства\Upatstvo za popolnuvanje na finansiskiot obrazec.pdf`
- Remove/archive: `Упатства\Upatstvo-za-popolnuvanje-na-finansiskiot-obrazec (1).pdf`

Rationale: all three files are byte-identical.

## Proposed Naming Standard
- Use one style per folder:
- Macedonian names in Cyrillic for user-facing material.
- ASCII transliteration only when required by external systems.
- No duplicate suffixes like `(1)`.
- Use `YYYY` or `YYYY-MM` in names when version/date is known.
- Replace multiple spaces with single space.

## Proposed Rename Actions (no changes applied yet)
- `Скрејпер + симнувач за e-nabavki.gov.mk (PublicAccess) (1).docx` -> `Скрејпер + симнувач за e-nabavki.gov.mk (PublicAccess).docx`
- `Упатства\Priracnik  za koristenje na ESJN za Ekonomski operatori_nov2021.pdf` -> `Упатства\Priracnik za koristenje na ESJN za Ekonomski operatori_nov2021.pdf`
- `Упатства\Upatstvo za digitalno potpisuvanje_feb.2026.pdf` -> `Упатства\Upatstvo-za-digitalno-potpisuvanje_feb-2026.pdf`
- `Упатства\Upatstvo-Podnesuvanje ponuda na ESJN.pdf` -> `Упатства\Upatstvo-podnesuvanje-ponuda-na-ESJN.pdf`

## Safe Execution Order
1. Copy duplicate candidates to `review\archive_candidates\`.
2. Remove duplicate copies after manual spot-check.
3. Rename files one by one and validate links/usages.
4. Produce final index file with canonical names.

## Optional Next Step
- Create `index.csv` with columns: `canonical_name`, `current_path`, `document_type`, `year_tag`, `status`.
