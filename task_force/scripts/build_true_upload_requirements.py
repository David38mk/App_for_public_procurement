#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

from openpyxl import Workbook


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "task_force" / "out" / "tender_context"
MODEL_DIR = ROOT / "\u043c\u043e\u0434\u0435\u043b\u0438 \u043d\u0430 \u0442\u0435\u043d\u0434\u0435\u0440\u0441\u043a\u0430 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0446\u0438\u0458\u0430"

CSV_OUT = OUT_DIR / "true_upload_documents_canonical.csv"
MD_OUT = OUT_DIR / "true_upload_documents_canonical.md"
XLSX_OUT = OUT_DIR / "true_upload_documents_canonical.xlsx"
OPEN_Q_OUT = OUT_DIR / "true_upload_documents_open_questions.md"


KW_SERIOZNOST = "\u0441\u0435\u0440\u0438\u043e\u0437\u043d\u043e\u0441\u0442"
KW_SPOSOBNOST = "\u0441\u043f\u043e\u0441\u043e\u0431\u043d\u043e\u0441\u0442"
KW_ISO_27001 = "iso 27001"
KW_ISO_20000 = "iso 20000"
KW_ISO_22301 = "iso 22301"
KW_QUALIFIED_CERT = "\u043a\u0432\u0430\u043b\u0438\u0444\u0438\u043a\u0443\u0432\u0430\u043d \u0441\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442"
KW_ELECTRONIC_SIG = "\u0435\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u0441\u043a\u0438 \u043f\u043e\u0442\u043f\u0438\u0441"
KW_PODIZVEDUVAC = "\u043f\u043e\u0434\u0438\u0437\u0432\u0435\u0434\u0443\u0432\u0430\u0447"
KW_GRUPNA_PONUDA = "\u0433\u0440\u0443\u043f\u043d\u0430 \u043f\u043e\u043d\u0443\u0434\u0430"
KW_DANOK = "\u0434\u0430\u043d\u043e\u0447"
KW_STECAJ = "\u0441\u0442\u0435\u0447\u0430\u0458"
KW_LIKVIDACIJA = "\u043b\u0438\u043a\u0432\u0438\u0434\u0430\u0446\u0438\u0458"
KW_LICENSE = "\u043b\u0438\u0446\u0435\u043d\u0446"
KW_NO_EXCLUSION = "\u0438\u0441\u043a\u043b\u0443\u0447\u0443\u0432\u0430\u045a"

MODEL_COMMON_PATTERN = "model_common_uslovi_*.md"
BASELINE_MD = OUT_DIR / "true_uslovi_baseline_01606_2026.md"
BASELINE_CSV = OUT_DIR / "upload_requirements_template_01606_2026.csv"


@dataclass
class Requirement:
    group_category: str
    requirement_id: str
    document_type: str
    requirement_nature: str
    condition_trigger: str
    evidence_type: str
    acceptance_rule: str
    validity_constraints: str
    source_confidence: str
    review_status: str
    legal_review_needed: str
    needs_human_confirmation: str
    normalized_from_tags: str
    source_files: set[str] = field(default_factory=set)
    source_sections: set[str] = field(default_factory=set)
    runtime_hits: int = 0
    runtime_files: set[str] = field(default_factory=set)
    rule_test_linkage: str = (
        "task_force/scripts/extract_tender_context.py:build_upload_hints; "
        "tests/compliance/test_approval_consistency.py"
    )
    notes: str = ""


def slug_sort_key(req_id: str) -> tuple[str, str]:
    parts = req_id.split("-")
    return (parts[1] if len(parts) > 1 else req_id, req_id)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def collect_model_docx_files() -> list[Path]:
    files: list[Path] = []
    if MODEL_DIR.exists():
        files = sorted(MODEL_DIR.rglob("*.docx"))
    return files


def collect_model_doc_files() -> list[Path]:
    files: list[Path] = []
    if MODEL_DIR.exists():
        files = sorted(MODEL_DIR.rglob("*.doc"))
    return files


def extract_docx_text(path: Path) -> str:
    chunks: list[str] = []
    with zipfile.ZipFile(path, "r") as zf:
        xml_names = [n for n in zf.namelist() if n.startswith("word/") and n.endswith(".xml")]
        for name in xml_names:
            if not any(k in name for k in ("document.xml", "header", "footer")):
                continue
            root = ET.fromstring(zf.read(name))
            vals = [node.text or "" for node in root.findall(".//{*}t")]
            vals = [v.strip() for v in vals if v and v.strip()]
            if vals:
                chunks.append(" ".join(vals))
    return normalize_space(" ".join(chunks))


def classify_runtime_hint(row: dict[str, str]) -> str | None:
    tag = (row.get("tag") or "").strip().lower()
    snippet = normalize_space((row.get("snippet") or "").lower())

    if KW_PODIZVEDUVAC in snippet:
        return "TRUEDOC-OFFER-004"
    if KW_GRUPNA_PONUDA in snippet:
        return "TRUEDOC-OFFER-005"

    if tag == "technical_offer":
        return "TRUEDOC-OFFER-001"
    if tag == "financial_offer":
        return "TRUEDOC-OFFER-002"
    if tag == "reference_list":
        return "TRUEDOC-TECH-004"
    if tag == "license":
        return "TRUEDOC-PROF-002"
    if tag == "bank_guarantee":
        if KW_SERIOZNOST in snippet:
            return "TRUEDOC-GUAR-001"
        return "TRUEDOC-GUAR-002"
    if tag == "declaration_statement":
        if KW_SERIOZNOST in snippet:
            return "TRUEDOC-GUAR-001"
        if KW_SPOSOBNOST in snippet:
            return "TRUEDOC-OFFER-003"
        if KW_NO_EXCLUSION in snippet:
            return "TRUEDOC-EXCL-001"
        return "TRUEDOC-OFFER-003"
    if tag == "certificate":
        if KW_ISO_27001 in snippet:
            return "TRUEDOC-QUAL-001"
        if KW_ISO_20000 in snippet:
            return "TRUEDOC-QUAL-002"
        if KW_ISO_22301 in snippet:
            return "TRUEDOC-QUAL-003"
        if KW_QUALIFIED_CERT in snippet or KW_ELECTRONIC_SIG in snippet:
            return "TRUEDOC-COND-002"
        return "TRUEDOC-TECH-003"
    if tag == "proof_document":
        if KW_DANOK in snippet:
            return "TRUEDOC-EXCL-002"
        if KW_STECAJ in snippet:
            return "TRUEDOC-EXCL-003"
        if KW_LIKVIDACIJA in snippet:
            return "TRUEDOC-EXCL-004"
        if KW_LICENSE in snippet:
            return "TRUEDOC-PROF-002"
        return "TRUEDOC-COND-001"
    return None


def build_requirements() -> dict[str, Requirement]:
    reqs = {
        "TRUEDOC-EXCL-001": Requirement(
            group_category="Exclusion grounds docs",
            requirement_id="TRUEDOC-EXCL-001",
            document_type="No-exclusion declaration",
            requirement_nature="mandatory",
            condition_trigger="Always with bid",
            evidence_type="Signed declaration",
            acceptance_rule="Declaration covers all exclusion grounds from tender section 5.2",
            validity_constraints="Valid on submission date",
            source_confidence="high",
            review_status="confirmed",
            legal_review_needed="yes",
            needs_human_confirmation="no",
            normalized_from_tags="declaration_statement",
        ),
        "TRUEDOC-EXCL-002": Requirement(
            group_category="Exclusion grounds docs",
            requirement_id="TRUEDOC-EXCL-002",
            document_type="Tax/public duties clearance certificate",
            requirement_nature="mandatory",
            condition_trigger="Always for capability proof package",
            evidence_type="Authority certificate",
            acceptance_rule="Shows no due unpaid taxes/public duties or approved deferral",
            validity_constraints="Not older than 6 months before bid deadline",
            source_confidence="high",
            review_status="confirmed",
            legal_review_needed="yes",
            needs_human_confirmation="no",
            normalized_from_tags="proof_document",
        ),
        "TRUEDOC-EXCL-003": Requirement(
            group_category="Exclusion grounds docs",
            requirement_id="TRUEDOC-EXCL-003",
            document_type="No-bankruptcy certificate",
            requirement_nature="mandatory",
            condition_trigger="Always for capability proof package",
            evidence_type="Registry/court certificate",
            acceptance_rule="Confirms no bankruptcy proceeding opened",
            validity_constraints="Not older than 6 months before bid deadline",
            source_confidence="high",
            review_status="confirmed",
            legal_review_needed="yes",
            needs_human_confirmation="no",
            normalized_from_tags="proof_document",
        ),
        "TRUEDOC-EXCL-004": Requirement(
            group_category="Exclusion grounds docs",
            requirement_id="TRUEDOC-EXCL-004",
            document_type="No-liquidation certificate",
            requirement_nature="mandatory",
            condition_trigger="Always for capability proof package",
            evidence_type="Registry/court certificate",
            acceptance_rule="Confirms no liquidation proceeding opened",
            validity_constraints="Not older than 6 months before bid deadline",
            source_confidence="high",
            review_status="confirmed",
            legal_review_needed="yes",
            needs_human_confirmation="no",
            normalized_from_tags="proof_document",
        ),
        "TRUEDOC-EXCL-005": Requirement(
            group_category="Exclusion grounds docs",
            requirement_id="TRUEDOC-EXCL-005",
            document_type="Prohibition sanctions / negative references confirmation",
            requirement_nature="conditional",
            condition_trigger="If requested explicitly by contracting authority",
            evidence_type="Registry confirmations / declarations",
            acceptance_rule="Evidence covers prohibition sanctions and negative references status",
            validity_constraints="Current at bid deadline",
            source_confidence="medium",
            review_status="confirmed",
            legal_review_needed="no",
            needs_human_confirmation="no",
            normalized_from_tags="declaration_statement,proof_document",
            notes="User decision: negative reference evidence is never mandatory.",
        ),
        "TRUEDOC-PROF-001": Requirement(
            group_category="Professional capability docs",
            requirement_id="TRUEDOC-PROF-001",
            document_type="Registered professional activity proof",
            requirement_nature="mandatory",
            condition_trigger="Always",
            evidence_type="Central registry extract / equivalent",
            acceptance_rule="Activity code must match subject of procurement",
            validity_constraints="Must be valid at submission date",
            source_confidence="high",
            review_status="confirmed",
            legal_review_needed="no",
            needs_human_confirmation="no",
            normalized_from_tags="license,proof_document",
        ),
        "TRUEDOC-PROF-002": Requirement(
            group_category="Professional capability docs",
            requirement_id="TRUEDOC-PROF-002",
            document_type="Sector license/permit (if regulated activity)",
            requirement_nature="conditional",
            condition_trigger="Only when law requires special permit",
            evidence_type="License/permit/authorization",
            acceptance_rule="License scope covers tender service and is valid",
            validity_constraints="Valid through submission and execution period",
            source_confidence="medium",
            review_status="confirmed",
            legal_review_needed="no",
            needs_human_confirmation="no",
            normalized_from_tags="license",
            notes="User decision: keep conditional by sector, but attach license proactively when available.",
        ),
        "TRUEDOC-TECH-001": Requirement(
            group_category="Technical/professional capability docs",
            requirement_id="TRUEDOC-TECH-001",
            document_type="Technical/professional capability statement",
            requirement_nature="mandatory",
            condition_trigger="Always",
            evidence_type="Signed statement",
            acceptance_rule="Covers all minimum technical/professional criteria from section 5.3.2",
            validity_constraints="Valid on submission date",
            source_confidence="high",
            review_status="confirmed",
            legal_review_needed="no",
            needs_human_confirmation="no",
            normalized_from_tags="declaration_statement",
        ),
        "TRUEDOC-TECH-002": Requirement(
            group_category="Technical/professional capability docs",
            requirement_id="TRUEDOC-TECH-002",
            document_type="Proof of key personnel engagement",
            requirement_nature="mandatory",
            condition_trigger="When key experts are required",
            evidence_type="Employment contracts / engagement declarations",
            acceptance_rule="Quantity and profiles meet requested minimum staffing",
            validity_constraints="Current at submission date",
            source_confidence="high",
            review_status="confirmed",
            legal_review_needed="no",
            needs_human_confirmation="no",
            normalized_from_tags="proof_document",
        ),
        "TRUEDOC-TECH-003": Requirement(
            group_category="Technical/professional capability docs",
            requirement_id="TRUEDOC-TECH-003",
            document_type="Key personnel professional certificates",
            requirement_nature="mandatory",
            condition_trigger="When certification profile is required",
            evidence_type="Certificates (CCIE/CCNP/PMP/ITIL or equivalent)",
            acceptance_rule="Certificates satisfy minimum count and equivalence clause",
            validity_constraints="Valid on submission date",
            source_confidence="high",
            review_status="confirmed",
            legal_review_needed="yes",
            needs_human_confirmation="no",
            normalized_from_tags="certificate",
        ),
        "TRUEDOC-TECH-004": Requirement(
            group_category="Technical/professional capability docs",
            requirement_id="TRUEDOC-TECH-004",
            document_type="Reference list of similar contracts",
            requirement_nature="conditional",
            condition_trigger="If tender requires prior experience references",
            evidence_type="Reference list + confirmations",
            acceptance_rule="Meets minimum number/value/period from tender section",
            validity_constraints="References fall inside requested time window",
            source_confidence="medium",
            review_status="confirmed",
            legal_review_needed="no",
            needs_human_confirmation="no",
            normalized_from_tags="reference_list",
            notes="User decision: reference evidence is tender-specific.",
        ),
    }
    reqs.update(
        {
            "TRUEDOC-QUAL-001": Requirement(
                group_category="Quality standards (ISO etc.)",
                requirement_id="TRUEDOC-QUAL-001",
                document_type="ISO 27001 certificate",
                requirement_nature="mandatory",
                condition_trigger="When quality standards section requires ISO 27001",
                evidence_type="ISO certificate",
                acceptance_rule="Valid ISO certificate with scope aligned to tender requirement",
                validity_constraints="Valid on submission date",
                source_confidence="high",
                review_status="confirmed",
                legal_review_needed="yes",
                needs_human_confirmation="no",
                normalized_from_tags="certificate",
            ),
            "TRUEDOC-QUAL-002": Requirement(
                group_category="Quality standards (ISO etc.)",
                requirement_id="TRUEDOC-QUAL-002",
                document_type="ISO 20000-1 certificate",
                requirement_nature="mandatory",
                condition_trigger="When quality standards section requires ISO 20000-1",
                evidence_type="ISO certificate",
                acceptance_rule="Valid ISO certificate with scope aligned to tender requirement",
                validity_constraints="Valid on submission date",
                source_confidence="high",
                review_status="confirmed",
                legal_review_needed="yes",
                needs_human_confirmation="no",
                normalized_from_tags="certificate",
            ),
            "TRUEDOC-QUAL-003": Requirement(
                group_category="Quality standards (ISO etc.)",
                requirement_id="TRUEDOC-QUAL-003",
                document_type="ISO 22301 certificate",
                requirement_nature="mandatory",
                condition_trigger="When quality standards section requires ISO 22301",
                evidence_type="ISO certificate",
                acceptance_rule="Valid ISO certificate with scope aligned to tender requirement",
                validity_constraints="Valid on submission date",
                source_confidence="high",
                review_status="confirmed",
                legal_review_needed="yes",
                needs_human_confirmation="no",
                normalized_from_tags="certificate",
            ),
            "TRUEDOC-GUAR-001": Requirement(
                group_category="Guarantees",
                requirement_id="TRUEDOC-GUAR-001",
                document_type="Bid seriousness declaration / bid security",
                requirement_nature="conditional",
                condition_trigger="If tender chapter 3.8 requires it",
                evidence_type="Signed statement and/or bid bond",
                acceptance_rule="Signed by authorized person; valid through bid validity period",
                validity_constraints="At least bid validity period",
                source_confidence="high",
                review_status="confirmed",
                legal_review_needed="yes",
                needs_human_confirmation="no",
                normalized_from_tags="declaration_statement,bank_guarantee",
            ),
            "TRUEDOC-GUAR-002": Requirement(
                group_category="Guarantees",
                requirement_id="TRUEDOC-GUAR-002",
                document_type="Performance bank guarantee",
                requirement_nature="conditional",
                condition_trigger="Selected bidder before contract execution",
                evidence_type="Original bank guarantee",
                acceptance_rule="Amount and wording match tender/contract clauses (5% in baseline 01606/2026)",
                validity_constraints="Valid for contract execution period defined in tender",
                source_confidence="high",
                review_status="confirmed",
                legal_review_needed="yes",
                needs_human_confirmation="no",
                normalized_from_tags="bank_guarantee",
            ),
            "TRUEDOC-OFFER-001": Requirement(
                group_category="Offer forms (technical/financial/declarations)",
                requirement_id="TRUEDOC-OFFER-001",
                document_type="Technical offer form with annexes",
                requirement_nature="mandatory",
                condition_trigger="Always",
                evidence_type="Completed and signed form",
                acceptance_rule="All technical characteristics answered against minimum requirements",
                validity_constraints="Final signed version at submission",
                source_confidence="high",
                review_status="confirmed",
                legal_review_needed="no",
                needs_human_confirmation="no",
                normalized_from_tags="technical_offer",
            ),
            "TRUEDOC-OFFER-002": Requirement(
                group_category="Offer forms (technical/financial/declarations)",
                requirement_id="TRUEDOC-OFFER-002",
                document_type="Financial offer form",
                requirement_nature="mandatory",
                condition_trigger="Always",
                evidence_type="Completed and signed form",
                acceptance_rule="Price in MKD with VAT shown separately; arithmetic consistency",
                validity_constraints="Final signed version at submission",
                source_confidence="high",
                review_status="confirmed",
                legal_review_needed="no",
                needs_human_confirmation="no",
                normalized_from_tags="financial_offer",
            ),
            "TRUEDOC-OFFER-003": Requirement(
                group_category="Offer forms (technical/financial/declarations)",
                requirement_id="TRUEDOC-OFFER-003",
                document_type="Capability declaration form (Prilog-3)",
                requirement_nature="mandatory",
                condition_trigger="When bidder uses declaration route for capability proof",
                evidence_type="Signed declaration template",
                acceptance_rule="Template completed and signed by authorized representative",
                validity_constraints="Valid on submission date",
                source_confidence="high",
                review_status="confirmed",
                legal_review_needed="no",
                needs_human_confirmation="no",
                normalized_from_tags="declaration_statement",
            ),
            "TRUEDOC-OFFER-004": Requirement(
                group_category="Offer forms (technical/financial/declarations)",
                requirement_id="TRUEDOC-OFFER-004",
                document_type="Subcontractor forms (data + consent)",
                requirement_nature="conditional",
                condition_trigger="Only if subcontractors are declared",
                evidence_type="Subcontractor data form and signed consent",
                acceptance_rule="Each subcontractor form complete and signed",
                validity_constraints="Valid on submission date",
                source_confidence="medium",
                review_status="draft",
                legal_review_needed="no",
                needs_human_confirmation="yes",
                normalized_from_tags="proof_document",
            ),
            "TRUEDOC-OFFER-005": Requirement(
                group_category="Offer forms (technical/financial/declarations)",
                requirement_id="TRUEDOC-OFFER-005",
                document_type="Group bid documents (group data + group agreement)",
                requirement_nature="conditional",
                condition_trigger="Only for consortium/group bids",
                evidence_type="Group bidder data + signed group agreement",
                acceptance_rule="All consortium members and lead member clearly identified",
                validity_constraints="Valid on submission date",
                source_confidence="medium",
                review_status="draft",
                legal_review_needed="no",
                needs_human_confirmation="yes",
                normalized_from_tags="proof_document",
            ),
            "TRUEDOC-COND-001": Requirement(
                group_category="Conditional/contract-stage docs",
                requirement_id="TRUEDOC-COND-001",
                document_type="Full supporting documents package after selection",
                requirement_nature="conditional",
                condition_trigger="If bid submitted with declaration-only capability proof",
                evidence_type="Scanned supporting certificates/documents",
                acceptance_rule="Selected bidder submits complete package within commission deadline",
                validity_constraints="Deadline not shorter than 3 working days (baseline section 5.1.3)",
                source_confidence="high",
                review_status="confirmed",
                legal_review_needed="yes",
                needs_human_confirmation="no",
                normalized_from_tags="proof_document,declaration_statement",
            ),
            "TRUEDOC-COND-002": Requirement(
                group_category="Conditional/contract-stage docs",
                requirement_id="TRUEDOC-COND-002",
                document_type="Qualified electronic signature certificate",
                requirement_nature="mandatory",
                condition_trigger="Always for e-submission in ESJN",
                evidence_type="Qualified e-signature certificate",
                acceptance_rule="Offer files electronically signed by authorized person",
                validity_constraints="Certificate valid on submission date",
                source_confidence="high",
                review_status="confirmed",
                legal_review_needed="no",
                needs_human_confirmation="no",
                normalized_from_tags="certificate",
            ),
        }
    )
    return reqs


def apply_baseline_traceability(reqs: dict[str, Requirement]) -> None:
    if BASELINE_CSV.exists():
        rows = read_csv_rows(BASELINE_CSV)
        mapping = {
            "REQ-01606-EXCL-001": "TRUEDOC-EXCL-001",
            "REQ-01606-TAX-001": "TRUEDOC-EXCL-002",
            "REQ-01606-BANKR-001": "TRUEDOC-EXCL-003",
            "REQ-01606-LIQ-001": "TRUEDOC-EXCL-004",
            "REQ-01606-PROF-001": "TRUEDOC-PROF-001",
            "REQ-01606-TECH-001": "TRUEDOC-TECH-001",
            "REQ-01606-CERT-CCIE-001": "TRUEDOC-TECH-003",
            "REQ-01606-CERT-CCNPSEC-001": "TRUEDOC-TECH-003",
            "REQ-01606-CERT-PMP-001": "TRUEDOC-TECH-003",
            "REQ-01606-CERT-ITIL-001": "TRUEDOC-TECH-003",
            "REQ-01606-CERT-CCNPENT-001": "TRUEDOC-TECH-003",
            "REQ-01606-ISO-27001-001": "TRUEDOC-QUAL-001",
            "REQ-01606-ISO-20000-001": "TRUEDOC-QUAL-002",
            "REQ-01606-ISO-22301-001": "TRUEDOC-QUAL-003",
            "REQ-01606-GUAR-001": "TRUEDOC-GUAR-002",
        }
        for row in rows:
            src_id = row.get("requirement_id", "").strip()
            req_id = mapping.get(src_id)
            if not req_id:
                continue
            req = reqs[req_id]
            req.source_files.add(str(BASELINE_CSV.relative_to(ROOT)))
            sec = row.get("source_section", "").strip()
            if sec:
                req.source_sections.add(f"baseline:{sec}")

    if BASELINE_MD.exists():
        baseline_rel = str(BASELINE_MD.relative_to(ROOT))
        for req in reqs.values():
            req.source_files.add(baseline_rel)

        reqs["TRUEDOC-COND-001"].source_sections.add("baseline:5.1.3")
        reqs["TRUEDOC-EXCL-001"].source_sections.add("baseline:5.2")
        reqs["TRUEDOC-EXCL-002"].source_sections.add("baseline:5.2.4")
        reqs["TRUEDOC-EXCL-003"].source_sections.add("baseline:5.2.4")
        reqs["TRUEDOC-EXCL-004"].source_sections.add("baseline:5.2.4")
        reqs["TRUEDOC-EXCL-002"].source_sections.add("baseline:5.2.7")
        reqs["TRUEDOC-EXCL-003"].source_sections.add("baseline:5.2.7")
        reqs["TRUEDOC-EXCL-004"].source_sections.add("baseline:5.2.7")


def apply_runtime_traceability(reqs: dict[str, Requirement], hint_rows: Iterable[dict[str, str]]) -> None:
    runtime_csv_by_req: dict[str, set[str]] = defaultdict(set)
    for row in hint_rows:
        req_id = classify_runtime_hint(row)
        if not req_id or req_id not in reqs:
            continue
        req = reqs[req_id]
        req.runtime_hits += 1
        src_file = (row.get("file") or "").strip()
        if src_file:
            req.runtime_files.add(src_file)
            req.source_files.add(f"downloads/{src_file}")
        src_page = (row.get("source_page") or "").strip()
        if src_page:
            req.source_sections.add(f"runtime:page {src_page}")
        csv_name = (row.get("_from_csv") or "").strip()
        if csv_name:
            runtime_csv_by_req[req_id].add(csv_name)

    for req_id, csv_files in runtime_csv_by_req.items():
        for runtime_file in sorted(csv_files):
            reqs[req_id].source_files.add(f"task_force/out/tender_context/{runtime_file}")


def apply_model_traceability(reqs: dict[str, Requirement]) -> tuple[list[Path], list[Path]]:
    model_docx = collect_model_docx_files()
    model_doc = collect_model_doc_files()
    model_common_files = sorted(OUT_DIR.glob(MODEL_COMMON_PATTERN))
    if model_common_files:
        latest_common = model_common_files[-1]
        common_rel = str(latest_common.relative_to(ROOT))
        for req in reqs.values():
            req.source_files.add(common_rel)

    keyword_to_req = {
        KW_SERIOZNOST: "TRUEDOC-GUAR-001",
        "\u0433\u0430\u0440\u0430\u043d\u0446\u0438\u0458\u0430": "TRUEDOC-GUAR-002",
        "\u043f\u043e\u0434\u0438\u0437\u0432\u0435\u0434\u0443\u0432\u0430\u0447": "TRUEDOC-OFFER-004",
        "\u0433\u0440\u0443\u043f\u043d\u0430 \u043f\u043e\u043d\u0443\u0434\u0430": "TRUEDOC-OFFER-005",
        "\u0441\u043f\u043e\u0441\u043e\u0431\u043d\u043e\u0441\u0442": "TRUEDOC-OFFER-003",
        "\u0442\u0435\u0445\u043d\u0438\u0447\u043a\u0430 \u043f\u043e\u043d\u0443\u0434\u0430": "TRUEDOC-OFFER-001",
        "\u0444\u0438\u043d\u0430\u043d\u0441\u0438\u0441\u043a\u0430 \u043f\u043e\u043d\u0443\u0434\u0430": "TRUEDOC-OFFER-002",
        "\u0434\u043e\u043a\u0430\u0437": "TRUEDOC-COND-001",
    }

    for path in model_docx:
        text = extract_docx_text(path).lower()
        if not text:
            continue
        rel = str(path.relative_to(ROOT))
        for kw, req_id in keyword_to_req.items():
            if kw in text:
                req = reqs[req_id]
                req.source_files.add(rel)
                req.source_sections.add(f"model:{kw}")

        if "feb-25" in path.name.lower():
            reqs["TRUEDOC-OFFER-003"].source_files.add(rel)
            reqs["TRUEDOC-OFFER-003"].source_sections.add("model:prilog-3")

    return (model_docx, model_doc)


def to_row(req: Requirement) -> dict[str, str]:
    return {
        "group_category": req.group_category,
        "requirement_id": req.requirement_id,
        "document_type": req.document_type,
        "requirement_nature": req.requirement_nature,
        "condition_trigger": req.condition_trigger,
        "evidence_type": req.evidence_type,
        "acceptance_rule": req.acceptance_rule,
        "validity_constraints": req.validity_constraints,
        "source_confidence": req.source_confidence,
        "review_status": req.review_status,
        "legal_review_needed": req.legal_review_needed,
        "needs_human_confirmation": req.needs_human_confirmation,
        "source_file": "; ".join(sorted(req.source_files)),
        "source_section": "; ".join(sorted(req.source_sections)),
        "rule_test_linkage": req.rule_test_linkage,
        "normalized_from_tags": req.normalized_from_tags,
        "runtime_hits": str(req.runtime_hits),
        "runtime_source_files": "; ".join(sorted(req.runtime_files)),
        "notes": req.notes,
    }


def write_csv(rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "group_category",
        "requirement_id",
        "document_type",
        "requirement_nature",
        "condition_trigger",
        "evidence_type",
        "acceptance_rule",
        "validity_constraints",
        "source_confidence",
        "review_status",
        "legal_review_needed",
        "needs_human_confirmation",
        "source_file",
        "source_section",
        "rule_test_linkage",
        "normalized_from_tags",
        "runtime_hits",
        "runtime_source_files",
        "notes",
    ]
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_xlsx(rows: list[dict[str, str]]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "canonical_docs"
    headers = list(rows[0].keys()) if rows else []
    ws.append(headers)
    for row in rows:
        ws.append([row[h] for h in headers])
    wb.save(XLSX_OUT)


def write_markdown(rows: list[dict[str, str]]) -> None:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["group_category"]].append(row)

    ordered_groups = [
        "Exclusion grounds docs",
        "Professional capability docs",
        "Technical/professional capability docs",
        "Quality standards (ISO etc.)",
        "Guarantees",
        "Offer forms (technical/financial/declarations)",
        "Conditional/contract-stage docs",
    ]

    lines = [
        "# True Upload Document Requirements (Canonical)",
        "",
        "Status: conservative canonical baseline generated from runtime upload hints, curated baseline, and model tender documentation.",
        "",
    ]
    for group in ordered_groups:
        rows_in_group = sorted(grouped.get(group, []), key=lambda r: slug_sort_key(r["requirement_id"]))
        if not rows_in_group:
            continue
        lines.append(f"## {group}")
        lines.append("")
        lines.append("| requirement_id | document_type | nature | evidence_type | acceptance_rule | validity | confidence | review | legal_review_needed | needs_human_confirmation | source_section |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for row in rows_in_group:
            lines.append(
                "| "
                + " | ".join(
                    [
                        row["requirement_id"],
                        row["document_type"],
                        row["requirement_nature"],
                        row["evidence_type"],
                        row["acceptance_rule"],
                        row["validity_constraints"],
                        row["source_confidence"],
                        row["review_status"],
                        row["legal_review_needed"],
                        row["needs_human_confirmation"],
                        row["source_section"],
                    ]
                )
                + " |"
            )
        lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def write_open_questions(rows: list[dict[str, str]], model_doc_files: list[Path]) -> None:
    questions: list[str] = []

    for row in rows:
        if row["needs_human_confirmation"] == "yes":
            questions.append(
                f"- `{row['requirement_id']}` ({row['document_type']}): confirm exact trigger and upload slot mapping for production."
            )
        elif row["legal_review_needed"] == "yes" and row["review_status"] != "confirmed":
            questions.append(
                f"- `{row['requirement_id']}`: legal interpretation needed before confirmation."
            )

    if model_doc_files:
        unresolved = ", ".join(sorted(str(p.relative_to(ROOT)) for p in model_doc_files))
        questions.append(
            "- Legacy `.doc` model files could not be parsed deterministically in this pass; review manually: "
            + unresolved
        )

    lines = [
        "# Open Questions - Canonical Upload Documents",
        "",
        "These items remain intentionally conservative and require explicit human confirmation before hard policy use.",
        "",
        "## Needs Human Confirmation",
    ]
    if questions:
        lines.extend(questions)
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Decisions Needed",
            "- Confirm exact upload-slot mapping in ESJN for consortium/subcontractor documents.",
            "- Keep remaining consortium/subcontractor mapping decision for final phase.",
        ]
    )
    OPEN_Q_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    reqs = build_requirements()
    tagged_rows: list[dict[str, str]] = []
    for p in sorted(OUT_DIR.glob("upload_hints_*.csv")):
        rows = read_csv_rows(p)
        for row in rows:
            tagged = dict(row)
            tagged["_from_csv"] = p.name
            tagged_rows.append(tagged)

    apply_baseline_traceability(reqs)
    apply_runtime_traceability(reqs, tagged_rows)
    _model_docx_files, model_doc_files = apply_model_traceability(reqs)

    rows = [to_row(reqs[k]) for k in sorted(reqs.keys(), key=slug_sort_key)]
    write_csv(rows)
    write_markdown(rows)
    write_xlsx(rows)
    write_open_questions(rows, model_doc_files)

    print(f"CSV:  {CSV_OUT}")
    print(f"MD:   {MD_OUT}")
    print(f"XLSX: {XLSX_OUT}")
    print(f"Q:    {OPEN_Q_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
