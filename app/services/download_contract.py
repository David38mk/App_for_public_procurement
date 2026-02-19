from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class DownloadErrorContract:
    code: str
    user_message: str
    retryable: bool


@dataclass(frozen=True)
class DownloadRetryResult:
    status: str
    attempts_used: int
    started_count: int
    error: DownloadErrorContract | None


def classify_download_exception(exc: Exception) -> DownloadErrorContract:
    text = str(exc).lower()
    name = type(exc).__name__.lower()

    if "outside current visible filtered rows" in text or "not found on first" in text:
        return DownloadErrorContract(
            code="scope_mismatch",
            user_message="Selected dossier is outside current visible search scope.",
            retryable=False,
        )

    if "could not prepare search scope" in text:
        return DownloadErrorContract(
            code="scope_prepare_failed",
            user_message="Could not prepare current search scope for download.",
            retryable=True,
        )

    if "timeout" in text or "webdriver" in name:
        return DownloadErrorContract(
            code="transient_platform_error",
            user_message="Temporary platform error during retrieval; retry is safe.",
            retryable=True,
        )

    if "download failed" in text or "no direct download links" in text:
        return DownloadErrorContract(
            code="download_unavailable",
            user_message="Download links are currently unavailable for this dossier.",
            retryable=True,
        )

    return DownloadErrorContract(
        code="unexpected_error",
        user_message="Unexpected retrieval error.",
        retryable=False,
    )


def execute_with_retry_contract(
    operation: Callable[[int], int],
    max_attempts: int = 2,
    on_event: Callable[[str], Any] | None = None,
) -> DownloadRetryResult:
    attempts = max(1, max_attempts)
    for attempt in range(1, attempts + 1):
        if on_event:
            on_event(f"status=attempt attempt={attempt}/{attempts}")
        try:
            started = operation(attempt)
            if on_event:
                on_event(f"status=success attempt={attempt}/{attempts} started={started}")
            return DownloadRetryResult(
                status="success",
                attempts_used=attempt,
                started_count=started,
                error=None,
            )
        except Exception as exc:
            contract = classify_download_exception(exc)
            if on_event:
                on_event(
                    "status=error "
                    f"attempt={attempt}/{attempts} code={contract.code} retryable={str(contract.retryable).lower()} "
                    f"message={contract.user_message}"
                )
            if (not contract.retryable) or attempt == attempts:
                return DownloadRetryResult(
                    status="failed",
                    attempts_used=attempt,
                    started_count=0,
                    error=contract,
                )

    return DownloadRetryResult(
        status="failed",
        attempts_used=attempts,
        started_count=0,
        error=DownloadErrorContract(
            code="unexpected_error",
            user_message="Unexpected retrieval error.",
            retryable=False,
        ),
    )

