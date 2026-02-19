# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:\Users\rabota\Desktop\App for public procurements")
OUT_DIR = ROOT / "task_force" / "out"

MANUAL_HINTS = [
    "upatstvo",
    "priracnik",
    "korisnicko",
    "guideline",
    "brosura",
    "manual",
    "guide",
    "упатство",
    "прирачник",
    "корисничко",
]


@dataclass
class ManualRecord:
    path: Path
    ext: str
    size_kb: float
    modified: str
    embedded_creation: str
    embedded_mod: str
    risk: str
    tags: str


def is_manual_file(path: Path) -> bool:
    if path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
        return False
    low = path.as_posix().lower()
    if "review/archive_before_" in low:
        return False
    if "task_force/" in low:
        return False
    if "/упатства/" in low or "/upatstva/" in low:
        return True
    name = path.name.lower()
    return any(h in name for h in MANUAL_HINTS)


def pdf_embedded_dates(path: Path) -> tuple[str, str]:
    if path.suffix.lower() != ".pdf":
        return "", ""
    try:
        raw = path.read_bytes().decode("latin-1", errors="ignore")
    except Exception:
        return "", ""
    c = re.search(r"/CreationDate\s*\(D:(\d{4})(\d{2})(\d{2})", raw)
    m = re.search(r"/ModDate\s*\(D:(\d{4})(\d{2})(\d{2})", raw)
    creation = f"{c.group(1)}-{c.group(2)}-{c.group(3)}" if c else ""
    mod = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""
    return creation, mod


def infer_risk(path: Path, creation_date: str) -> str:
    name = path.name.lower()
    year = None
    m = re.search(r"(20\d{2})", name)
    if m:
        year = int(m.group(1))
    elif creation_date:
        year = int(creation_date[:4])

    if any(x in name for x in ["nov2021", "2021"]):
        return "High"
    if year is not None:
        if year <= 2022:
            return "High"
        if year <= 2024:
            return "Medium"
    return "Low"


def infer_tags(path: Path) -> str:
    name = path.name.lower()
    tags: list[str] = []
    if "esjn" in name or "e-nabavki" in name:
        tags.append("esjn")
    if "епазар" in name or "epazar" in name:
        tags.append("epazar")
    if "digital" in name or "потпис" in name:
        tags.append("digital-signing")
    if "финанс" in name or "finans" in name:
        tags.append("financial-form")
    if "тендер" in name or "tender" in name:
        tags.append("tender-doc")
    if "закон" in name:
        tags.append("law")
    return ",".join(tags)


def build_records() -> list[ManualRecord]:
    records: list[ManualRecord] = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if not is_manual_file(p):
            continue
        cdate, mdate = pdf_embedded_dates(p)
        records.append(
            ManualRecord(
                path=p,
                ext=p.suffix.lower().lstrip("."),
                size_kb=round(p.stat().st_size / 1024, 2),
                modified=datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                embedded_creation=cdate,
                embedded_mod=mdate,
                risk=infer_risk(p, cdate),
                tags=infer_tags(p),
            )
        )
    records.sort(key=lambda r: str(r.path).lower())
    return records


def write_inventory(records: list[ManualRecord]) -> None:
    out = OUT_DIR / "manual_inventory.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "path",
            "type",
            "size_kb",
            "modified",
            "embedded_creation_date",
            "embedded_mod_date",
            "risk",
            "tags",
        ])
        for r in records:
            rel = r.path.relative_to(ROOT).as_posix()
            w.writerow([
                rel,
                r.ext,
                r.size_kb,
                r.modified,
                r.embedded_creation,
                r.embedded_mod,
                r.risk,
                r.tags,
            ])


def write_context_packets(records: list[ManualRecord]) -> None:
    out = OUT_DIR / "manual_context_packets.md"
    lines: list[str] = []
    lines.append("# Manual Context Packets")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    for i, r in enumerate(records, 1):
        rel = r.path.relative_to(ROOT).as_posix()
        lines.append(f"## Manual {i}: `{rel}`")
        lines.append(f"- Type: `{r.ext}`")
        lines.append(f"- Size: `{r.size_kb} KB`")
        lines.append(f"- Modified: `{r.modified}`")
        lines.append(f"- Embedded creation date: `{r.embedded_creation or 'n/a'}`")
        lines.append(f"- Embedded mod date: `{r.embedded_mod or 'n/a'}`")
        lines.append(f"- Risk: `{r.risk}`")
        lines.append(f"- Tags: `{r.tags or 'n/a'}`")
        lines.append("- Context summary: _To be completed by Process Mapping Agent._")
        lines.append("- App implications: _To be completed by Template Intelligence Agent._")
        lines.append("- Open questions: _To be completed._")
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")


def write_handoff(records: list[ManualRecord]) -> None:
    out = OUT_DIR / "handoff_master.md"
    high = [r for r in records if r.risk == "High"]
    medium = [r for r in records if r.risk == "Medium"]

    lines: list[str] = []
    lines.append("# Handoff Master")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Scope")
    lines.append("Build document-handling features using context from all user manuals.")
    lines.append("")
    lines.append("## Inventory Summary")
    lines.append(f"- Manuals detected: `{len(records)}`")
    lines.append(f"- High risk manuals: `{len(high)}`")
    lines.append(f"- Medium risk manuals: `{len(medium)}`")
    lines.append("")
    lines.append("## Priority Manuals (High Risk)")
    for r in high:
        lines.append(f"- `{r.path.relative_to(ROOT).as_posix()}`")
    if not high:
        lines.append("- none")
    lines.append("")
    lines.append("## Next Work Items")
    lines.append("1. Process Mapping Agent: complete context summaries for all manuals.")
    lines.append("2. Template Intelligence Agent: map manual requirements to template placeholders.")
    lines.append("3. Compliance Agent: validate outdated manuals and mark replacement needed.")
    lines.append("4. Handoff Agent: convert findings into implementation tickets for document handling.")
    lines.append("")
    lines.append("## Acceptance Criteria")
    lines.append("- Every manual has a completed context summary.")
    lines.append("- Required fields for document generation are identified and mapped.")
    lines.append("- High-risk manuals are flagged in backlog with mitigation plan.")
    lines.append("- Document handling feature scope is ready for implementation sprint.")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = build_records()
    write_inventory(records)
    write_context_packets(records)
    write_handoff(records)
    print(f"generated_records={len(records)}")
    print(f"inventory={OUT_DIR / 'manual_inventory.csv'}")
    print(f"context={OUT_DIR / 'manual_context_packets.md'}")
    print(f"handoff={OUT_DIR / 'handoff_master.md'}")


if __name__ == "__main__":
    main()
