from __future__ import annotations

import json
from pathlib import Path

from app.services.policy_loader import load_runtime_rules


def test_runtime_loader_includes_only_approved_rules(tmp_path: Path) -> None:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    approved_rule = {
        "rule_id": "RULE-TEST-APPROVED",
        "approval_state": "approved",
    }
    draft_rule = {
        "rule_id": "RULE-TEST-DRAFT",
        "approval_state": "draft",
    }
    pending_rule = {
        "rule_id": "RULE-TEST-PENDING",
        "approval_state": "pending_legal",
    }

    (rules_dir / "approved.json").write_text(json.dumps(approved_rule), encoding="utf-8")
    (rules_dir / "draft.json").write_text(json.dumps(draft_rule), encoding="utf-8")
    (rules_dir / "pending.json").write_text(json.dumps(pending_rule), encoding="utf-8")

    loaded = load_runtime_rules(rules_dir)

    assert len(loaded) == 1
    assert loaded[0]["rule_id"] == "RULE-TEST-APPROVED"
    assert loaded[0]["approval_state"] == "approved"


def test_runtime_loader_returns_empty_for_missing_directory(tmp_path: Path) -> None:
    missing = tmp_path / "missing-rules-dir"
    loaded = load_runtime_rules(missing)
    assert loaded == []

