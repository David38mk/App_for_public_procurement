# Manual Context Packets

Generated: 2026-02-19 22:45:00

## Manual 1: `Упатства/Brosura-DZR-BJN-2023.pdf`
- Type: `pdf`
- Risk: `Medium`
- Tags: `n/a`
- Context summary: Brochure-style guidance related to public procurement practice; likely supports awareness and operational interpretation rather than hard transaction flow rules.
- Key process areas: institutional guidance, procurement best-practice orientation, control awareness.
- App implications: expose as reference/support material in document workspace; do not treat as direct workflow gate without stronger citation.
- Open questions: Does this contain normative mandatory steps or only explanatory guidance?
- Confidence: `medium`

## Manual 2: `Упатства/MKD-Guideline-MEAT-criteria-final.pdf`
- Type: `pdf`
- Risk: `Medium`
- Tags: `n/a`
- Context summary: Guidance around MEAT/evaluation criteria, likely affecting evaluation logic and criteria documentation quality.
- Key process areas: criteria definition, weighting/evaluation framing, scoring consistency.
- App implications: prepare template support for criteria fields and scoring rationale sections; keep this outside runtime enforcement until exact normative clauses are mapped.
- Open questions: Which criteria elements are mandatory versus recommended?
- Confidence: `medium`

## Manual 3: `Упатства/Preporaki-primena-na-ZJN-krajna-itnost.pdf`
- Type: `pdf`
- Risk: `Medium`
- Tags: `n/a`
- Context summary: Recommendations for urgent procurement scenarios; potentially sensitive due to exceptional workflow conditions.
- Key process areas: urgency path selection, justification, constrained timelines, documentation completeness.
- App implications: include optional urgency workflow branch with strict audit evidence capture and rationale fields.
- Open questions: Which urgent-process checkpoints are hard requirements in current law vs contextual recommendations?
- Confidence: `medium`

## Manual 4: `Упатства/Priracnik-za-koristenje-na-ESJN-za-Dogovorni-organi-nov2021.pdf`
- Type: `pdf`
- Risk: `High`
- Tags: `esjn`
- Context summary: Contracting-authority ESJN usage manual containing search, login, document retrieval, and operational steps.
- Key process areas: notice search and filtering, dossier access, document handling, login/role actions.
- App implications: source for search and download flows (`REQ-ESJN-2021-001..003`), but keep all derived rules in `draft` until section-level confirmation.
- Open questions: Which cited sections remain valid against current ESJN behavior in 2026?
- Confidence: `high`

## Manual 5: `Упатства/Priracnik-za-koristenje-na-ESJN-za-Ekonomski-operatori-nov2021.pdf`
- Type: `pdf`
- Risk: `High`
- Tags: `esjn`
- Context summary: Economic-operator ESJN manual covering bid submission, attachments, confirmation actions, and related dossier workflow.
- Key process areas: submission workflow, attachment handling, required inputs, confirmation/evidence steps.
- App implications: primary source for doc-builder and workspace requirements (`REQ-ESJN-2021-004..006`); requires citation hardening before runtime activation.
- Open questions: Are attachment and submission constraints unchanged in latest platform iteration?
- Confidence: `high`

## Manual 6: `Упатства/Priracnik-za-nevoobicaeno-niska-cena-BJN.pdf`
- Type: `pdf`
- Risk: `Medium`
- Tags: `n/a`
- Context summary: Guidance related to abnormally low price handling and related procedural interpretation.
- Key process areas: price anomaly handling, clarifications, documentation support.
- App implications: likely impacts evaluation documentation templates and explanation fields, not base document retrieval flow.
- Open questions: Is this currently mandatory for all procedure types or only for targeted cases?
- Confidence: `medium`

## Manual 7: `Упатства/Upatstvo-podnesuvanje-ponuda-na-ESJN.pdf`
- Type: `pdf`
- Risk: `Low`
- Tags: `esjn`
- Context summary: Recent ESJN bid-submission instruction, likely closer to current UI/flow.
- Key process areas: submission sequence, pre-submit checks, form completion.
- App implications: use as freshness anchor for newer submission UX expectations; compare against 2021 manuals to flag flow drift.
- Open questions: Which steps supersede older ESJN operator manual sections?
- Confidence: `medium`

## Manual 8: `Упатства/Upatstvo-za-digitalno-potpisuvanje-feb-2026.pdf`
- Type: `pdf`
- Risk: `Low`
- Tags: `digital-signing`
- Context summary: current digital-signature guidance likely defining signing prerequisites, tooling, and signature usage sequence.
- Key process areas: signing prerequisites, certificate usage, signature execution order, error recovery.
- App implications: add explicit signature readiness checks and user guidance before submission actions.
- Open questions: Are there signature provider-specific constraints that must be encoded?
- Confidence: `medium`

## Manual 9: `Упатства/Upatstvo-za-popolnuvanje-na-finansiskiot-obrazec.pdf`
- Type: `pdf`
- Risk: `Low`
- Tags: `financial-form`
- Context summary: instruction for completing financial forms and expected field semantics.
- Key process areas: financial form field completion, format/data rules, submission readiness.
- App implications: map financial template placeholders and validation constraints into document builder preflight checks.
- Open questions: Which financial fields are strictly mandatory by procedure type?
- Confidence: `medium`

## Manual 10: `Упатства/Zaednicki-poimnik-za-JN.doc`
- Type: `doc`
- Risk: `Low`
- Tags: `n/a`
- Context summary: likely procurement glossary/terminology source in legacy format.
- Key process areas: shared terminology and field naming harmonization.
- App implications: use as vocabulary source for labels/help text; avoid runtime enforcement from glossary-only content.
- Open questions: Should this be converted to docx/pdf and version-controlled as canonical terminology reference?
- Confidence: `low`

## Manual 11: `Упатства/еПазар-Корисничко-упатство-за-Договорни-органи-Април.pdf`
- Type: `pdf`
- Risk: `Medium`
- Tags: `epazar`
- Context summary: ePazar guidance for contracting authorities; likely process distinctions versus ESJN flow.
- Key process areas: ePazar navigation, authority-specific actions, catalog/procedure flow.
- App implications: support workflow branching between ESJN and ePazar and role-specific UI hints.
- Open questions: Is this manual superseded by a newer ePazar authority guide?
- Confidence: `medium`

## Manual 12: `Упатства/Корисничко-упатство-за-Економски-оператори-еПазар.pdf`
- Type: `pdf`
- Risk: `High`
- Tags: `epazar`
- Context summary: ePazar operator manual; draft extraction links it to process routing and mandatory field validation requirements.
- Key process areas: ePazar access, catalog mapping, mandatory input mapping, operator actions.
- App implications: source for `REQ-EPAZAR-2022-001..003`; one requirement still has unresolved citation and remains blocked.
- Open questions: Need exact section/page citation for error-handling and corrective guidance requirement (`REQ-EPAZAR-2022-003`).
- Confidence: `high`

## Manual 13: `Упатства/Упатство-техничка-спецификација-и-образец-на-техничка-понуда.pdf`
- Type: `pdf`
- Risk: `Low`
- Tags: `n/a`
- Context summary: guidance focused on technical specification and technical offer form completion.
- Key process areas: technical offer field structure, specification alignment, form consistency.
- App implications: strengthen template checks for technical-offer completeness and field-level validation.
- Open questions: Which sections define mandatory vs optional technical attachments?
- Confidence: `medium`
