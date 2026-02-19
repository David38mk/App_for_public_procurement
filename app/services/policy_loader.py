from __future__ import annotations

import json
from pathlib import Path
from typing import Any


APPROVED_STATE = "approved"


def load_runtime_rules(rules_dir: str | Path) -> list[dict[str, Any]]:
    """
    Load only approved policy rules for runtime usage.

    Draft/pending/deprecated rules are intentionally excluded.
    """
    root = Path(rules_dir)
    if not root.exists():
        return []

    approved_rules: list[dict[str, Any]] = []
    for rule_path in sorted(root.glob("*.json")):
        rule = json.loads(rule_path.read_text(encoding="utf-8-sig"))
        if rule.get("approval_state") == APPROVED_STATE:
            approved_rules.append(rule)

    return approved_rules
