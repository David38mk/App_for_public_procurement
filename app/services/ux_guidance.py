from __future__ import annotations


def build_corrective_guidance(error_code: str, action: str, mode: str) -> dict[str, object]:
    code = (error_code or "unexpected_error").strip().lower()
    action_val = (action or "").strip().lower() or "action"
    mode_val = (mode or "").strip().lower() or "esjn"

    guidance_map = {
        "scope_mismatch": [
            "Run a fresh search and keep filters unchanged.",
            "Select dossiers only from current visible results.",
            "Retry download from the same search context.",
        ],
        "scope_prepare_failed": [
            "Wait a few seconds and retry.",
            "Confirm portal page is loaded and search panel is available.",
            "If repeated, re-open notices page and run search again.",
        ],
        "transient_platform_error": [
            "Retry after short delay; operation is retry-safe.",
            "Check network/connectivity stability.",
            "Capture screenshot/log if error repeats.",
        ],
        "download_unavailable": [
            "Verify dossier has public download links.",
            "Try login-enabled download flow if credentials are available.",
            "Retry later if portal links are temporarily unavailable.",
        ],
        "validation_missing_fields": [
            "Fill all mandatory fields shown in the validation error.",
            "Re-run action after required fields are complete.",
            "Do not proceed until validation passes.",
        ],
        "unexpected_error": [
            "Retry once from the same workflow context.",
            "If repeated, re-open workflow and repeat from previous stable step.",
            "Escalate with error details and timestamp.",
        ],
    }

    steps = guidance_map.get(code, guidance_map["unexpected_error"])
    retry_safe = code in {
        "scope_prepare_failed",
        "transient_platform_error",
        "download_unavailable",
        "validation_missing_fields",
    }
    title = f"Corrective guidance for {action_val} ({mode_val})"
    return {
        "title": title,
        "error_code": code,
        "retry_safe": retry_safe,
        "steps": steps,
    }

