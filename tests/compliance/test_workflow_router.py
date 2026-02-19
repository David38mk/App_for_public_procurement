from __future__ import annotations

import unittest

from app.services.workflow_router import route_action


class WorkflowRouterTests(unittest.TestCase):
    def test_esjn_route_allows_search(self) -> None:
        d = route_action("esjn", "search")
        self.assertTrue(d.allowed)
        self.assertEqual(d.mode, "esjn")

    def test_epazar_route_allows_esjn_connector_fallback(self) -> None:
        d = route_action("epazar", "search")
        self.assertTrue(d.allowed)
        self.assertIn("ESJN connector", d.message)

    def test_unknown_mode_is_rejected(self) -> None:
        d = route_action("unknown", "generate_document")
        self.assertFalse(d.allowed)
        self.assertIn("Unsupported workflow mode", d.message)


if __name__ == "__main__":
    unittest.main()
