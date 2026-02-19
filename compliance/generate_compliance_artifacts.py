from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPLIANCE_DIR = ROOT / "compliance"
REVIEW_DIR = COMPLIANCE_DIR / "review"
RULES_DIR = COMPLIANCE_DIR / "rules"
TESTS_DIR = ROOT / "tests" / "compliance"

MATRIX_PATH = COMPLIANCE_DIR / "requirements_matrix_draft_with_citations.csv"
RULE_SCHEMA_PATH = COMPLIANCE_DIR / "rule_schema.json"
SME_REVIEW_PATH = REVIEW_DIR / "sme_review_checklist.csv"
LEGAL_REVIEW_PATH = REVIEW_DIR / "legal_review_checklist.csv"
TRACEABILITY_PATH = COMPLIANCE_DIR / "traceability_index.csv"
BACKLOG_PATH = COMPLIANCE_DIR / "IMPLEMENTATION_BACKLOG.md"


def read_matrix_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def infer_rule_type(app_module: str) -> str:
    module = (app_module or "").strip().lower()
    mapping = {
        "search": "workflow_gate",
        "download": "document_requirement",
        "auth_audit": "authorization",
        "doc_builder": "document_requirement",
        "workspace_pack": "document_requirement",
        "audit_log": "audit",
        "workflow_router": "workflow_gate",
        "validation_engine": "validation",
        "ux_errors": "workflow_gate",
    }
    return mapping.get(module, "validation")


def infer_severity(app_module: str) -> str:
    module = (app_module or "").strip().lower()
    if module in {"auth_audit", "doc_builder", "workspace_pack"}:
        return "high"
    if module in {"audit_log", "workflow_router", "validation_engine"}:
        return "medium"
    return "low"


def requirement_to_rule_id(requirement_id: str) -> str:
    suffix = requirement_id.replace("REQ-", "")
    return f"RULE-{suffix}"


def parse_draft_page(source_section: str) -> int | None:
    text = source_section or ""
    marker = "pages "
    idx = text.find(marker)
    if idx == -1:
        return None
    page_chunk = text[idx + len(marker) :].split("(", 1)[0]
    first_token = page_chunk.split(",", 1)[0].strip()
    try:
        return int(first_token)
    except ValueError:
        return None


def build_rule(row: dict[str, str]) -> dict[str, object]:
    requirement_id = row["requirement_id"]
    rule_id = requirement_to_rule_id(requirement_id)
    source_section = row["source_section"]
    return {
        "rule_id": rule_id,
        "source_file": row["source_file"],
        "source_section": source_section,
        "source_page": parse_draft_page(source_section),
        "effective_from": row["source_date"],
        "effective_to": None,
        "rule_type": infer_rule_type(row["app_module"]),
        "severity": infer_severity(row["app_module"]),
        "condition": f"Requirement {requirement_id} applies to {row['app_module']} flow.",
        "action": row["requirement_text"],
        "error_message": f"{requirement_id} is not satisfied.",
        "app_module": row["app_module"],
        "test_case_id": row["test_case_id"],
        "approval_state": "draft",
        "approved_by": None,
        "approved_at": None,
        "version": "0.1.0",
        "notes": (
            "Draft rule generated from machine-derived citation matrix. "
            "Requires SME + legal validation before any promotion."
        ),
    }


def write_rule_files(rows: list[dict[str, str]]) -> None:
    RULES_DIR.mkdir(parents=True, exist_ok=True)
    for row in rows:
        rule = build_rule(row)
        file_name = f"{row['requirement_id'].lower()}.json"
        out_path = RULES_DIR / file_name
        out_path.write_text(json.dumps(rule, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_test_scaffolding(rows: list[dict[str, str]]) -> None:
    TESTS_DIR.mkdir(parents=True, exist_ok=True)
    init_path = TESTS_DIR / "__init__.py"
    if not init_path.exists():
        init_path.write_text("", encoding="utf-8")

    for row in rows:
        req_id = row["requirement_id"]
        tc_id = row["test_case_id"]
        test_name = f"test_{tc_id.lower().replace('-', '_')}.py"
        file_path = TESTS_DIR / test_name
        content = f"""from __future__ import annotations

import json
from pathlib import Path


def test_{tc_id.lower().replace('-', '_')}_approval_gate() -> None:
    rule_path = Path(__file__).resolve().parents[2] / "compliance" / "rules" / "{req_id.lower()}.json"
    rule = json.loads(rule_path.read_text(encoding="utf-8"))
    assert rule["rule_id"] == "RULE-{req_id.replace("REQ-", "")}"
    assert rule["test_case_id"] == "{tc_id}"
    assert (
        rule["approval_state"] == "approved"
    ), "Fail-safe gate: non-approved rules must stay inactive until SME+legal approval."
"""
        file_path.write_text(content, encoding="utf-8")


def write_backlog(rows: list[dict[str, str]]) -> None:
    date_label = datetime.now(timezone.utc).date().isoformat()
    lines = [
        "# Compliance Implementation Backlog",
        "",
        f"Updated: {date_label} (UTC)",
        "",
        "Scope: Document handling backlog derived only from draft, traceable requirements.",
        "",
        "## Priority 1 (Blocking)",
    ]
    for req_id in ("REQ-ESJN-2021-004", "REQ-ESJN-2021-005", "REQ-ESJN-2021-002"):
        row = next(r for r in rows if r["requirement_id"] == req_id)
        lines.append(
            f"- `{req_id}` ({row['test_case_id']}): {row['requirement_text']} "
            f"[module={row['app_module']}, approval_state=draft]"
        )

    lines.extend(
        [
            "",
            "## Priority 2 (High Risk Controls)",
            "- `REQ-ESJN-2021-003` (TC-REQ-003): Enforce authenticated role gates and audit logs in document operations.",
            "- `REQ-ESJN-2021-006` (TC-REQ-006): Persist submission evidence metadata for audit traceability.",
            "",
            "## Priority 3 (Workflow Segmentation and UX)",
            "- `REQ-EPAZAR-2022-001` (TC-REQ-007): Separate ePazar vs ESJN flows in document handling UX.",
            "- `REQ-EPAZAR-2022-002` (TC-REQ-008): Validate ePazar mandatory inputs before document actions.",
            "- `REQ-EPAZAR-2022-003` (TC-REQ-009): Add corrective guidance and retry-safe state handling.",
            "",
            "## Guardrails",
            "- Do not activate runtime policy loading for any rule unless `approval_state=approved`.",
            "- Every backlog item must retain traceability to requirement ID, source citation, rule ID, and test case ID.",
            "- Any source-section update requires SME+legal re-review and regression tests.",
            "",
        ]
    )
    BACKLOG_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = read_matrix_rows(MATRIX_PATH)

    _ = json.loads(RULE_SCHEMA_PATH.read_text(encoding="utf-8-sig"))

    now = datetime.now(timezone.utc).isoformat()

    write_csv(
        SME_REVIEW_PATH,
        [
            "requirement_id",
            "source_file",
            "draft_source_section",
            "reviewer_decision",
            "reviewer_comment",
            "reviewed_at",
        ],
        [
            {
                "requirement_id": row["requirement_id"],
                "source_file": row["source_file"],
                "draft_source_section": row["source_section"],
                "reviewer_decision": "",
                "reviewer_comment": "",
                "reviewed_at": "",
            }
            for row in rows
        ],
    )

    write_csv(
        LEGAL_REVIEW_PATH,
        [
            "requirement_id",
            "legal_decision",
            "legal_comment",
            "effective_from_confirmed",
            "reviewed_at",
        ],
        [
            {
                "requirement_id": row["requirement_id"],
                "legal_decision": "",
                "legal_comment": "",
                "effective_from_confirmed": "",
                "reviewed_at": "",
            }
            for row in rows
        ],
    )

    write_rule_files(rows)

    write_csv(
        TRACEABILITY_PATH,
        [
            "requirement_id",
            "rule_id",
            "source_file",
            "source_section",
            "app_module",
            "test_case_id",
            "approval_state",
        ],
        [
            {
                "requirement_id": row["requirement_id"],
                "rule_id": requirement_to_rule_id(row["requirement_id"]),
                "source_file": row["source_file"],
                "source_section": row["source_section"],
                "app_module": row["app_module"],
                "test_case_id": row["test_case_id"],
                "approval_state": "draft",
            }
            for row in rows
        ],
    )

    write_test_scaffolding(rows)
    write_backlog(rows)

    summary = {
        "generated_at": now,
        "requirements_count": len(rows),
        "review_files": [str(SME_REVIEW_PATH), str(LEGAL_REVIEW_PATH)],
        "rules_dir": str(RULES_DIR),
        "traceability_index": str(TRACEABILITY_PATH),
        "tests_dir": str(TESTS_DIR),
        "backlog": str(BACKLOG_PATH),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
