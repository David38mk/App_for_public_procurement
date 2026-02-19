from __future__ import annotations

import unittest

from app.services.ux_guidance import build_corrective_guidance


class UxGuidanceTests(unittest.TestCase):
    def test_scope_prepare_failed_guidance_is_retry_safe(self) -> None:
        g = build_corrective_guidance("scope_prepare_failed", "download_selected", "esjn")
        self.assertEqual(g["error_code"], "scope_prepare_failed")
        self.assertTrue(g["retry_safe"])
        self.assertTrue(len(g["steps"]) >= 2)

    def test_unknown_error_falls_back_to_unexpected(self) -> None:
        g = build_corrective_guidance("something-unknown", "generate_document", "epazar")
        self.assertEqual(g["error_code"], "something-unknown")
        self.assertIn("Corrective guidance", g["title"])
        self.assertTrue(len(g["steps"]) >= 2)


if __name__ == "__main__":
    unittest.main()

