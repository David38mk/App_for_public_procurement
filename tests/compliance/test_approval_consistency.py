from __future__ import annotations

import json
import unittest
from pathlib import Path


class ApprovalConsistencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.rules_dir = self.root / "compliance" / "rules"
        self.traceability_path = self.root / "compliance" / "traceability_index.csv"
        self.sme_path = self.root / "compliance" / "review" / "sme_review_checklist.csv"
        self.legal_path = self.root / "compliance" / "review" / "legal_review_checklist.csv"

    def _read_csv_rows(self, path: Path) -> list[dict[str, str]]:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        if not lines:
            return []
        header = [h.strip().strip('"') for h in lines[0].split(",")]
        out: list[dict[str, str]] = []
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = []
            cur = ""
            in_quotes = False
            i = 0
            while i < len(line):
                ch = line[i]
                if ch == '"' and (i + 1) < len(line) and line[i + 1] == '"':
                    cur += '"'
                    i += 2
                    continue
                if ch == '"':
                    in_quotes = not in_quotes
                    i += 1
                    continue
                if ch == "," and not in_quotes:
                    parts.append(cur)
                    cur = ""
                    i += 1
                    continue
                cur += ch
                i += 1
            parts.append(cur)
            row = {header[idx]: (parts[idx].strip() if idx < len(parts) else "") for idx in range(len(header))}
            out.append(row)
        return out

    def test_approved_rule_alignment_with_review_and_traceability(self) -> None:
        rules = []
        for p in sorted(self.rules_dir.glob("*.json")):
            data = json.loads(p.read_text(encoding="utf-8-sig"))
            rules.append(data)

        self.assertTrue(rules, "No rule files found.")
        approved_rules = [r for r in rules if r.get("approval_state") == "approved"]
        self.assertEqual(len(approved_rules), len(rules), "All in-scope rules should now be approved.")

        trace_rows = self._read_csv_rows(self.traceability_path)
        trace_by_req = {r.get("requirement_id", ""): r for r in trace_rows}

        sme_rows = self._read_csv_rows(self.sme_path)
        sme_by_req = {r.get("requirement_id", ""): r for r in sme_rows}

        legal_rows = self._read_csv_rows(self.legal_path)
        legal_by_req = {r.get("requirement_id", ""): r for r in legal_rows}

        for rule in approved_rules:
            rule_id = str(rule.get("rule_id") or "")
            req_id = rule_id.replace("RULE-", "REQ-", 1)
            with self.subTest(requirement_id=req_id):
                self.assertIn(req_id, trace_by_req, "Traceability row missing for approved rule.")
                self.assertEqual(
                    trace_by_req[req_id].get("approval_state"),
                    "approved",
                    "Traceability approval_state mismatch.",
                )

                self.assertIn(req_id, sme_by_req, "SME review row missing for approved rule.")
                self.assertEqual(
                    (sme_by_req[req_id].get("reviewer_decision") or "").strip().lower(),
                    "approved",
                    "SME decision must be approved for approved rules.",
                )
                self.assertTrue(
                    (sme_by_req[req_id].get("reviewed_at") or "").strip(),
                    "SME reviewed_at must be populated for approved rules.",
                )

                self.assertIn(req_id, legal_by_req, "Legal review row missing for approved rule.")
                self.assertEqual(
                    (legal_by_req[req_id].get("legal_decision") or "").strip().lower(),
                    "approved",
                    "Legal decision must be approved for approved rules.",
                )
                self.assertTrue(
                    (legal_by_req[req_id].get("reviewed_at") or "").strip(),
                    "Legal reviewed_at must be populated for approved rules.",
                )


if __name__ == "__main__":
    unittest.main()
