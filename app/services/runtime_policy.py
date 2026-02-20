from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .policy_loader import load_runtime_rules


ACTION_TO_MODULE = {
    "search": "search",
    "download_selected": "download",
    "generate_document": "doc_builder",
}


@dataclass(frozen=True)
class PolicyDecision:
    action: str
    module: str
    allowed: bool
    reason: str
    active_rule_ids: tuple[str, ...]


class RuntimePolicyGate:
    def __init__(self, approved_rules: list[dict]):
        by_module: dict[str, list[dict]] = {}
        for rule in approved_rules:
            module = str(rule.get("app_module") or "").strip()
            if not module:
                continue
            by_module.setdefault(module, []).append(rule)
        self._by_module = by_module

    def decide(self, action: str) -> PolicyDecision:
        normalized_action = (action or "").strip()
        module = ACTION_TO_MODULE.get(normalized_action)
        if not module:
            return PolicyDecision(
                action=normalized_action or "unset",
                module="unknown",
                allowed=False,
                reason=f"No compliance module mapping defined for action '{normalized_action or 'unset'}'.",
                active_rule_ids=(),
            )

        module_rules = self._by_module.get(module, [])
        rule_ids = tuple(sorted(str(rule.get("rule_id") or "") for rule in module_rules if rule.get("rule_id")))
        if not module_rules:
            return PolicyDecision(
                action=normalized_action,
                module=module,
                allowed=False,
                reason=(
                    f"No approved runtime rules for module '{module}'. "
                    "Action stays blocked until SME+legal approval is completed."
                ),
                active_rule_ids=(),
            )

        return PolicyDecision(
            action=normalized_action,
            module=module,
            allowed=True,
            reason="approved_rule_active",
            active_rule_ids=rule_ids,
        )


def load_runtime_policy_gate(rules_dir: str | Path) -> RuntimePolicyGate:
    return RuntimePolicyGate(load_runtime_rules(rules_dir))
