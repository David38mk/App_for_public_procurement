from __future__ import annotations

from typing import Iterable

try:
    from .tender_search import TenderRow
except ImportError:
    from tender_search import TenderRow


def stable_sort_tenders(rows: Iterable[TenderRow]) -> list[TenderRow]:
    return sorted(
        list(rows),
        key=lambda r: (
            (r.dossier_id or "").strip().lower(),
            (r.title or "").strip().lower(),
            (r.institution or "").strip().lower(),
            (r.deadline or "").strip().lower(),
            int(r.source_page or 0),
            int(r.index or 0),
        ),
    )


def build_search_context(
    keyword: str,
    match_mode: str,
    strict_filter: bool,
    rows: Iterable[TenderRow],
) -> dict:
    ordered = stable_sort_tenders(rows)
    dossier_ids = tuple((r.dossier_id or "").strip() for r in ordered if (r.dossier_id or "").strip())
    return {
        "keyword": (keyword or "").strip(),
        "match_mode": (match_mode or "").strip(),
        "strict_filter": bool(strict_filter),
        "dossier_ids": dossier_ids,
    }


def validate_download_scope(
    context: dict | None,
    current_keyword: str,
    selected_dossier_ids: Iterable[str],
) -> tuple[bool, str]:
    if not context:
        return False, "No active search context. Run search before download."

    if (current_keyword or "").strip() != (context.get("keyword") or "").strip():
        return False, "Keyword changed after search. Re-run search to refresh stable results."

    allowed = set(context.get("dossier_ids") or ())
    selected = {(d or "").strip() for d in selected_dossier_ids if (d or "").strip()}
    if not selected.issubset(allowed):
        return False, "Selected dossier is outside last stable search context. Re-run search."

    return True, "ok"
