from __future__ import annotations


def validate_required_inputs(payload: dict[str, str], required_fields: list[str]) -> list[str]:
    missing: list[str] = []
    for field in required_fields:
        value = payload.get(field, "")
        if not str(value).strip():
            missing.append(field)
    return sorted(set(missing))

