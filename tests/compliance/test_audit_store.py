from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path

from app.services.audit_store import append_audit_event, load_audit_events


class AuditStoreTests(unittest.TestCase):
    def _case_dir(self) -> Path:
        root = Path(__file__).resolve().parents[2] / "downloads" / "test_audit_store"
        case_dir = root / str(uuid.uuid4())
        case_dir.mkdir(parents=True, exist_ok=True)
        return case_dir

    def test_append_and_load_events_are_queryable(self) -> None:
        root = self._case_dir()
        try:
            audit_file = root / "events.jsonl"
            append_audit_event(
                audit_file=audit_file,
                event_type="generate_document",
                actor="alice",
                module="doc_builder",
                status="success",
                dossier_id="D-001",
                metadata={"output_path": "generated_docs/doc1.docx"},
            )
            append_audit_event(
                audit_file=audit_file,
                event_type="download_selected",
                actor="bob",
                module="download",
                status="failed",
                dossier_id="D-002",
                metadata={"error_code": "scope_mismatch"},
            )

            events = load_audit_events(audit_file)
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0]["event_type"], "generate_document")
            self.assertEqual(events[0]["actor"], "alice")
            self.assertEqual(events[0]["module"], "doc_builder")
            self.assertEqual(events[0]["status"], "success")
            self.assertEqual(events[0]["dossier_id"], "D-001")
            self.assertIn("timestamp_utc", events[0])
            self.assertEqual(events[1]["metadata"]["error_code"], "scope_mismatch")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_load_returns_empty_for_missing_file(self) -> None:
        root = self._case_dir()
        try:
            missing = root / "missing.jsonl"
            events = load_audit_events(missing)
            self.assertEqual(events, [])
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

