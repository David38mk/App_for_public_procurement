from __future__ import annotations

import unittest

from app.services.authorization import authorize_action, build_auth_audit_event


class AuthorizationGateTests(unittest.TestCase):
    def test_download_action_allows_procurement_officer(self) -> None:
        d = authorize_action("download_selected", "alice", "procurement_officer")
        self.assertTrue(d.allowed)

    def test_download_action_denies_viewer(self) -> None:
        d = authorize_action("download_selected", "alice", "viewer")
        self.assertFalse(d.allowed)
        self.assertIn("not allowed", d.reason)

    def test_generate_document_requires_username(self) -> None:
        d = authorize_action("generate_document", "", "admin")
        self.assertFalse(d.allowed)
        self.assertIn("Username is required", d.reason)

    def test_audit_event_has_expected_shape(self) -> None:
        msg = build_auth_audit_event(
            action="download_selected",
            username="alice",
            role="admin",
            allowed=True,
            reason="authorized",
        )
        self.assertIn("AUTH_AUDIT", msg)
        self.assertIn("action=download_selected", msg)
        self.assertIn("user=alice", msg)
        self.assertIn("role=admin", msg)
        self.assertIn("allowed=true", msg)


if __name__ == "__main__":
    unittest.main()

