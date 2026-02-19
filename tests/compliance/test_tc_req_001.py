from __future__ import annotations

import json
from pathlib import Path


def test_tc_req_001_approval_gate() -> None:
    rule_path = Path(__file__).resolve().parents[2] / "compliance" / "rules" / "req-esjn-2021-001.json"
    rule = json.loads(rule_path.read_text(encoding="utf-8"))
    assert rule["rule_id"] == "RULE-ESJN-2021-001"
    assert rule["test_case_id"] == "TC-REQ-001"
    assert (
        rule["approval_state"] == "approved"
    ), "Fail-safe gate: non-approved rules must stay inactive until SME+legal approval."
