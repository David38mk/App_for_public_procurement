#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
from openpyxl import Workbook

try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover
    PdfReader = None  # type: ignore


DOC_EXTENSIONS = {".pdf", ".docx"}
EXCLUDE_DIR_TOKENS = {"debug"}

KEYWORDS = [
    "услов",
    "услови",
    "доказ",
    "документ",
    "документи",
    "критериум",
    "критериуми",
    "понудувач",
    "економски оператор",
    "обврзан",
    "должен",
    "мора",
    "изјава",
    "гаранција",
    "рок",
    "техничка понуда",
]

UPLOAD_DOC_HINTS = [
    ("банкарска гаранција", "bank_guarantee"),
    ("изјава", "declaration_statement"),
    ("сертификат", "certificate"),
    ("лиценца", "license"),
    ("техничка понуда", "technical_offer"),
    ("финансиска понуда", "financial_offer"),
    ("референтна листа", "reference_list"),
    ("доказ за", "proof_document"),
]


@dataclass
class ContextHit:
    keyword: str
    snippet: str
    page: int | None


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
            data = zf.read(name)
            root = ET.fromstring(data)
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
    out = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return out


def find_hits(paragraphs: list[str], pages: list[str] | None = None) -> list[ContextHit]:
    hits: list[ContextHit] = []
    for para in paragraphs:
        para_l = para.lower()
        for kw in KEYWORDS:
            if kw in para_l:
                page_no: int | None = None
                if pages:
                    for idx, pg in enumerate(pages, start=1):
                        if para[:80] and para[:80] in pg:
                            page_no = idx
                            break
                snippet = para[:500]
                hits.append(ContextHit(keyword=kw, snippet=snippet, page=page_no))
                break
    return hits


def score_filename(path: Path) -> int:
    name = path.name.lower()
    score = 0
    if "тендер" in name:
        score += 5
    if "документација" in name:
        score += 5
    if "техничка" in name:
        score += 3
    if "услов" in name:
        score += 4
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


def build_upload_hints(hits: list[ContextHit]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for hit in hits:
        txt = hit.snippet.lower()
        for term, tag in UPLOAD_DOC_HINTS:
            if term in txt:
                out.append(
                    {
                        "tag": tag,
                        "term": term,
                        "source_page": str(hit.page or ""),
                        "snippet": hit.snippet[:220],
                    }
                )
    # Deduplicate by (tag, snippet)
    unique: dict[tuple[str, str], dict[str, str]] = {}
    for item in out:
        unique[(item["tag"], item["snippet"])] = item
    return list(unique.values())


def build_requirements_template_rows(upload_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    tag_to_category = {
        "bank_guarantee": "guarantee",
        "declaration_statement": "declaration",
        "certificate": "qualification",
        "license": "qualification",
        "technical_offer": "technical_offer",
        "financial_offer": "financial_offer",
        "reference_list": "qualification",
        "proof_document": "evidence",
    }

    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in upload_rows:
        key = (row.get("file", "").strip(), row.get("tag", "").strip())
        grouped.setdefault(key, []).append(row)

    out: list[dict[str, str]] = []
    for (file_name, tag), rows in grouped.items():
        if not tag:
            continue
        category = tag_to_category.get(tag, "evidence")
        terms = sorted({(r.get("term") or "").strip() for r in rows if (r.get("term") or "").strip()})
        source_pages = sorted({(r.get("source_page") or "").strip() for r in rows if (r.get("source_page") or "").strip()})
        snippets = [r.get("snippet", "").strip() for r in rows if (r.get("snippet") or "").strip()]
        hint_text = "; ".join(terms[:4]) if terms else tag
        snippet = snippets[0] if snippets else ""
        req_id = f"REQ-AUTO-{re.sub(r'[^A-Za-z0-9]+', '-', tag).strip('-').upper()}-{len(rows):03d}"
        out.append(
            {
                "requirement_id": req_id,
                "source_file": file_name,
                "category": category,
                "hint_tag": tag,
                "requirement_text": f"Provide evidence for '{hint_text}' derived from tender context.",
                "evidence_expected": tag,
                "mandatory": "yes",
                "source_pages": ",".join(source_pages),
                "snippet": snippet[:280],
                "status": "draft_from_upload_hints",
            }
        )

    out.sort(key=lambda x: (x["source_file"], x["category"], x["hint_tag"]))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract tender context and likely 'Услови' obligations.")
    parser.add_argument("--input-dir", default="downloads", help="Directory with downloaded tender docs.")
    parser.add_argument(
        "--out-dir",
        default="task_force/out/tender_context",
        help="Output folder for structured context pack.",
    )
    parser.add_argument("--max-files", type=int, default=8, help="Max files to process.")
    args = parser.parse_args()

    root = Path.cwd()
    input_dir = (root / args.input_dir).resolve()
    out_dir = (root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    files = collect_candidates(input_dir)[: max(1, args.max_files)]

    results: list[dict[str, Any]] = []
    csv_rows: list[dict[str, str]] = []

    for path in files:
        file_record: dict[str, Any] = {
            "file": str(path),
            "kind": path.suffix.lower().lstrip("."),
            "status": "ok",
            "hit_count": 0,
            "hits": [],
            "upload_hints": [],
        }
        try:
            if path.suffix.lower() == ".pdf":
                text, pages = extract_pdf_text(path)
            else:
                text = extract_docx_text(path)
                pages = []

            paragraphs = split_paragraphs(text)
            hits = find_hits(paragraphs, pages if pages else None)
            upload_hints = build_upload_hints(hits)

            file_record["hit_count"] = len(hits)
            file_record["hits"] = [
                {"keyword": h.keyword, "page": h.page, "snippet": h.snippet} for h in hits[:80]
            ]
            file_record["upload_hints"] = upload_hints[:80]

            for hint in upload_hints:
                csv_rows.append(
                    {
                        "file": path.name,
                        "tag": hint["tag"],
                        "term": hint["term"],
                        "source_page": hint["source_page"],
                        "snippet": hint["snippet"],
                    }
                )
        except Exception as exc:
            file_record["status"] = f"error: {type(exc).__name__}: {exc}"

        results.append(file_record)

    payload = {
        "generated_at_utc": stamp,
        "input_dir": str(input_dir),
        "processed_files": len(results),
        "pdf_reader_available": PdfReader is not None,
        "files": results,
    }

    json_path = out_dir / f"tender_context_{stamp}.json"
    md_path = out_dir / f"tender_context_{stamp}.md"
    csv_path = out_dir / f"upload_hints_{stamp}.csv"
    xlsx_path = out_dir / f"upload_hints_{stamp}.xlsx"
    requirements_path = out_dir / f"upload_requirements_template_{stamp}.csv"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # utf-8-sig keeps Cyrillic readable when opened directly in Excel on Windows.
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["file", "tag", "term", "source_page", "snippet"])
        writer.writeheader()
        writer.writerows(csv_rows)

    wb = Workbook()
    ws = wb.active
    ws.title = "upload_hints"
    ws.append(["file", "tag", "term", "source_page", "snippet"])
    for row in csv_rows:
        ws.append([row["file"], row["tag"], row["term"], row["source_page"], row["snippet"]])
    wb.save(xlsx_path)

    req_rows = build_requirements_template_rows(csv_rows)
    with requirements_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "requirement_id",
                "source_file",
                "category",
                "hint_tag",
                "requirement_text",
                "evidence_expected",
                "mandatory",
                "source_pages",
                "snippet",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(req_rows)

    lines = [
        f"# Tender Context Pack ({stamp})",
        "",
        f"- Input dir: `{input_dir}`",
        f"- Files processed: `{len(results)}`",
        f"- PDF reader available: `{PdfReader is not None}`",
        "",
        "## File Summary",
    ]
    for item in results:
        lines.append(
            f"- `{Path(item['file']).name}`: status={item['status']}, hits={item['hit_count']}, upload_hints={len(item['upload_hints'])}"
        )
    lines.extend(
        [
            "",
            "## Next Use",
            "- Review `upload_hints_*.csv` to map detected obligations to actual upload slots on submit-bid page.",
            "- Review `upload_requirements_template_*.csv` generated from current upload hints (same extraction run).",
            "- Keep all items as draft obligations until manual legal/SME confirmation.",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"JSON: {json_path}")
    print(f"MD:   {md_path}")
    print(f"CSV:  {csv_path}")
    print(f"XLSX: {xlsx_path}")
    print(f"REQ:  {requirements_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
