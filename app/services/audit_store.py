from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_audit_event(
    audit_file: str | Path,
    event_type: str,
    actor: str,
    module: str,
    status: str,
    dossier_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = Path(audit_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp_utc": _now_utc(),
        "event_type": event_type,
        "actor": actor,
        "module": module,
        "status": status,
        "dossier_id": dossier_id,
        "metadata": metadata or {},
    }

    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event


def load_audit_events(audit_file: str | Path) -> list[dict[str, Any]]:
    path = Path(audit_file)
    if not path.exists():
        return []

    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            events.append(json.loads(raw))
    return events

