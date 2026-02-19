# Key PDF Content Freshness Review

## Review Date
- February 19, 2026

## Method
- Used PDF embedded metadata (`CreationDate`, `ModDate`) extracted from file internals.
- Used filename semantics (year markers and topic).
- Limitation: full body text extraction is not available in this terminal session.

## Freshness Table (Key PDFs)

| File | Embedded Date | Risk | Reason | Action |
|---|---|---|---|---|
| `Упатства\Upatstvo za digitalno potpisuvanje_feb.2026.pdf` | 2026-02-13 | Low | Explicit 2026 date and current topic | Keep as current baseline |
| `Упатства\Упатство-техничка-спецификација-и-образец-на-техничка-понуда.pdf` | 2025-04-09 | Medium-Low | Relatively recent | Keep, verify against 2026 amendments |
| `Упатства\Upatstvo-Podnesuvanje ponuda na ESJN.pdf` | 2025-04-01 | Medium | ESJN workflow can change quickly | Validate current portal flow/screens |
| `Упатства\Upatstvo-za-popolnuvanje-na-finansiskiot-obrazec.pdf` | 2025-04-01 | Medium | Not old, but duplicate files create version ambiguity | Keep one canonical copy |
| `Упатства\Upatstvo-za-popolnuvanje-na-finansiskiot-obrazec (1).pdf` | 2025-04-01 | Medium | Exact duplicate | Remove/archive |
| `Упатства\Upatstvo za popolnuvanje na finansiskiot obrazec.pdf` | 2025-04-01 | Medium | Exact duplicate | Remove/archive |
| `Упатства\Preporaki_primena-na-ZJN_krajna-itnost.pdf` | 2024-09-26 | Medium-High | Urgency procurement guidance can become outdated | Revalidate against current law |
| `Упатства\Priracnik-za-nevoobicaeno-niska-cena_BJN.pdf` | 2024-03-13 | Medium | Potentially still valid, check updates | Verify legal references |
| `Упатства\MKD_Guideline-MEAT-criteria-final.pdf` | 2023-09-20 | Medium-High | Criteria guidance may have changed | Validate scoring/criteria references |
| `Упатства\Brosura_DZR_BJN_2023.pdf` | 2023-05-08 | Medium-High | 2023 guidance likely partially stale in 2026 | Replace if newer issue exists |
| `Упатства\еПазар - Корисничко упатство за Договорни органи_Април.pdf` | 2023-04-04 | High | Platform UI/process likely changed by 2026 | Replace/update first wave |
| `Упатства\Корисничко упатство за Економски оператори_еПазар.pdf` | 2022-02-21 | High | Old platform manual | Replace urgently |
| `Упатства\Priracnik  za koristenje na ESJN za Ekonomski operatori_nov2021.pdf` | 2021-01-18 | High | Very likely outdated | Replace urgently |
| `Упатства\Priracnik za koristenje na ESJN za Dogovorni organi_nov2021.pdf` | 2021-01-08 | High | Very likely outdated | Replace urgently |

## Priority Update Queue
1. Replace the two 2021 ESJN manuals.
2. Replace the 2022 and 2023 ePazar manuals.
3. Revalidate 2023-2024 policy/guideline PDFs.
4. Keep 2025-2026 PDFs as active set after a legal-reference check.
5. Deduplicate the finance-form instruction PDFs.

## Notes
- Embedded dates are more trustworthy than local filesystem modified dates.
- Most local modified timestamps are from a single import day and should not be treated as publication dates.
