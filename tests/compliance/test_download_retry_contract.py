from __future__ import annotations

import unittest

from app.services.download_contract import (
    classify_download_exception,
    execute_with_retry_contract,
)


class DownloadRetryContractTests(unittest.TestCase):
    def test_retry_contract_retries_retryable_error_then_succeeds(self) -> None:
        calls = {"n": 0}

        def op(_: int) -> int:
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("Could not prepare search scope for download.")
            return 3

        result = execute_with_retry_contract(operation=op, max_attempts=2)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.attempts_used, 2)
        self.assertEqual(result.started_count, 3)

    def test_retry_contract_stops_on_non_retryable_error(self) -> None:
        calls = {"n": 0}

        def op(_: int) -> int:
            calls["n"] += 1
            raise RuntimeError("Download guard blocked dossier outside current visible filtered rows.")

        result = execute_with_retry_contract(operation=op, max_attempts=3)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.attempts_used, 1)
        self.assertEqual(result.error.code, "scope_mismatch")
        self.assertEqual(calls["n"], 1)

    def test_classification_maps_known_patterns(self) -> None:
        c1 = classify_download_exception(RuntimeError("No direct download links found."))
        self.assertEqual(c1.code, "download_unavailable")
        self.assertTrue(c1.retryable)

        c2 = classify_download_exception(RuntimeError("Could not prepare search scope for download."))
        self.assertEqual(c2.code, "scope_prepare_failed")
        self.assertTrue(c2.retryable)


if __name__ == "__main__":
    unittest.main()

