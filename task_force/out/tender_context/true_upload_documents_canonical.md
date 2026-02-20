# True Upload Document Requirements (Canonical)

Status: conservative canonical baseline generated from runtime upload hints, curated baseline, and model tender documentation.

## Exclusion grounds docs

| requirement_id | document_type | nature | evidence_type | acceptance_rule | validity | confidence | review | legal_review_needed | needs_human_confirmation | source_section |
|---|---|---|---|---|---|---|---|---|---|---|
| TRUEDOC-EXCL-001 | No-exclusion declaration | mandatory | Signed declaration | Declaration covers all exclusion grounds from tender section 5.2 | Valid on submission date | high | confirmed | yes | no | baseline:5.2; baseline:5.2.4 |
| TRUEDOC-EXCL-002 | Tax/public duties clearance certificate | mandatory | Authority certificate | Shows no due unpaid taxes/public duties or approved deferral | Not older than 6 months before bid deadline | high | confirmed | yes | no | baseline:5.2.4; baseline:5.2.7 |
| TRUEDOC-EXCL-003 | No-bankruptcy certificate | mandatory | Registry/court certificate | Confirms no bankruptcy proceeding opened | Not older than 6 months before bid deadline | high | confirmed | yes | no | baseline:5.2.4; baseline:5.2.7 |
| TRUEDOC-EXCL-004 | No-liquidation certificate | mandatory | Registry/court certificate | Confirms no liquidation proceeding opened | Not older than 6 months before bid deadline | high | confirmed | yes | no | baseline:5.2.4; baseline:5.2.7 |
| TRUEDOC-EXCL-005 | Prohibition sanctions / negative references confirmation | conditional | Registry confirmations / declarations | Evidence covers prohibition sanctions and negative references status | Current at bid deadline | medium | confirmed | no | no |  |

## Professional capability docs

| requirement_id | document_type | nature | evidence_type | acceptance_rule | validity | confidence | review | legal_review_needed | needs_human_confirmation | source_section |
|---|---|---|---|---|---|---|---|---|---|---|
| TRUEDOC-PROF-001 | Registered professional activity proof | mandatory | Central registry extract / equivalent | Activity code must match subject of procurement | Must be valid at submission date | high | confirmed | no | no | baseline:5.3.1 |
| TRUEDOC-PROF-002 | Sector license/permit (if regulated activity) | conditional | License/permit/authorization | License scope covers tender service and is valid | Valid through submission and execution period | medium | confirmed | no | no | runtime:page 11; runtime:page 14 |

## Technical/professional capability docs

| requirement_id | document_type | nature | evidence_type | acceptance_rule | validity | confidence | review | legal_review_needed | needs_human_confirmation | source_section |
|---|---|---|---|---|---|---|---|---|---|---|
| TRUEDOC-TECH-001 | Technical/professional capability statement | mandatory | Signed statement | Covers all minimum technical/professional criteria from section 5.3.2 | Valid on submission date | high | confirmed | no | no | baseline:5.3.2 |
| TRUEDOC-TECH-002 | Proof of key personnel engagement | mandatory | Employment contracts / engagement declarations | Quantity and profiles meet requested minimum staffing | Current at submission date | high | confirmed | no | no |  |
| TRUEDOC-TECH-003 | Key personnel professional certificates | mandatory | Certificates (CCIE/CCNP/PMP/ITIL or equivalent) | Certificates satisfy minimum count and equivalence clause | Valid on submission date | high | confirmed | yes | no | baseline:5.3.2.1; runtime:page 11; runtime:page 14; runtime:page 7; runtime:page 9 |
| TRUEDOC-TECH-004 | Reference list of similar contracts | conditional | Reference list + confirmations | Meets minimum number/value/period from tender section | References fall inside requested time window | medium | confirmed | no | no |  |

## Quality standards (ISO etc.)

| requirement_id | document_type | nature | evidence_type | acceptance_rule | validity | confidence | review | legal_review_needed | needs_human_confirmation | source_section |
|---|---|---|---|---|---|---|---|---|---|---|
| TRUEDOC-QUAL-001 | ISO 27001 certificate | mandatory | ISO certificate | Valid ISO certificate with scope aligned to tender requirement | Valid on submission date | high | confirmed | yes | no | baseline:5.4.1 |
| TRUEDOC-QUAL-002 | ISO 20000-1 certificate | mandatory | ISO certificate | Valid ISO certificate with scope aligned to tender requirement | Valid on submission date | high | confirmed | yes | no | baseline:5.4.1 |
| TRUEDOC-QUAL-003 | ISO 22301 certificate | mandatory | ISO certificate | Valid ISO certificate with scope aligned to tender requirement | Valid on submission date | high | confirmed | yes | no | baseline:5.4.1 |

## Guarantees

| requirement_id | document_type | nature | evidence_type | acceptance_rule | validity | confidence | review | legal_review_needed | needs_human_confirmation | source_section |
|---|---|---|---|---|---|---|---|---|---|---|
| TRUEDOC-GUAR-001 | Bid seriousness declaration / bid security | conditional | Signed statement and/or bid bond | Signed by authorized person; valid through bid validity period | At least bid validity period | high | confirmed | yes | no | model:сериозност; runtime:page 11; runtime:page 9 |
| TRUEDOC-GUAR-002 | Performance bank guarantee | conditional | Original bank guarantee | Amount and wording match tender/contract clauses (5% in baseline 01606/2026) | Valid for contract execution period defined in tender | high | confirmed | yes | no | baseline:3.8.2; model:гаранција |

## Offer forms (technical/financial/declarations)

| requirement_id | document_type | nature | evidence_type | acceptance_rule | validity | confidence | review | legal_review_needed | needs_human_confirmation | source_section |
|---|---|---|---|---|---|---|---|---|---|---|
| TRUEDOC-OFFER-001 | Technical offer form with annexes | mandatory | Completed and signed form | All technical characteristics answered against minimum requirements | Final signed version at submission | high | confirmed | no | no | model:техничка понуда; runtime:page 10 |
| TRUEDOC-OFFER-002 | Financial offer form | mandatory | Completed and signed form | Price in MKD with VAT shown separately; arithmetic consistency | Final signed version at submission | high | confirmed | no | no | model:финансиска понуда; runtime:page 10 |
| TRUEDOC-OFFER-003 | Capability declaration form (Prilog-3) | mandatory | Signed declaration template | Template completed and signed by authorized representative | Valid on submission date | high | confirmed | no | no | model:prilog-3; model:способност; runtime:page 10; runtime:page 11; runtime:page 13; runtime:page 16; runtime:page 9 |
| TRUEDOC-OFFER-004 | Subcontractor forms (data + consent) | conditional | Subcontractor data form and signed consent | Each subcontractor form complete and signed | Valid on submission date | medium | draft | no | yes | model:подизведувач |
| TRUEDOC-OFFER-005 | Group bid documents (group data + group agreement) | conditional | Group bidder data + signed group agreement | All consortium members and lead member clearly identified | Valid on submission date | medium | draft | no | yes | model:групна понуда |

## Conditional/contract-stage docs

| requirement_id | document_type | nature | evidence_type | acceptance_rule | validity | confidence | review | legal_review_needed | needs_human_confirmation | source_section |
|---|---|---|---|---|---|---|---|---|---|---|
| TRUEDOC-COND-001 | Full supporting documents package after selection | conditional | Scanned supporting certificates/documents | Selected bidder submits complete package within commission deadline | Deadline not shorter than 3 working days (baseline section 5.1.3) | high | confirmed | yes | no | baseline:5.1.3; model:доказ; runtime:page 16 |
| TRUEDOC-COND-002 | Qualified electronic signature certificate | mandatory | Qualified e-signature certificate | Offer files electronically signed by authorized person | Certificate valid on submission date | high | confirmed | no | no | runtime:page 10; runtime:page 7 |
