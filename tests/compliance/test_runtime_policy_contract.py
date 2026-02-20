from __future__ import annotations

import unittest
from pathlib import Path

from app.services.policy_loader import load_runtime_rules
from app.services.runtime_policy import load_runtime_policy_gate


class RuntimePolicyContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rules_dir = Path(__file__).resolve().parents[2] / "compliance" / "rules"

    def test_all_rules_in_scope_are_approved_for_runtime(self) -> None:
        loaded = load_runtime_rules(self.rules_dir)
        self.assertEqual(
            len(loaded),
            9,
            "Expected 9 approved in-scope rules to be runtime-active.",
        )

    def test_core_actions_are_allowed_by_runtime_gate(self) -> None:
        gate = load_runtime_policy_gate(self.rules_dir)
        for action in ("search", "download_selected", "generate_document"):
            with self.subTest(action=action):
                decision = gate.decide(action)
                self.assertTrue(decision.allowed, f"Action '{action}' should be allowed by approved rules.")
                self.assertTrue(decision.active_rule_ids, "Approved rule set should not be empty.")


if __name__ == "__main__":
    unittest.main()
