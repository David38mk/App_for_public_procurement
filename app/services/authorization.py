from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


ALLOWED_ROLES_BY_ACTION: dict[str, set[str]] = {
    "download_selected": {"admin", "procurement_officer", "compliance_auditor"},
    "generate_document": {"admin", "procurement_officer"},
}


@dataclass(frozen=True)
class AuthDecision:
    allowed: bool
    reason: str


def authorize_action(action: str, username: str, role: str) -> AuthDecision:
    allowed_roles = ALLOWED_ROLES_BY_ACTION.get(action)
    normalized_role = (role or "").strip().lower()
    normalized_user = (username or "").strip()

    if not normalized_user:
        return AuthDecision(allowed=False, reason="Username is required for privileged action.")

    if not allowed_roles:
        return AuthDecision(allowed=False, reason=f"Unknown protected action: {action}")

    if normalized_role not in allowed_roles:
        return AuthDecision(
            allowed=False,
            reason=f"Role '{normalized_role or 'unset'}' is not allowed for action '{action}'.",
        )

    return AuthDecision(allowed=True, reason="authorized")


def build_auth_audit_event(action: str, username: str, role: str, allowed: bool, reason: str) -> str:
    ts = datetime.now(timezone.utc).isoformat()
    user = (username or "").strip() or "anonymous"
    role_val = (role or "").strip().lower() or "unset"
    return (
        f"AUTH_AUDIT ts={ts} action={action} user={user} "
        f"role={role_val} allowed={str(allowed).lower()} reason={reason}"
    )

