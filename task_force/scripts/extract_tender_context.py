#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from difflib import SequenceMatcher
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from openpyxl import Workbook

try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover
    PdfReader = None  # type: ignore


DOC_EXTENSIONS = {".pdf", ".docx"}
EXCLUDE_DIR_TOKENS = {"debug"}
TENDER_ID_RE = re.compile(r"(?<!\d)(\d{5})[-/](\d{4})(?!\d)")
HEADING_LINE_RE = re.compile(r"^\s*(\d+(?:\.\d+){0,3})\.?\s*(.*)$")

KEYWORDS = [
    "\u0443\u0441\u043b\u043e\u0432",
    "\u0443\u0441\u043b\u043e\u0432\u0438",
    "\u0434\u043e\u043a\u0430\u0437",
    "\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442",
    "\u043a\u0440\u0438\u0442\u0435\u0440\u0438\u0443\u043c",
    "\u043f\u043e\u043d\u0443\u0434\u0443\u0432\u0430\u0447",
    "\u0435\u043a\u043e\u043d\u043e\u043c\u0441\u043a\u0438 \u043e\u043f\u0435\u0440\u0430\u0442\u043e\u0440",
    "\u0438\u0437\u0458\u0430\u0432\u0430",
    "\u0433\u0430\u0440\u0430\u043d\u0446\u0438\u0458\u0430",
    "\u0442\u0435\u0445\u043d\u0438\u0447\u043a\u0430 \u043f\u043e\u043d\u0443\u0434\u0430",
]

UPLOAD_DOC_HINTS = [
    ("\u0431\u0430\u043d\u043a\u0430\u0440\u0441\u043a\u0430 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u0458\u0430", "bank_guarantee"),
    ("\u0438\u0437\u0458\u0430\u0432\u0430", "declaration_statement"),
    ("\u0441\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442", "certificate"),
    ("\u043b\u0438\u0446\u0435\u043d\u0446\u0430", "license"),
    ("\u0442\u0435\u0445\u043d\u0438\u0447\u043a\u0430 \u043f\u043e\u043d\u0443\u0434\u0430", "technical_offer"),
    ("\u0444\u0438\u043d\u0430\u043d\u0441\u0438\u0441\u043a\u0430 \u043f\u043e\u043d\u0443\u0434\u0430", "financial_offer"),
    ("\u0440\u0435\u0444\u0435\u0440\u0435\u043d\u0442\u043d\u0430 \u043b\u0438\u0441\u0442\u0430", "reference_list"),
    ("\u0434\u043e\u043a\u0430\u0437 \u0437\u0430", "proof_document"),
]

# Union of sections requested by user across tenders.
TARGET_SECTIONS = [
    "1.3",
    "1.5",
    "1.6.1",
    "1.6.1.1",
    "3.4",
    "3.9",
    "3.10",
    "4",
    "4.2",
    "4.2.4",
    "4.3",
    "4.3.1",
    "4.3.2",
    "4.4",
    "5",
    "5.1",
    "5.2",
    "5.3",
    "6",
    "6.1",
]

MANUAL_REVIEW_FLAG = "\u041f\u0440\u043e\u0432\u0435\u0440\u0438 \u0440\u0430\u0447\u043d\u043e"
MAX_HIDDEN_TECH_SPEC_ITEMS = 10
INSTITUTION_BLOCKLIST = (
    "\u043c\u0438\u043d\u0438\u0441\u0442\u0435\u0440\u0441\u0442\u0432\u043e\u0442\u043e \u0437\u0430 \u0444\u0438\u043d\u0430\u043d\u0441\u0438\u0438",
    "\u0443\u0458\u043f",
    "\u0443\u043f\u0440\u0430\u0432\u0430 \u0437\u0430 \u0458\u0430\u0432\u043d\u0438 \u043f\u0440\u0438\u0445\u043e\u0434\u0438",
    "\u0434\u0430\u043d\u043e\u0446\u0438",
)
W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


@dataclass
class ParsedFile:
    path: Path
    kind: str
    text: str
    pages: list[str]
    tender_id: str | None
    hit_count: int
    hits: list[dict[str, Any]]
    upload_hints: list[dict[str, str]]


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_docx_text(path: Path) -> str:
    chunks: list[str] = []
    with zipfile.ZipFile(path, "r") as zf:
        xml_names = [n for n in zf.namelist() if n.startswith("word/") and n.endswith(".xml")]
        for name in xml_names:
            if not any(k in name for k in ("document.xml", "header", "footer")):
                continue
            root = ET.fromstring(zf.read(name))
            texts = [node.text or "" for node in root.findall(".//{*}t")]
            merged = " ".join(t.strip() for t in texts if t and t.strip())
            if merged:
                chunks.append(merged)
    return normalize_text("\n\n".join(chunks))


def extract_pdf_text(path: Path) -> tuple[str, list[str]]:
    if PdfReader is None:
        return "", []
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(normalize_text(page.extract_text() or ""))
    return normalize_text("\n\n".join(pages)), pages


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def score_filename(path: Path) -> int:
    name = path.name.lower()
    score = 0
    if "\u0442\u0435\u043d\u0434\u0435\u0440" in name:
        score += 6
    if "\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0446" in name:
        score += 6
    if "\u0442\u0435\u0445\u043d\u0438\u0447\u043a\u0430 \u0441\u043f\u0435\u0446\u0438\u0444\u0438\u043a\u0430\u0446" in name:
        score += 5
    if "\u0442\u0435\u0445\u043d\u0438\u0447\u043a\u0430" in name:
        score += 3
    if "\u0443\u0441\u043b\u043e\u0432" in name:
        score += 4
    if path.suffix.lower() == ".pdf":
        score += 1
    return score


def collect_candidates(input_dir: Path) -> list[Path]:
    files: list[Path] = []
    for p in input_dir.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in DOC_EXTENSIONS:
            continue
        if any(tok in {part.lower() for part in p.parts} for tok in EXCLUDE_DIR_TOKENS):
            continue
        files.append(p)
    files.sort(key=lambda x: (score_filename(x), x.stat().st_mtime), reverse=True)
    return files


def find_hits(paragraphs: list[str], pages: list[str] | None = None) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for para in paragraphs:
        low = para.lower()
        for kw in KEYWORDS:
            if kw in low:
                page_no: int | None = None
                if pages:
                    for idx, pg in enumerate(pages, start=1):
                        if para[:80] and para[:80] in pg:
                            page_no = idx
                            break
                hits.append({"keyword": kw, "page": page_no, "snippet": para[:500]})
                break
    return hits


def build_upload_hints(hits: list[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for hit in hits:
        txt = (hit.get("snippet") or "").lower()
        for term, tag in UPLOAD_DOC_HINTS:
            if term in txt:
                out.append(
                    {
                        "tag": tag,
                        "term": term,
                        "source_page": str(hit.get("page") or ""),
                        "snippet": (hit.get("snippet") or "")[:220],
                    }
                )
    unique: dict[tuple[str, str], dict[str, str]] = {}
    for item in out:
        unique[(item["tag"], item["snippet"])] = item
    return list(unique.values())


def detect_tender_id(path: Path, text: str) -> str | None:
    m = TENDER_ID_RE.search(path.name)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = TENDER_ID_RE.search(text[:3000])
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return None


def is_toc_like_line(line: str) -> bool:
    txt = (line or "").strip()
    if not txt:
        return False
    if re.search(r"\.{4,}", txt):
        return True
    if re.search(r"\.{2,}\s*\d{1,3}\s*$", txt):
        return True
    return False


def extract_target_sections(text: str) -> dict[str, dict[str, str]]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    headings: list[tuple[int, str, str]] = []
    for idx, line in enumerate(lines):
        m = HEADING_LINE_RE.match(line)
        if not m:
            continue
        sec = m.group(1)
        rest = m.group(2).strip()
        headings.append((idx, sec, rest))

    by_sec: dict[str, list[int]] = {}
    for idx, sec, _ in headings:
        if sec in TARGET_SECTIONS:
            by_sec.setdefault(sec, []).append(idx)

    chosen_idx_by_sec: dict[str, int] = {}
    for sec in TARGET_SECTIONS:
        candidates = by_sec.get(sec, [])
        if not candidates:
            continue
        chosen: int | None = None
        for idx in candidates:
            line = lines[idx]
            if is_toc_like_line(line):
                continue
            window = " ".join(lines[idx : min(len(lines), idx + 4)]).lower()
            if is_toc_like_line(window):
                continue
            chosen = idx
            break
        if chosen is None:
            chosen = candidates[0]
        chosen_idx_by_sec[sec] = chosen

    heading_idx_lookup = {idx: sec for idx, sec, _ in headings}
    sorted_targets = sorted(((idx, sec) for sec, idx in chosen_idx_by_sec.items()), key=lambda x: x[0])
    out: dict[str, dict[str, str]] = {}
    for idx, sec in sorted_targets:
        next_idx = len(lines)
        for probe in range(idx + 1, len(lines)):
            if probe in heading_idx_lookup:
                next_idx = probe
                break
        block = lines[idx:next_idx]
        if not block:
            continue
        heading = block[0]
        body_lines = block[1:] if len(block) > 1 else block
        body = "\n".join(body_lines) if body_lines else heading
        out[sec] = {"heading": heading, "text": body[:6000]}
    return out


def extract_bullet_documents(section_text: str) -> list[str]:
    lines = [ln.strip() for ln in section_text.splitlines() if ln.strip()]
    marker_re = re.compile(r"^(?:[-\u2022\u25aa\u25cf\u2023\uf0ad\u25cf\uf0b7\uf0ad]|ï€­)\s*(.+)$")
    bullets: list[str] = []
    current = ""
    for line in lines:
        m = marker_re.match(line)
        if m:
            if current:
                bullets.append(normalize_text(current))
            current = m.group(1).strip()
            continue
        if current:
            current = f"{current} {line}"
    if current:
        bullets.append(normalize_text(current))

    cleaned: list[str] = []
    for b in bullets:
        low = b.lower()
        if any(k in low for k in ("\u043f\u043e\u0442\u0432\u0440\u0434\u0430", "\u0438\u0437\u0458\u0430\u0432\u0430", "\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442")):
            cleaned.append(b[:500])
    return cleaned


def build_requirements_template_rows(
    source_file: str,
    upload_rows: list[dict[str, str]],
    sections: dict[str, dict[str, str]],
    tech_spec_hits: list[dict[str, Any]],
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []

    for sec, payload in sections.items():
        out.append(
            {
                "requirement_id": f"REQ-SEC-{sec.replace('.', '-')}",
                "source_file": source_file,
                "category": "section_extract",
                "hint_tag": "section_extract",
                "section_code": sec,
                "section_heading": payload["heading"][:240],
                "requirement_text": payload["text"][:2400],
                "evidence_expected": "review_section_content",
                "mandatory": "yes",
                "source_pages": "",
                "snippet": payload["text"][:280],
                "status": "draft_from_target_section",
            }
        )

    if "4.2.4" in sections:
        docs = extract_bullet_documents(sections["4.2.4"]["text"])
        for i, doc_line in enumerate(docs, start=1):
            out.append(
                {
                    "requirement_id": f"REQ-EXCL-DOC-{i:03d}",
                    "source_file": source_file,
                    "category": "exclusion_evidence",
                    "hint_tag": "proof_document",
                    "section_code": "4.2.4",
                    "section_heading": sections["4.2.4"]["heading"][:240],
                    "requirement_text": doc_line,
                    "evidence_expected": "explicit_supporting_document",
                    "mandatory": "yes",
                    "source_pages": "",
                    "snippet": doc_line[:280],
                    "status": "draft_from_target_section",
                }
            )

    for i, hit in enumerate(tech_spec_hits, start=1):
        out.append(
            {
                "requirement_id": f"REQ-TECHSPEC-HIDDEN-{i:03d}",
                "source_file": source_file,
                "category": "technical_spec_hidden_conditions",
                "hint_tag": "hidden_uslovi",
                "section_code": "tech_spec",
                "section_heading": "\u0422\u0435\u0445\u043d\u0438\u0447\u043a\u0430 \u0441\u043f\u0435\u0446\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0458\u0430 - \u0441\u043a\u0440\u0438\u0435\u043d\u0438 \u0443\u0441\u043b\u043e\u0432\u0438",
                "requirement_text": hit.get("snippet", "")[:2400],
                "evidence_expected": "review_technical_specification",
                "mandatory": "yes",
                "source_pages": str(hit.get("page") or ""),
                "snippet": hit.get("snippet", "")[:280],
                "status": "draft_from_technical_spec",
            }
        )

    for row in upload_rows:
        out.append(
            {
                "requirement_id": f"REQ-HINT-{re.sub(r'[^A-Za-z0-9]+', '-', row['tag']).strip('-').upper()}",
                "source_file": source_file,
                "category": "upload_hint",
                "hint_tag": row["tag"],
                "section_code": "",
                "section_heading": "",
                "requirement_text": f"Detected upload hint term '{row['term']}' in tender context.",
                "evidence_expected": row["tag"],
                "mandatory": "yes",
                "source_pages": row["source_page"],
                "snippet": row["snippet"][:280],
                "status": "draft_from_upload_hints",
            }
        )

    return out


def write_upload_hints_xlsx(rows: list[dict[str, str]], path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "upload_hints"
    ws.append(["file", "tag", "term", "source_page", "snippet"])
    for row in rows:
        ws.append([row["file"], row["tag"], row["term"], row["source_page"], row["snippet"]])
    wb.save(path)


def write_rows_xlsx(rows: list[dict[str, str]], path: Path, sheet_name: str) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]
    headers = list(rows[0].keys()) if rows else []
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h, "") for h in headers])
    wb.save(path)


def write_simple_checklist_docx(lines: list[str], path: Path) -> None:
    def paragraph_xml(text: str) -> str:
        clean = escape(text).replace("\n", " ")
        return (
            "<w:p><w:r><w:rPr><w:sz w:val=\"22\"/></w:rPr>"
            f"<w:t xml:space=\"preserve\">{clean}</w:t>"
            "</w:r></w:p>"
        )

    plain_lines: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            plain_lines.append("")
            continue
        if line.startswith("# "):
            plain_lines.append(line[2:].strip())
            continue
        if line.startswith("## "):
            plain_lines.append(line[3:].strip())
            continue
        if line.startswith("- [ ] "):
            plain_lines.append("â˜ " + line[6:].strip())
            continue
        if line.startswith("- "):
            plain_lines.append("â€¢ " + line[2:].strip())
            continue
        plain_lines.append(line)

    body = "".join(paragraph_xml(x if x else " ") for x in plain_lines)
    document_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:document xmlns:wpc=\"http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas\" "
        "xmlns:mc=\"http://schemas.openxmlformats.org/markup-compatibility/2006\" "
        "xmlns:o=\"urn:schemas-microsoft-com:office:office\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" "
        "xmlns:m=\"http://schemas.openxmlformats.org/officeDocument/2006/math\" "
        "xmlns:v=\"urn:schemas-microsoft-com:vml\" "
        "xmlns:wp14=\"http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing\" "
        "xmlns:wp=\"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing\" "
        "xmlns:w10=\"urn:schemas-microsoft-com:office:word\" "
        "xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\" "
        "xmlns:w14=\"http://schemas.microsoft.com/office/word/2010/wordml\" "
        "xmlns:wpg=\"http://schemas.microsoft.com/office/word/2010/wordprocessingGroup\" "
        "xmlns:wpi=\"http://schemas.microsoft.com/office/word/2010/wordprocessingInk\" "
        "xmlns:wne=\"http://schemas.microsoft.com/office/word/2006/wordml\" "
        "xmlns:wps=\"http://schemas.microsoft.com/office/word/2010/wordprocessingShape\" "
        "mc:Ignorable=\"w14 wp14\">"
        f"<w:body>{body}<w:sectPr><w:pgSz w:w=\"11906\" w:h=\"16838\"/><w:pgMar w:top=\"1440\" w:right=\"1440\" "
        "w:bottom=\"1440\" w:left=\"1440\" w:header=\"708\" w:footer=\"708\" w:gutter=\"0\"/>"
        "<w:cols w:space=\"708\"/><w:docGrid w:linePitch=\"360\"/></w:sectPr></w:body></w:document>"
    )
    content_types_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
        "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
        "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
        "<Override PartName=\"/word/document.xml\" "
        "ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>"
        "</Types>"
    )
    root_rels_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" "
        "Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" "
        "Target=\"word/document.xml\"/>"
        "</Relationships>"
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("_rels/.rels", root_rels_xml)
        zf.writestr("word/document.xml", document_xml)


def build_simple_checklist_lines(
    tender_id: str,
    main_source_file: str,
    sections: dict[str, dict[str, str]],
    req_rows: list[dict[str, str]],
) -> list[str]:
    lines = [
        f"# Upload Checklist - {tender_id}",
        "",
        f"Source tender file: `{main_source_file}`",
        "",
        "## Key Tender Sections (\u0443\u0441\u043b\u043e\u0432\u0438)",
    ]
    for sec in sorted(sections.keys(), key=lambda s: [int(x) for x in s.split(".")]):
        heading = sections[sec]["heading"].strip()
        lines.append(f"- [ ] {sec} - {heading}")

    lines.extend(["", "## Required Evidence Documents"])
    evidence_rows = [r for r in req_rows if r.get("category") in {"exclusion_evidence"}]
    if evidence_rows:
        for row in evidence_rows:
            lines.append(f"- [ ] {row['requirement_text']}")
    else:
        lines.append("- [ ] No explicit exclusion evidence bullets extracted. Review section 4.2.4 manually.")

    lines.extend(["", "## Hidden Conditions (Technical Specification)"])
    hidden_rows = [r for r in req_rows if r.get("category") == "technical_spec_hidden_conditions"]
    if hidden_rows:
        for row in hidden_rows:
            src_page = row.get("source_pages", "").strip()
            page_note = f" (page {src_page})" if src_page else ""
            lines.append(f"- [ ] {row['snippet']}{page_note}")
    else:
        lines.append("- [ ] No hidden technical-spec conditions detected in this run.")

    lines.extend(
        [
            "",
            "## Final Control",
            "- [ ] All mandatory documents attached.",
            "- [ ] Conditional documents evaluated and attached where applicable.",
            "- [ ] Deadline and e-auction rules validated against tender sections.",
        ]
    )
    return lines


def build_simple_form_rows(req_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    relevant = [
        r
        for r in req_rows
        if r.get("category")
        in {"section_extract", "exclusion_evidence", "technical_spec_hidden_conditions"}
    ]
    for idx, row in enumerate(relevant, start=1):
        if row.get("category") == "section_extract":
            item_text = row.get("section_heading", "").strip()
        elif row.get("category") == "technical_spec_hidden_conditions":
            item_text = row.get("snippet", "").strip()
        else:
            item_text = row.get("requirement_text", "").strip()
        item_text = re.sub(r"\s+", " ", item_text)[:260]
        rows.append(
            {
                "item_no": str(idx),
                "section_code": row.get("section_code", ""),
                "requirement_id": row.get("requirement_id", ""),
                "checklist_item": item_text,
                "mandatory": row.get("mandatory", "yes"),
                "provided": "",
                "attached_file_name": "",
                "reviewer_comment": "",
            }
        )
    return rows


def write_simple_form_docx(rows: list[dict[str, str]], tender_id: str, path: Path) -> None:
    lines = [f"Upload Form - {tender_id}", ""]
    for row in rows:
        lines.append(
            f"â˜ [{row.get('item_no','')}] {row.get('section_code','')} {row.get('requirement_id','')} - {row.get('checklist_item','')}"
        )
        lines.append("    Provided: ________")
        lines.append("    Attached file: ________")
        lines.append("    Reviewer comment: ________")
        lines.append("")
    write_simple_checklist_docx(lines, path)


def compact_text(value: str, max_len: int = 520) -> str:
    txt = re.sub(r"\s+", " ", (value or "").strip())
    txt = re.sub(r"^\d+(?:\.\d+){0,3}\.?\s*", "", txt)
    if len(txt) <= max_len:
        return txt
    return txt[: max_len - 3].rstrip() + "..."


def pick_section_text(sections: dict[str, dict[str, str]], keys: list[str]) -> str:
    for key in keys:
        payload = sections.get(key)
        if payload and payload.get("text"):
            return payload["text"]
    return ""


def detect_institution_name(full_text: str) -> str:
    normalized = normalize_text(full_text)
    head = normalized[:8000]
    patterns = [
        r"(?:\u0434\u043e\u0433\u043e\u0432\u043e\u0440\u043d(?:\u0438\u043e\u0442)?\s+\u043e\u0440\u0433\u0430\u043d)\s*[:\-]\s*([^\n]{4,220})",
        r"(?:\u043d\u0430\u0437\u0438\u0432\s+\u043d\u0430\s+\u0434\u043e\u0433\u043e\u0432\u043e\u0440(?:\u043d\u0438\u043e\u0442)?\s+\u043e\u0440\u0433\u0430\u043d)\s*[:\-]\s*([^\n]{4,220})",
    ]
    for pat in patterns:
        m = re.search(pat, head, flags=re.IGNORECASE)
        if not m:
            continue
        candidate = compact_text(m.group(1), 180)
        low = candidate.lower()
        if (
            "\u0447\u0438\u0458 \u043f\u0440\u0435\u0434\u043c\u0435\u0442" in low
            or "\u0435\u043a\u043e\u043d\u043e\u043c\u0441\u043a\u0438 \u043e\u043f\u0435\u0440\u0430\u0442\u043e\u0440" in low
            or "\u045c\u0435 " in low
            or " \u0441\u0435 " in low
            or "\u0437\u0430 \u0434\u0430\u043d\u043e\u0446\u0438\u0442\u0435" in low
            or "\u043c\u0438\u043d\u0438\u0441\u0442\u0435\u0440\u0441\u0442\u0432\u043e\u0442\u043e \u0437\u0430 \u0444\u0438\u043d\u0430\u043d\u0441\u0438\u0438" in low
            or len(candidate.split()) < 2
        ):
            continue
        return candidate

    m = re.search(
        r"\u0442\u0435\u043d\u0434\u0435\u0440\u0441\u043a\u0430\s+\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0446\u0438\u0458\u0430.{0,180}?\u0437\u0430\s+(.{6,180}?)\s+\u0441\u043e\s+\u0431\u0440\u043e\u0458\s+\u043d\u0430\s+\u043e\u0433\u043b\u0430\u0441",
        head,
        flags=re.IGNORECASE,
    )
    if m:
        return compact_text(m.group(1), 180)

    m = re.search(
        r"\u0443\u0441\u043b\u0443\u0433\u0438\s+\u043e\u0434\s+\u0438\u043d\u0442\u0435\u0440\u043d\u0435\u0442\s+\u0437\u0430\s+([^,\\n]{3,120})",
        normalized,
        re.IGNORECASE,
    )
    if m:
        candidate = re.split(
            r"\s+\u0441\u043e\s+\u0431\u0440\u043e\u0458\s+\u043d\u0430\s+\u043e\u0433\u043b\u0430\u0441",
            m.group(1),
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        return compact_text(candidate, 180)

    m = re.search(
        r"\b(\u043c\u0438\u043d\u0438\u0441\u0442\u0435\u0440\u0441\u0442\u0432\u043e[^\n]{3,140}|\u043e\u043f\u0448\u0442\u0438\u043d\u0430[^\n]{3,140}|\u0441\u0443\u0434[^\n]{3,140})",
        normalized,
        re.IGNORECASE,
    )
    if m:
        return compact_text(m.group(1), 180)
    return "\u041d\u0435 \u0435 \u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0441\u043a\u0438 \u0434\u0435\u0442\u0435\u043a\u0442\u0438\u0440\u0430\u043d\u043e (\u043f\u0440\u043e\u0432\u0435\u0440\u0438 \u0442\u0435\u043d\u0434\u0435\u0440\u0441\u043a\u0430 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0446\u0438\u0458\u0430)."


def detect_procedure_type(section_15_text: str) -> str:
    low = section_15_text.lower()
    if "поедноставена отворена постапка" in low:
        return "Поедноставена отворена постапка"
    if "отворена постапка" in low:
        return "Отворена постапка"
    if "постапка од мала вредност" in low or "набавка од мала вредност" in low:
        return "Набавка од мала вредност"
    return compact_text(section_15_text, 180) or "Провери дел 1.5."


def detect_procedure_type_from_full_text(full_text: str, section_15_text: str) -> str:
    merged = f"{full_text[:12000]} {section_15_text}".lower()
    if "поедноставена отворена постапка" in merged:
        return "Поедноставена отворена постапка"
    if "отворена постапка" in merged:
        return "Отворена постапка"
    if "набавка од мала вредност" in merged or "постапка од мала вредност" in merged:
        return "Набавка од мала вредност"
    if "конкурентна постапка" in merged:
        return "Конкурентна постапка"
    return detect_procedure_type(section_15_text)


def detect_subject_from_full_text(full_text: str) -> str:
    normalized = normalize_text(full_text)[:16000]
    patterns = [
        r"предмет\s+на\s+постапката[^\n]{0,180}",
        r"предмет\s+на\s+набавката[^\n]{0,180}",
        r"предмет\s+на\s+договор[^\n]{0,180}",
    ]
    for pat in patterns:
        m = re.search(pat, normalized, flags=re.IGNORECASE)
        if not m:
            continue
        candidate = first_sentence(m.group(0), 220)
        low = candidate.lower()
        if "корупц" in low or "општи мерки" in low or "набавка" not in low:
            continue
        return candidate
    return ""


def pick_section_text_with_keywords(
    sections: dict[str, dict[str, str]],
    keys: list[str],
    keywords: list[str],
) -> str:
    for key in keys:
        payload = sections.get(key)
        if not payload:
            continue
        txt = payload.get("text", "")
        low = txt.lower()
        if any(kw in low for kw in keywords):
            return txt
    return pick_section_text(sections, keys)


def build_elegant_context_lines(
    tender_id: str,
    main_source_file: str,
    full_text: str,
    sections: dict[str, dict[str, str]],
    tech_spec_hits: list[dict[str, Any]],
) -> list[str]:
    sec_13 = pick_section_text_with_keywords(sections, ["1.3"], ["Ð¿Ñ€ÐµÐ´Ð¼ÐµÑ‚", "Ð½Ð°Ð±Ð°Ð²ÐºÐ°"])
    sec_15 = pick_section_text_with_keywords(sections, ["1.5"], ["Ð¿Ð¾ÑÑ‚Ð°Ð¿ÐºÐ°", "Ð¾Ñ‚Ð²Ð¾Ñ€ÐµÐ½Ð°"])
    sec_161 = pick_section_text_with_keywords(sections, ["1.6.1"], ["Ð°ÑƒÐºÑ†Ð¸Ñ˜Ð°", "ÐµÐ»ÐµÐºÑ‚Ñ€Ð¾Ð½ÑÐºÐ°"])
    sec_34 = pick_section_text_with_keywords(sections, ["3.4"], ["Ñ†ÐµÐ½Ð°", "Ð¿Ð¾Ð½ÑƒÐ´Ð°"])
    sec_310 = pick_section_text_with_keywords(
        sections, ["3.10", "4.3"], ["ÑÐ¾Ð´Ñ€Ð¶Ð¸Ð½Ð° Ð½Ð° Ð¿Ð¾Ð½ÑƒÐ´Ð°Ñ‚Ð°", "ÐµÐ»ÐµÐ¼ÐµÐ½Ñ‚Ð¸", "Ñ„Ð¸Ð½Ð°Ð½ÑÐ¸ÑÐºÐ° Ð¿Ð¾Ð½ÑƒÐ´Ð°"]
    )
    sec_51 = pick_section_text_with_keywords(
        sections, ["5.1", "4.1"], ["ÐºÑ€Ð¸Ñ‚ÐµÑ€Ð¸ÑƒÐ¼Ð¸", "ÑƒÑ‚Ð²Ñ€Ð´ÑƒÐ²Ð°ÑšÐµ ÑÐ¿Ð¾ÑÐ¾Ð±Ð½Ð¾ÑÑ‚", "ÑÐ¿Ð¾ÑÐ¾Ð±Ð½Ð¾ÑÑ‚"]
    )
    sec_42 = pick_section_text_with_keywords(
        sections, ["4.2", "5.2"], ["Ð¿Ñ€Ð¸Ñ‡Ð¸Ð½Ð¸ Ð·Ð° Ð¸ÑÐºÐ»ÑƒÑ‡ÑƒÐ²Ð°ÑšÐµ", "Ð¸ÑÐºÐ»ÑƒÑ‡ÑƒÐ²Ð°ÑšÐµ"]
    )
    sec_43 = pick_section_text_with_keywords(
        sections, ["4.3", "5.3"], ["ÐºÐ²Ð°Ð»Ð¸Ñ‚Ð°Ñ‚Ð¸Ð²ÐµÐ½ Ð¸Ð·Ð±Ð¾Ñ€", "ÑƒÑÐ»Ð¾Ð²Ð¸"]
    )
    sec_432 = pick_section_text_with_keywords(
        sections, ["4.3.2", "5.3.2"], ["Ñ‚ÐµÑ…Ð½Ð¸Ñ‡ÐºÐ°", "Ð¿Ñ€Ð¾Ñ„ÐµÑÐ¸Ð¾Ð½Ð°Ð»Ð½Ð° ÑÐ¿Ð¾ÑÐ¾Ð±Ð½Ð¾ÑÑ‚"]
    )
    sec_44 = pick_section_text_with_keywords(
        sections, ["4.4", "5.4"], ["ÑÑ‚Ð°Ð½Ð´Ð°Ñ€Ð´Ð¸", "ÐºÐ²Ð°Ð»Ð¸Ñ‚ÐµÑ‚", "iso"]
    )
    sec_best = pick_section_text_with_keywords(
        sections, ["5.4", "5"], ["ÐºÑ€Ð¸Ñ‚ÐµÑ€Ð¸ÑƒÐ¼ Ð·Ð° Ð¸Ð·Ð±Ð¾Ñ€", "Ð½Ð°Ñ˜Ð¿Ð¾Ð²Ð¾Ð»Ð½Ð° Ð¿Ð¾Ð½ÑƒÐ´Ð°", "ÐºÑ€Ð¸Ñ‚ÐµÑ€Ð¸ÑƒÐ¼"]
    )

    auction_note = compact_text(sec_161, 260) if sec_161 else "ÐÐµÐ¼Ð° ÐµÐºÑÐ¿Ð»Ð¸Ñ†Ð¸Ñ‚Ð½Ð¾ Ð¿Ñ€Ð¾Ð½Ð°Ñ˜Ð´ÐµÐ½ Ð´ÐµÐ» 1.6.1."
    quality_note = compact_text(sec_44, 260) if sec_44 else "ÐÐµÐ¼Ð° ÐµÐºÑÐ¿Ð»Ð¸Ñ†Ð¸Ñ‚Ð½Ð¾ Ð¿Ñ€Ð¾Ð½Ð°Ñ˜Ð´ÐµÐ½Ð¸ ÑÑ‚Ð°Ð½Ð´Ð°Ñ€Ð´Ð¸."

    lines = [
        f"# ÐšÐ¾Ð½Ñ‚ÐµÐºÑÑ‚ Ð·Ð° upload - {tender_id}",
        "",
        f"Ð˜Ð·Ð²Ð¾Ñ€: `{main_source_file}`",
        "",
        f"**Ð˜Ð¼Ðµ Ð½Ð° Ð¸Ð½ÑÑ‚Ð¸Ñ‚ÑƒÑ†Ð¸Ñ˜Ð°:** {detect_institution_name(full_text)}",
        f"**Ð¢Ð¸Ð¿ Ð½Ð° Ð¿Ð¾ÑÑ‚Ð°Ð¿ÐºÐ°:** {detect_procedure_type_from_full_text(full_text, sec_15)}",
        f"**ÐŸÑ€ÐµÐ´Ð¼ÐµÑ‚ Ð½Ð° Ð½Ð°Ð±Ð°Ð²ÐºÐ°:** {compact_text(sec_13, 260) or 'ÐŸÑ€Ð¾Ð²ÐµÑ€Ð¸ Ð´ÐµÐ» 1.3.'}",
        f"**ÐŸÐ¾ÑÐµÐ±Ð½Ð¸ Ð½Ð°Ñ‡Ð¸Ð½Ð¸ Ð·Ð° Ð´Ð¾Ð´ÐµÐ»ÑƒÐ²Ð°ÑšÐµ Ð½Ð° Ð´Ð¾Ð³Ð¾Ð²Ð¾Ñ€Ð¾Ñ‚ Ð·Ð° Ñ˜Ð°Ð²Ð½Ð° Ð½Ð°Ð±Ð°Ð²ÐºÐ°:** {auction_note}",
        f"**Ð¦ÐµÐ½Ð° Ð½Ð° Ð¿Ð¾Ð½ÑƒÐ´Ð°Ñ‚Ð°:** {compact_text(sec_34, 260) or 'ÐŸÑ€Ð¾Ð²ÐµÑ€Ð¸ Ð´ÐµÐ» 3.4.'}",
        f"**Ð•Ð»ÐµÐ¼ÐµÐ½Ñ‚Ð¸ Ð½Ð° Ð¿Ð¾Ð½ÑƒÐ´Ð°Ñ‚Ð°:** {compact_text(sec_310, 260) or 'ÐŸÑ€Ð¾Ð²ÐµÑ€Ð¸ Ð´ÐµÐ» 3.10 / 4.3.'}",
        f"**ÐšÑ€Ð¸Ñ‚ÐµÑ€Ð¸ÑƒÐ¼Ð¸ Ð·Ð° ÑƒÑ‚Ð²Ñ€Ð´ÑƒÐ²Ð°ÑšÐµ Ð½Ð° ÑÐ¿Ð¾ÑÐ¾Ð±Ð½Ð¾ÑÑ‚ Ð½Ð° Ð¿Ð¾Ð½ÑƒÐ´ÑƒÐ²Ð°Ñ‡Ð¸Ñ‚Ðµ:** {compact_text(sec_51, 260) or 'ÐŸÑ€Ð¾Ð²ÐµÑ€Ð¸ Ð´ÐµÐ» 5.1 / 4.1.'}",
        f"**ÐŸÑ€Ð¸Ñ‡Ð¸Ð½Ð¸ Ð·Ð° Ð¸ÑÐºÐ»ÑƒÑ‡ÑƒÐ²Ð°ÑšÐµ Ð¾Ð´ Ð¿Ð¾ÑÑ‚Ð°Ð¿ÐºÐ°Ñ‚Ð°:** {compact_text(sec_42, 260) or 'ÐŸÑ€Ð¾Ð²ÐµÑ€Ð¸ Ð´ÐµÐ» 4.2 / 5.2.'}",
        f"**Ð£ÑÐ»Ð¾Ð²Ð¸ Ð·Ð° ÐºÐ²Ð°Ð»Ð¸Ñ‚Ð°Ñ‚Ð¸Ð²ÐµÐ½ Ð¸Ð·Ð±Ð¾Ñ€:** {compact_text(sec_43, 260) or 'ÐŸÑ€Ð¾Ð²ÐµÑ€Ð¸ Ð´ÐµÐ» 4.3 / 5.3.'}",
        f"**Ð¢ÐµÑ…Ð½Ð¸Ñ‡ÐºÐ° Ð¸ Ð¿Ñ€Ð¾Ñ„ÐµÑÐ¸Ð¾Ð½Ð°Ð»Ð½Ð° ÑÐ¿Ð¾ÑÐ¾Ð±Ð½Ð¾ÑÑ‚:** {compact_text(sec_432, 260) or 'ÐŸÑ€Ð¾Ð²ÐµÑ€Ð¸ Ð´ÐµÐ» 4.3.2 / 5.3.2.'}",
        f"**Ð¡Ñ‚Ð°Ð½Ð´Ð°Ñ€Ð´Ð¸ Ð·Ð° ÑÐ¸ÑÑ‚ÐµÐ¼Ð¸ Ð·Ð° ÐºÐ²Ð°Ð»Ð¸Ñ‚ÐµÑ‚:** {quality_note}",
        f"**ÐšÐ Ð˜Ð¢Ð•Ð Ð˜Ð£Ðœ Ð—Ð Ð˜Ð—Ð‘ÐžÐ  ÐÐ ÐÐÐˆÐŸÐžÐ’ÐžÐ›ÐÐ ÐŸÐžÐÐ£Ð”Ð:** {compact_text(sec_best, 220) or 'ÐŸÑ€Ð¾Ð²ÐµÑ€Ð¸ Ð´ÐµÐ» Ð·Ð° ÐºÑ€Ð¸Ñ‚ÐµÑ€Ð¸ÑƒÐ¼.'}",
        "",
        "## Ð”Ð¾Ð¿Ð¾Ð»Ð½Ð¸Ñ‚ÐµÐ»Ð½Ð¾ Ð¾Ð´ Ð¢ÐµÑ…Ð½Ð¸Ñ‡ÐºÐ° ÑÐ¿ÐµÑ†Ð¸Ñ„Ð¸ÐºÐ°Ñ†Ð¸Ñ˜Ð°",
    ]
    if tech_spec_hits:
        for i, hit in enumerate(tech_spec_hits[:10], start=1):
            page = str(hit.get("page") or "").strip()
            suffix = f" (ÑÑ‚Ñ€. {page})" if page else ""
            lines.append(f"- {i}. {compact_text(hit.get('snippet', ''), 220)}{suffix}")
    else:
        lines.append("- ÐÐµÐ¼Ð° Ð´ÐµÑ‚ÐµÐºÑ‚Ð¸Ñ€Ð°Ð½Ð¸ Ð´Ð¾Ð¿Ð¾Ð»Ð½Ð¸Ñ‚ÐµÐ»Ð½Ð¸ ÑƒÑÐ»Ð¾Ð²Ð¸ Ð²Ð¾ Ñ‚ÐµÑ…Ð½Ð¸Ñ‡ÐºÐ°Ñ‚Ð° ÑÐ¿ÐµÑ†Ð¸Ñ„Ð¸ÐºÐ°Ñ†Ð¸Ñ˜Ð° Ð²Ð¾ Ð¾Ð²Ð°Ð° Ð¾Ð±Ñ€Ð°Ð±Ð¾Ñ‚ÐºÐ°.")
    return lines


def clean_summary_text(text: str) -> str:
    txt = normalize_csv_cell(text, max_len=1600)
    txt = re.sub(r"^[\-\u2022\u25aa\u25cf\uf0ad\uf0b7]+\s*", "", txt)
    txt = re.sub(r"^\d+(?:\.\d+){0,4}\.?\s*", "", txt)
    txt = re.sub(r"^[A-ZÐ-Ð¨0-9 ]{8,}$", "", txt).strip()
    return txt


def first_sentence(text: str, max_len: int = 220) -> str:
    txt = compact_text(clean_summary_text(text), max_len * 2)
    if not txt:
        return ""
    sentence = re.split(r"(?<=[\.\!\?])\s+", txt, maxsplit=1)[0].strip()
    sentence = re.sub(r"\s+", " ", sentence)
    return compact_text(sentence or txt, max_len)


def normalize_for_similarity(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\u0400-\u04FF]+", " ", (text or "").lower())
    return re.sub(r"\s+", " ", normalized).strip()


def pick_section_value(
    sections: dict[str, dict[str, str]],
    preferred_keys: list[str],
    keywords: list[str],
    fallback_note: str,
    max_len: int = 220,
    allow_section_only: bool = True,
    allow_semantic_fallback: bool = True,
) -> dict[str, str]:
    for key in preferred_keys:
        payload = sections.get(key)
        if not payload:
            continue
        txt = payload.get("text", "")
        heading = payload.get("heading", "")
        merged = f"{heading} {txt}"
        low = merged.lower()
        if keywords and any(kw in low for kw in keywords):
            return {
                "value": first_sentence(merged, max_len) or fallback_note,
                "confidence": "high",
                "source_section": key,
                "mapping": "semantic+section",
            }

    if allow_section_only:
        for key in preferred_keys:
            payload = sections.get(key)
            if payload and payload.get("text"):
                return {
                    "value": first_sentence(payload["text"], max_len) or fallback_note,
                    "confidence": "medium",
                    "source_section": key,
                    "mapping": "section_only",
                }

    if allow_semantic_fallback:
        for sec_code, payload in sections.items():
            txt = payload.get("text", "")
            heading = payload.get("heading", "")
            merged = f"{heading} {txt}"
            low = merged.lower()
            if keywords and any(kw in low for kw in keywords):
                return {
                    "value": first_sentence(merged, max_len) or fallback_note,
                    "confidence": "low",
                    "source_section": sec_code,
                    "mapping": "semantic_fallback",
                }

    return {
        "value": f"{MANUAL_REVIEW_FLAG} - {fallback_note}",
        "confidence": "low",
        "source_section": "",
        "mapping": "missing",
    }


def detect_institution_field(full_text: str) -> dict[str, str]:
    def trim_institution_name(raw: str) -> str:
        candidate = normalize_csv_cell(raw, max_len=220)
        candidate = re.split(r"\s*(?:,|;|\bÐ°Ð´Ñ€ÐµÑÐ°\b|\bÑ‚ÐµÐ»ÐµÑ„Ð¾Ð½\b|\bÐµÐ»ÐµÐºÑ‚Ñ€Ð¾Ð½ÑÐºÐ°\b)\s*", candidate, maxsplit=1)[0]
        candidate = re.sub(r"^[\-\u2022]+\s*", "", candidate).strip(" .,:;")
        return compact_text(candidate, 120)

    normalized = normalize_text(full_text)
    head = normalized[:8000]
    strong_patterns = [
        r"(?:\u0434\u043e\u0433\u043e\u0432\u043e\u0440\u043d(?:\u0438\u043e\u0442)?\s+\u043e\u0440\u0433\u0430\u043d)\s*[:\-]\s*([^\n]{4,220})",
        r"(?:\u043d\u0430\u0437\u0438\u0432\s+\u043d\u0430\s+\u0434\u043e\u0433\u043e\u0432\u043e\u0440(?:\u043d\u0438\u043e\u0442)?\s+\u043e\u0440\u0433\u0430\u043d)\s*[:\-]\s*([^\n]{4,220})",
    ]
    for pat in strong_patterns:
        m = re.search(pat, head, flags=re.IGNORECASE)
        if not m:
            continue
        candidate = trim_institution_name(m.group(1))
        low = candidate.lower()
        if (
            "\u0447\u0438\u0458 \u043f\u0440\u0435\u0434\u043c\u0435\u0442" in low
            or "\u0435\u043a\u043e\u043d\u043e\u043c\u0441\u043a\u0438 \u043e\u043f\u0435\u0440\u0430\u0442\u043e\u0440" in low
            or "\u045c\u0435 " in low
            or " \u0441\u0435 " in low
            or len(candidate.split()) < 2
            or any(bad in low for bad in INSTITUTION_BLOCKLIST)
        ):
            continue
        return {"value": candidate, "confidence": "high", "source_section": "header", "mapping": "explicit_label"}

    moderate_patterns = [
        r"\u0442\u0435\u043d\u0434\u0435\u0440\u0441\u043a\u0430\s+\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0446\u0438\u0458\u0430.{0,180}?\u0437\u0430\s+(.{6,180}?)\s+\u0441\u043e\s+\u0431\u0440\u043e\u0458\s+\u043d\u0430\s+\u043e\u0433\u043b\u0430\u0441",
        r"\b(\u043e\u043f\u0448\u0442\u0438\u043d\u0430[^\n]{3,120}|\u0458\u0430\u0432\u043d\u043e \u043f\u0440\u0435\u0442\u043f\u0440\u0438\u0458\u0430\u0442\u0438\u0435[^\n]{3,120}|\u0443\u043d\u0438\u0432\u0435\u0440\u0437\u0438\u0442\u0435\u0442[^\n]{3,120}|\u043a\u043b\u0438\u043d\u0438\u043a[^\n]{3,120}|\u043c\u0438\u043d\u0438\u0441\u0442\u0435\u0440\u0441\u0442\u0432\u043e[^\n]{3,120})",
    ]
    for pat in moderate_patterns:
        m = re.search(pat, head, flags=re.IGNORECASE)
        if not m:
            continue
        candidate = trim_institution_name(m.group(1))
        low = candidate.lower()
        if len(candidate.split()) < 2 or any(bad in low for bad in INSTITUTION_BLOCKLIST):
            continue
        return {"value": candidate, "confidence": "medium", "source_section": "header", "mapping": "pattern_fallback"}

    return {
        "value": f"{MANUAL_REVIEW_FLAG} - \u0438\u043d\u0441\u0442\u0438\u0442\u0443\u0446\u0438\u0458\u0430 \u043d\u0435 \u0435 \u0458\u0430\u0441\u043d\u043e \u0434\u0435\u0444\u0438\u043d\u0438\u0440\u0430\u043d\u0430.",
        "confidence": "low",
        "source_section": "",
        "mapping": "missing",
    }


def score_tech_spec_hit(hit: dict[str, Any]) -> int:
    snippet = str(hit.get("snippet", ""))
    low = snippet.lower()
    score = 0
    for kw in ("Ð¼Ð¾Ñ€Ð°", "Ð·Ð°Ð´Ð¾Ð»Ð¶", "Ð¸ÑÐºÐ»ÑƒÑ‡", "Ð´Ð¾ÐºÐ°Ð·", "ÑÐµÑ€Ñ‚Ð¸Ñ„Ð¸ÐºÐ°Ñ‚", "Ñ€Ð¾Ðº", "Ð³Ð°Ñ€Ð°Ð½"):
        if kw in low:
            score += 2
    score += min(3, max(0, len(snippet) // 120))
    if hit.get("page"):
        score += 1
    return score


def dedupe_top_tech_spec_hits(
    tech_spec_hits: list[dict[str, Any]], max_items: int = MAX_HIDDEN_TECH_SPEC_ITEMS
) -> list[dict[str, Any]]:
    ranked = sorted(tech_spec_hits, key=score_tech_spec_hit, reverse=True)
    kept: list[dict[str, Any]] = []
    fingerprints: list[str] = []
    for hit in ranked:
        fp = normalize_for_similarity(str(hit.get("snippet", "")))
        if len(fp) < 24:
            continue
        is_duplicate = False
        for seen in fingerprints:
            if fp == seen or SequenceMatcher(None, fp, seen).ratio() >= 0.88:
                is_duplicate = True
                break
        if is_duplicate:
            continue
        kept.append(hit)
        fingerprints.append(fp)
        if len(kept) >= max_items:
            break
    return kept


def build_context_fields(
    full_text: str,
    sections: dict[str, dict[str, str]],
    tech_spec_hits: list[dict[str, Any]],
) -> dict[str, dict[str, str]]:
    procedure_field = pick_section_value(
        sections,
        ["1.5"],
        ["постапка", "отворена"],
        "процедура (дел 1.5)",
        180,
        allow_semantic_fallback=False,
    )

    fields: dict[str, dict[str, str]] = {
        "institution_name": detect_institution_field(full_text),
        "procedure_type": {
            "value": first_sentence(detect_procedure_type_from_full_text(full_text, procedure_field["value"]), 180),
            "confidence": "high" if procedure_field["confidence"] != "low" else "medium",
            "source_section": procedure_field.get("source_section", ""),
            "mapping": "derived_from_procedure",
        },
        "subject_of_procurement": pick_section_value(
            sections,
            ["1.3"],
            ["предмет", "набавка"],
            "предмет на набавка (дел 1.3)",
            allow_semantic_fallback=False,
        ),
        "award_method_notes": pick_section_value(
            sections,
            ["1.6.1", "1.6.1.1"],
            ["аукција", "електронска", "доделув", "додели"],
            "доделување на договор (дел 1.6.1)",
            allow_section_only=False,
        ),
        "offer_price_notes": pick_section_value(
            sections,
            ["3.4"],
            ["цена", "понуда"],
            "цена на понуда (дел 3.4)",
            allow_semantic_fallback=False,
        ),
        "offer_elements": pick_section_value(
            sections,
            ["3.10", "4.3"],
            ["содржина на понудата", "елементи на понудата", "финансиска понуда", "техничка понуда"],
            "елементи на понудата (дел 3.10/4.3)",
            allow_section_only=False,
        ),
        "bidder_eligibility_criteria": pick_section_value(
            sections,
            ["5.1"],
            ["утврдување способност", "критериуми", "способност"],
            "способност на понудувач (дел 5.1)",
            allow_semantic_fallback=False,
        ),
        "exclusion_grounds": pick_section_value(
            sections,
            ["5.2", "4.2.4"],
            ["причини за исклучување", "исклучување", "основи за исклучување"],
            "причини за исклучување (дел 5.2)",
            allow_section_only=False,
            allow_semantic_fallback=False,
        ),
        "qualitative_selection_conditions": pick_section_value(
            sections,
            ["5.3"],
            ["квалитативен избор", "услови за квалитативен избор"],
            "квалитативен избор (дел 5.3)",
            allow_section_only=False,
            allow_semantic_fallback=False,
        ),
        "technical_professional_ability": pick_section_value(
            sections,
            ["5.3.2"],
            ["техничка и професионална способност", "техничка способност", "професионална способност"],
            "техничка/професионална способност (дел 5.3.2)",
            allow_section_only=False,
            allow_semantic_fallback=False,
        ),
        "quality_standards": pick_section_value(
            sections,
            ["5.3.3", "5.3"],
            ["стандард", "квалитет", "iso", "еквивалент"],
            "стандарди квалитет (дел 5.3)",
            allow_section_only=False,
        ),
        "best_offer_criterion": pick_section_value(
            sections,
            ["6.1", "5.4"],
            ["критериум за избор", "најповолна понуда", "економски најповолна", "најниска понудена цена"],
            "критериум за најповолна понуда",
            allow_section_only=False,
            allow_semantic_fallback=False,
        ),
    }

    subj = fields.get("subject_of_procurement", {})
    subj_value = str(subj.get("value", ""))
    if (not subj_value) or ("корупц" in subj_value.lower()) or ("општи мерки" in subj_value.lower()):
        inferred_subject = detect_subject_from_full_text(full_text)
        if inferred_subject:
            fields["subject_of_procurement"] = {
                "value": inferred_subject,
                "confidence": "medium",
                "source_section": "",
                "mapping": "full_text_subject_fallback",
            }
        else:
            fields["subject_of_procurement"] = {
                "value": f"{MANUAL_REVIEW_FLAG} - предмет на набавка",
                "confidence": "low",
                "source_section": "",
                "mapping": "subject_manual_review",
            }

    for field in fields.values():
        if field.get("confidence") == "low" and MANUAL_REVIEW_FLAG not in field.get("value", ""):
            field["value"] = f"{MANUAL_REVIEW_FLAG} - {field['value']}"

    fields["hidden_technical_conditions"] = {
        "value": str(len(tech_spec_hits)),
        "confidence": "high" if tech_spec_hits else "low",
        "source_section": "tech_spec",
        "mapping": "deduped_top_hits",
    }
    return fields


def build_elegant_context_lines_v2(
    tender_id: str,
    main_source_file: str,
    context_fields: dict[str, dict[str, str]],
    tech_spec_hits: list[dict[str, Any]],
) -> list[str]:
    def fmt_field(key: str) -> str:
        data = context_fields.get(key, {})
        value = data.get("value", f"{MANUAL_REVIEW_FLAG}.")
        conf = data.get("confidence", "low")
        src = data.get("source_section", "")
        src_note = f", source={src}" if src else ""
        return f"{value} [{conf}{src_note}]"

    lines = [
        f"# Context for upload - {tender_id}",
        "",
        f"Source: `{main_source_file}`",
        "",
        f"**Institution name:** {fmt_field('institution_name')}",
        f"**Procedure type:** {fmt_field('procedure_type')}",
        f"**Subject of procurement:** {fmt_field('subject_of_procurement')}",
        f"**Award method notes:** {fmt_field('award_method_notes')}",
        f"**Offer price notes:** {fmt_field('offer_price_notes')}",
        f"**Offer elements:** {fmt_field('offer_elements')}",
        f"**Bidder eligibility criteria:** {fmt_field('bidder_eligibility_criteria')}",
        f"**Exclusion grounds:** {fmt_field('exclusion_grounds')}",
        f"**Qualitative selection conditions:** {fmt_field('qualitative_selection_conditions')}",
        f"**Technical/professional ability:** {fmt_field('technical_professional_ability')}",
        f"**Quality standards:** {fmt_field('quality_standards')}",
        f"**Best offer criterion:** {fmt_field('best_offer_criterion')}",
        "",
        f"## Additional hidden conditions (top {MAX_HIDDEN_TECH_SPEC_ITEMS})",
    ]
    if tech_spec_hits:
        for i, hit in enumerate(tech_spec_hits[:MAX_HIDDEN_TECH_SPEC_ITEMS], start=1):
            page = str(hit.get("page") or "").strip()
            suffix = f" (page {page})" if page else ""
            lines.append(f"- {i}. {first_sentence(str(hit.get('snippet', '')), 220)}{suffix}")
    else:
        lines.append(f"- {MANUAL_REVIEW_FLAG} - no hidden technical conditions were detected in this run.")
    return lines


def normalize_csv_cell(value: Any, max_len: int = 2400) -> str:
    txt = str(value or "")
    txt = re.sub(r"[\r\n\t]+", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:max_len]


def sanitize_rows_for_csv(rows: list[dict[str, Any]], max_len: int = 2400) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        out.append({str(k): normalize_csv_cell(v, max_len=max_len) for k, v in row.items()})
    return out


def write_context_docx_from_template(
    template_path: Path,
    output_path: Path,
    context_fields: dict[str, dict[str, str]],
) -> bool:
    if not template_path.exists():
        return False

    ordered_fields = [
        "institution_name",
        "procedure_type",
        "subject_of_procurement",
        "award_method_notes",
        "offer_price_notes",
        "offer_elements",
        "bidder_eligibility_criteria",
        "exclusion_grounds",
        "qualitative_selection_conditions",
        "technical_professional_ability",
        "quality_standards",
        "best_offer_criterion",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(template_path, "r") as zin:
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    root = ET.fromstring(data)
                    rows = root.findall(f".//{W_NS}tr")
                    for idx, tr in enumerate(rows):
                        if idx >= len(ordered_fields):
                            break
                        tcs = tr.findall(f"{W_NS}tc")
                        if len(tcs) < 2:
                            continue
                        field_key = ordered_fields[idx]
                        value = normalize_csv_cell(
                            context_fields.get(field_key, {}).get("value", MANUAL_REVIEW_FLAG), max_len=520
                        )
                        right_tc = tcs[1]
                        paragraph = right_tc.find(f"{W_NS}p")
                        if paragraph is None:
                            paragraph = ET.SubElement(right_tc, f"{W_NS}p")
                        for node in list(paragraph):
                            paragraph.remove(node)
                        run = ET.SubElement(paragraph, f"{W_NS}r")
                        text = ET.SubElement(run, f"{W_NS}t")
                        text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                        text.text = value
                    data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                zout.writestr(item, data)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract per-tender context and upload template rows from tender documents."
    )
    parser.add_argument("--input-dir", default="downloads", help="Directory with downloaded tender docs.")
    parser.add_argument("--out-dir", default="task_force/out/tender_context", help="Output directory.")
    parser.add_argument("--max-files", type=int, default=20, help="Max files to process.")
    parser.add_argument("--tender-id", default="", help="Optional tender id filter, e.g. 09362-2025.")
    parser.add_argument(
        "--context-template",
        default="task_force/templates/context_template_v2.docx",
        help="DOCX template used for tender context export.",
    )
    args = parser.parse_args()

    root = Path.cwd()
    input_dir = (root / args.input_dir).resolve()
    out_dir = (root / args.out_dir).resolve()
    context_template_path = (root / args.context_template).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    files = collect_candidates(input_dir)[: max(1, args.max_files)]

    parsed: list[ParsedFile] = []
    for path in files:
        kind = path.suffix.lower().lstrip(".")
        try:
            if path.suffix.lower() == ".pdf":
                text, pages = extract_pdf_text(path)
            else:
                text = extract_docx_text(path)
                pages = []
            paragraphs = split_paragraphs(text)
            hits = find_hits(paragraphs, pages if pages else None)
            hints = build_upload_hints(hits)
            tender_id = detect_tender_id(path, text)
            parsed.append(
                ParsedFile(
                    path=path,
                    kind=kind,
                    text=text,
                    pages=pages,
                    tender_id=tender_id,
                    hit_count=len(hits),
                    hits=hits[:120],
                    upload_hints=hints[:120],
                )
            )
        except Exception:
            parsed.append(
                ParsedFile(
                    path=path,
                    kind=kind,
                    text="",
                    pages=[],
                    tender_id=None,
                    hit_count=0,
                    hits=[],
                    upload_hints=[],
                )
            )

    grouped: dict[str, list[ParsedFile]] = {}
    tender_docs = [
        p
        for p in parsed
        if p.tender_id and "\u0442\u0435\u043d\u0434\u0435\u0440\u0441\u043a\u0430_\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0446" in p.path.name.lower()
    ]
    for item in parsed:
        if item.tender_id:
            continue
        is_tech_spec = "\u0442\u0435\u0445\u043d\u0438\u0447\u043a\u0430 \u0441\u043f\u0435\u0446\u0438\u0444\u0438\u043a\u0430\u0446" in item.path.name.lower()
        if not is_tech_spec:
            continue
        if args.tender_id:
            item.tender_id = args.tender_id
            continue
        if not tender_docs:
            continue
        nearest = min(
            tender_docs,
            key=lambda td: abs(td.path.stat().st_mtime - item.path.stat().st_mtime),
        )
        # Keep assignment conservative for files downloaded in the same window.
        if abs(nearest.path.stat().st_mtime - item.path.stat().st_mtime) <= 12 * 3600:
            item.tender_id = nearest.tender_id

    for item in parsed:
        if not item.tender_id:
            continue
        if args.tender_id and item.tender_id != args.tender_id:
            continue
        grouped.setdefault(item.tender_id, []).append(item)

    outputs: list[dict[str, str]] = []
    for tender_id, group_files in sorted(grouped.items()):
        group_files.sort(key=lambda x: (score_filename(x.path), x.path.stat().st_mtime), reverse=True)
        main_doc = group_files[0]

        sections = extract_target_sections(main_doc.text)
        tech_spec_hits: list[dict[str, Any]] = []
        upload_rows: list[dict[str, str]] = []
        file_records: list[dict[str, Any]] = []

        for item in group_files:
            is_tech_spec = "\u0442\u0435\u0445\u043d\u0438\u0447\u043a\u0430 \u0441\u043f\u0435\u0446\u0438\u0444\u0438\u043a\u0430\u0446" in item.path.name.lower()
            if is_tech_spec:
                tech_spec_hits.extend(item.hits[:40])
            for hint in item.upload_hints:
                upload_rows.append(
                    {
                        "file": item.path.name,
                        "tag": hint["tag"],
                        "term": hint["term"],
                        "source_page": hint["source_page"],
                        "snippet": hint["snippet"],
                    }
                )
            file_records.append(
                {
                    "file": str(item.path),
                    "kind": item.kind,
                    "status": "ok" if item.text else "error_or_empty",
                    "hit_count": item.hit_count,
                    "upload_hints": item.upload_hints,
                }
            )

        deduped_tech_spec_hits = dedupe_top_tech_spec_hits(tech_spec_hits, MAX_HIDDEN_TECH_SPEC_ITEMS)
        context_fields = build_context_fields(
            full_text=main_doc.text,
            sections=sections,
            tech_spec_hits=deduped_tech_spec_hits,
        )
        payload = {
            "generated_at_utc": stamp,
            "tender_id": tender_id,
            "main_source_file": str(main_doc.path),
            "processed_files": len(group_files),
            "pdf_reader_available": PdfReader is not None,
            "target_sections": sections,
            "context_fields": context_fields,
            "confidence_summary": {
                level: sum(1 for item in context_fields.values() if item.get("confidence") == level)
                for level in ("high", "medium", "low")
            },
            "files": file_records,
        }

        tender_slug = tender_id.replace("-", "_")
        json_path = out_dir / f"tender_context_{tender_slug}_{stamp}.json"
        md_path = out_dir / f"tender_context_{tender_slug}_{stamp}.md"
        context_docx_path = out_dir / f"tender_context_{tender_slug}_{stamp}.docx"
        csv_path = out_dir / f"upload_hints_{tender_slug}_{stamp}.csv"
        xlsx_path = out_dir / f"upload_hints_{tender_slug}_{stamp}.xlsx"
        requirements_path = out_dir / f"upload_requirements_template_{tender_slug}_{stamp}.csv"
        checklist_path = out_dir / f"simple_checklist_{tender_slug}_{stamp}.md"
        checklist_docx_path = out_dir / f"simple_checklist_{tender_slug}_{stamp}.docx"
        form_docx_path = out_dir / f"simple_form_{tender_slug}_{stamp}.docx"

        safe_upload_rows = sanitize_rows_for_csv(upload_rows, max_len=600)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["file", "tag", "term", "source_page", "snippet"])
            writer.writeheader()
            writer.writerows(safe_upload_rows)
        write_upload_hints_xlsx(upload_rows, xlsx_path)

        req_rows = build_requirements_template_rows(main_doc.path.name, upload_rows, sections, deduped_tech_spec_hits)
        safe_req_rows = sanitize_rows_for_csv(req_rows, max_len=2400)
        with requirements_path.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=[
                    "requirement_id",
                    "source_file",
                    "category",
                    "hint_tag",
                    "section_code",
                    "section_heading",
                    "requirement_text",
                    "evidence_expected",
                    "mandatory",
                    "source_pages",
                    "snippet",
                    "status",
                ],
            )
            writer.writeheader()
            writer.writerows(safe_req_rows)

        checklist_lines = build_simple_checklist_lines(
            tender_id=tender_id,
            main_source_file=main_doc.path.name,
            sections=sections,
            req_rows=req_rows,
        )
        checklist_path.write_text("\n".join(checklist_lines), encoding="utf-8")
        write_simple_checklist_docx(checklist_lines, checklist_docx_path)

        form_rows = build_simple_form_rows(req_rows)
        write_simple_form_docx(form_rows, tender_id, form_docx_path)

        context_lines = build_elegant_context_lines_v2(
            tender_id=tender_id,
            main_source_file=main_doc.path.name,
            context_fields=context_fields,
            tech_spec_hits=deduped_tech_spec_hits,
        )
        md_path.write_text("\n".join(context_lines), encoding="utf-8")
        if not write_context_docx_from_template(context_template_path, context_docx_path, context_fields):
            write_simple_checklist_docx(context_lines, context_docx_path)

        outputs.append(
            {
                "tender_id": tender_id,
                "json": str(json_path),
                "md": str(md_path),
                "context_docx": str(context_docx_path),
                "csv": str(csv_path),
                "xlsx": str(xlsx_path),
                "req": str(requirements_path),
                "checklist": str(checklist_path),
                "checklist_docx": str(checklist_docx_path),
                "form_docx": str(form_docx_path),
            }
        )

    if not outputs:
        print("No tender groups detected with tender-id signature.")
        return 0

    for item in outputs:
        print(f"TENDER: {item['tender_id']}")
        print(f"  JSON: {item['json']}")
        print(f"  MD:   {item['md']}")
        print(f"  CONTEXT DOCX: {item['context_docx']}")
        print(f"  CSV:  {item['csv']}")
        print(f"  XLSX: {item['xlsx']}")
        print(f"  REQ:  {item['req']}")
        print(f"  CHECKLIST: {item['checklist']}")
        print(f"  CHECKLIST DOCX: {item['checklist_docx']}")
        print(f"  FORM DOCX: {item['form_docx']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


