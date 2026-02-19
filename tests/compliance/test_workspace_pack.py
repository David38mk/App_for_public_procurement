from __future__ import annotations

import csv
import shutil
import unittest
import uuid
from pathlib import Path

from app.services.workspace_pack import create_workspace_pack


class WorkspacePackTests(unittest.TestCase):
    def _case_dir(self) -> Path:
        root = Path(__file__).resolve().parents[2] / "downloads" / "test_workspace_pack"
        case_dir = root / str(uuid.uuid4())
        case_dir.mkdir(parents=True, exist_ok=True)
        return case_dir

    def test_workspace_pack_is_deterministic_and_complete(self) -> None:
        root = self._case_dir()
        try:
            output_dir = root / "out"
            output_dir.mkdir(parents=True, exist_ok=True)
            primary = root / "Tender Document.docx"
            primary.write_text("doc", encoding="utf-8")
            att1 = root / "A Form.pdf"
            att2 = root / "B Form.pdf"
            att1.write_text("a", encoding="utf-8")
            att2.write_text("b", encoding="utf-8")

            pack1 = create_workspace_pack(
                base_output_dir=output_dir,
                dossier_ref="DOSSIER-123",
                primary_document_path=primary,
                required_attachment_paths=[str(att2), str(att1)],
            )
            pack2 = create_workspace_pack(
                base_output_dir=output_dir,
                dossier_ref="DOSSIER-123",
                primary_document_path=primary,
                required_attachment_paths=[str(att1), str(att2)],
            )

            self.assertEqual(pack1["workspace_dir"], pack2["workspace_dir"])
            self.assertTrue((Path(pack1["workspace_dir"]) / "00-primary-tender-document.docx").exists())
            self.assertTrue((Path(pack1["workspace_dir"]) / "01-attachment-a-form.pdf").exists())
            self.assertTrue((Path(pack1["workspace_dir"]) / "02-attachment-b-form.pdf").exists())

            with Path(pack1["checklist_path"]).open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0]["item"], "primary_document")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_workspace_pack_blocks_missing_required_attachment(self) -> None:
        root = self._case_dir()
        try:
            output_dir = root / "out"
            output_dir.mkdir(parents=True, exist_ok=True)
            primary = root / "Tender.docx"
            primary.write_text("doc", encoding="utf-8")
            missing_attachment = root / "does-not-exist.pdf"

            with self.assertRaises(ValueError) as ctx:
                create_workspace_pack(
                    base_output_dir=output_dir,
                    dossier_ref="DOSSIER-456",
                    primary_document_path=primary,
                    required_attachment_paths=[str(missing_attachment)],
                )
            self.assertIn("Missing required attachments", str(ctx.exception))
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

