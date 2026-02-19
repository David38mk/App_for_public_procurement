# DOC to DOCX Conversion Workflow

## Why
- `.doc` is legacy binary format with weaker change tracking and interoperability.
- `.docx` is safer for long-term maintenance and automation.

## Files to Convert
- `Упатства\Zaednicki_poimnik_za_JN.doc`
- `модели на тендерска документација\Отворена постапка\Model_Otvorena-postapka_usoglasena-so-izmeni-na-ZJN-14-25-1.doc`
- `модели на тендерска документација\Поедноставена отворена постапка\POP-Izmena-ZJN-14_25-1.doc`

## Recommended Process
1. Create backups: copy each `.doc` to `review\doc_backup\`.
2. Convert to `.docx` using Microsoft Word or LibreOffice.
3. Keep filenames stable, only extension change.
4. Open converted file and verify:
- page count
- table formatting
- header/footer
- signatures/stamps placeholders
5. Run side-by-side visual check against source `.doc`.
6. Mark old `.doc` files as archived, do not delete immediately.

## Acceptance Checklist
- Converted file opens without compatibility mode warning.
- No missing paragraphs or broken tables.
- Tracked changes metadata is preserved or intentionally reset.
- Final file saved in UTF-8-safe naming convention.

## Suggested Naming
- Keep original base filename, change `.doc` -> `.docx`.
- If edited for law updates, append version tag, example: `_rev-2026-02`.

## Rollback
- If any formatting mismatch exists, keep `.doc` active and log conversion defect in `review\conversion_issues.md`.
