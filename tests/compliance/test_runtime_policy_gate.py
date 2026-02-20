from __future__ import annotations

import json
import shutil
import unittest
import uuid
from pathlib import Path

from app.services.runtime_policy import load_runtime_policy_gate


class RuntimePolicyGateTests(unittest.TestCase):
    def _write_rule(self, rules_dir: Path, name: str, payload: dict) -> None:
        (rules_dir / name).write_text(json.dumps(payload), encoding="utf-8")

    def _make_case_dir(self) -> Path:
        root = Path(__file__).resolve().parents[2] / "downloads" / "test_runtime_policy_gate"
        case_dir = root / str(uuid.uuid4())
        case_dir.mkdir(parents=True, exist_ok=True)
        return case_dir

    def test_denies_action_when_module_has_no_approved_rules(self) -> None:
        root = self._make_case_dir()
        try:
            rules_dir = root / "rules"
            rules_dir.mkdir(parents=True, exist_ok=True)
            self._write_rule(
                rules_dir,
                "draft-search.json",
                {"rule_id": "RULE-SEARCH-DRAFT", "app_module": "search", "approval_state": "draft"},
            )

            gate = load_runtime_policy_gate(rules_dir)
            decision = gate.decide("search")
            self.assertFalse(decision.allowed)
            self.assertEqual(decision.module, "search")
            self.assertEqual(decision.active_rule_ids, ())
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_allows_action_when_module_has_approved_rule(self) -> None:
        root = self._make_case_dir()
        try:
            rules_dir = root / "rules"
            rules_dir.mkdir(parents=True, exist_ok=True)
            self._write_rule(
                rules_dir,
                "approved-doc-builder.json",
                {"rule_id": "RULE-DOC-APPROVED", "app_module": "doc_builder", "approval_state": "approved"},
            )

            gate = load_runtime_policy_gate(rules_dir)
            decision = gate.decide("generate_document")
            self.assertTrue(decision.allowed)
            self.assertEqual(decision.module, "doc_builder")
            self.assertEqual(decision.active_rule_ids, ("RULE-DOC-APPROVED",))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_unknown_action_is_denied(self) -> None:
        gate = load_runtime_policy_gate(Path(__file__).resolve().parents[2] / "compliance" / "rules")
        decision = gate.decide("unknown_action")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.module, "unknown")


if __name__ == "__main__":
    unittest.main()
