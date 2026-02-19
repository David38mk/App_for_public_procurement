# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from pypdf import PdfReader

ROOT = Path(r"C:\Users\rabota\Desktop\App for public procurements")
MATRIX_IN = ROOT / "compliance" / "requirements_matrix.csv"
OUT_DIR = ROOT / "compliance" / "extraction"
MATRIX_OUT = ROOT / "compliance" / "requirements_matrix_draft_with_citations.csv"
SNIPPETS_OUT = OUT_DIR / "high_risk_extraction_snippets.md"

KEYWORDS: Dict[str, List[str]] = {
    "REQ-ESJN-2021-001": ["пребар", "оглас", "досие", "subject", "notice"],
    "REQ-ESJN-2021-002": ["презем", "документ", "download", "file"],
    "REQ-ESJN-2021-003": ["најава", "корис", "лозин", "login", "password"],
    "REQ-ESJN-2021-004": ["понуда", "поднес", "criteria", "услов"],
    "REQ-ESJN-2021-005": ["прикач", "прилог", "attach", "upload", "document"],
    "REQ-ESJN-2021-006": ["потврд", "confirmation", "број", "reference"],
    "REQ-EPAZAR-2022-001": ["епазар", "оператор", "workflow", "каталог"],
    "REQ-EPAZAR-2022-002": ["задолж", "полиња", "внес", "required", "field"],
    "REQ-EPAZAR-2022-003": ["греш", "error", "неуспеш", "warning", "предупред"],
}


@dataclass
class MatchResult:
    pages: List[int]
    keywords: List[str]
    snippet: str


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def load_pdf_pages(path: Path) -> List[str]:
    reader = PdfReader(str(path))
    pages: List[str] = []
    for p in reader.pages:
        txt = p.extract_text() or ""
        pages.append(normalize(txt))
    return pages


def find_matches(pages: List[str], kws: List[str]) -> MatchResult:
    scored: List[tuple[int, int, List[str]]] = []
    for i, page in enumerate(pages, start=1):
        low = page.lower()
        hit_kws = [k for k in kws if k.lower() in low]
        if hit_kws:
            scored.append((i, len(hit_kws), hit_kws))
    scored.sort(key=lambda t: (-t[1], t[0]))
    top = scored[:3]
    top_pages = [t[0] for t in top]
    top_kws: List[str] = []
    for _, _, hk in top:
        for h in hk:
            if h not in top_kws:
                top_kws.append(h)

    snippet = ""
    if top:
        page_no = top[0][0]
        text = pages[page_no - 1]
        first_kw = top[0][2][0]
        idx = text.lower().find(first_kw.lower())
        if idx >= 0:
            start = max(0, idx - 140)
            end = min(len(text), idx + 220)
            snippet = text[start:end]
        else:
            snippet = text[:260]
    return MatchResult(top_pages, top_kws, snippet)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows: List[dict] = []
    with MATRIX_IN.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)
        rows = []
        for rr in raw_rows:
            fixed = {}
            for k, v in rr.items():
                nk = (k or "").strip().lstrip("\ufeff")
                fixed[nk] = v
            rows.append(fixed)

    pdf_cache: Dict[str, List[str]] = {}
    report_lines: List[str] = ["# High-Risk Manual Extraction (Draft)", ""]

    for r in rows:
        req_id = r["requirement_id"]
        src_rel = r["source_file"]
        src = ROOT / src_rel
        kws = KEYWORDS.get(req_id, [])

        if not kws or not src.exists() or src.suffix.lower() != ".pdf":
            continue

        if src_rel not in pdf_cache:
            try:
                pdf_cache[src_rel] = load_pdf_pages(src)
            except Exception as exc:
                r["interpretation_notes"] = (
                    r["interpretation_notes"]
                    + f" | Extraction failed: {type(exc).__name__}."
                )
                continue

        match = find_matches(pdf_cache[src_rel], kws)
        if match.pages:
            pages_txt = ", ".join(str(p) for p in match.pages)
            kws_txt = ", ".join(match.keywords[:6])
            r["source_section"] = f"Draft citation: pages {pages_txt} (keyword hits: {kws_txt})"
            r["interpretation_notes"] = (
                r["interpretation_notes"]
                + " | Auto-extracted draft page citations; SME/legal must verify exact normative section text."
            )

            report_lines.append(f"## {req_id}")
            report_lines.append(f"- Source: `{src_rel}`")
            report_lines.append(f"- Pages: `{pages_txt}`")
            report_lines.append(f"- Keywords: `{kws_txt}`")
            report_lines.append(f"- Snippet: `{match.snippet}`")
            report_lines.append("")
        else:
            r["interpretation_notes"] = (
                r["interpretation_notes"]
                + " | No keyword match found by automated extraction."
            )

    with MATRIX_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    SNIPPETS_OUT.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"matrix_out={MATRIX_OUT}")
    print(f"snippets_out={SNIPPETS_OUT}")


if __name__ == "__main__":
    main()
