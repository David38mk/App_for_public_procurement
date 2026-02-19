from __future__ import annotations

from dataclasses import dataclass


SUPPORTED_MODES = {"esjn", "epazar"}


@dataclass(frozen=True)
class RouteDecision:
    mode: str
    allowed: bool
    message: str


def route_action(mode: str, action: str) -> RouteDecision:
    normalized_mode = (mode or "").strip().lower()
    if normalized_mode not in SUPPORTED_MODES:
        return RouteDecision(
            mode=normalized_mode or "unset",
            allowed=False,
            message=f"Unsupported workflow mode: {normalized_mode or 'unset'}",
        )

    # Current connector-backed search/download are ESJN-oriented.
    # Keep these actions available to avoid blocking core discovery flow.
    if normalized_mode == "epazar" and action in {"search", "download_selected"}:
        return RouteDecision(
            mode=normalized_mode,
            allowed=True,
            message="ePazar mode selected; search/download run via ESJN connector in this build.",
        )

    return RouteDecision(mode=normalized_mode, allowed=True, message="routed")
