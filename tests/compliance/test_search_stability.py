from __future__ import annotations

import unittest

from app.services.search_stability import (
    build_search_context,
    stable_sort_tenders,
    validate_download_scope,
)
from app.services.tender_search import TenderRow


class SearchStabilityTests(unittest.TestCase):
    def test_stable_sort_orders_by_dossier_then_title(self) -> None:
        rows = [
            TenderRow(2, "B", "I1", "2026-01-01", "D-2", 1),
            TenderRow(1, "A", "I1", "2026-01-01", "D-1", 1),
        ]
        out = stable_sort_tenders(rows)
        self.assertEqual([r.dossier_id for r in out], ["D-1", "D-2"])

    def test_validate_download_scope_rejects_changed_keyword(self) -> None:
        rows = [TenderRow(1, "A", "I1", "2026-01-01", "D-1", 1)]
        ctx = build_search_context("internet", "contains", True, rows)
        ok, msg = validate_download_scope(ctx, "fiber", ["D-1"])
        self.assertFalse(ok)
        self.assertIn("Keyword changed", msg)

    def test_validate_download_scope_accepts_matching_context(self) -> None:
        rows = [TenderRow(1, "A", "I1", "2026-01-01", "D-1", 1)]
        ctx = build_search_context("internet", "contains", True, rows)
        ok, msg = validate_download_scope(ctx, "internet", ["D-1"])
        self.assertTrue(ok)
        self.assertEqual(msg, "ok")


if __name__ == "__main__":
    unittest.main()

