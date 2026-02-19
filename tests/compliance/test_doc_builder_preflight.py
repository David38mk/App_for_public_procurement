from __future__ import annotations

import unittest
import zipfile
import shutil
import uuid
from pathlib import Path

from app.services.template_builder import render_docx_template


def _write_minimal_docx(path: Path) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""
    document = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>{{ORG_NAME}}</w:t></w:r></w:p>
    <w:p><w:r><w:t>{{TENDER_ID}}</w:t></w:r></w:p>
  </w:body>
</w:document>
"""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document)


class TemplatePreflightTests(unittest.TestCase):
    def _make_case_dir(self) -> Path:
        root = Path(__file__).resolve().parents[2] / "downloads" / "test_doc_builder_preflight"
        case_dir = root / str(uuid.uuid4())
        case_dir.mkdir(parents=True, exist_ok=True)
        return case_dir

    def test_render_blocks_when_required_placeholder_value_missing(self) -> None:
        root = self._make_case_dir()
        try:
            template = root / "template.docx"
            output = root / "out.docx"
            _write_minimal_docx(template)

            with self.assertRaises(ValueError) as ctx:
                render_docx_template(
                    str(template),
                    str(output),
                    {
                        "ORG_NAME": "Example Org",
                        "TENDER_ID": "",
                    },
                )
            self.assertIn("Missing required template values", str(ctx.exception))
            self.assertIn("TENDER_ID", str(ctx.exception))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_render_succeeds_when_all_placeholder_values_provided(self) -> None:
        root = self._make_case_dir()
        try:
            template = root / "template.docx"
            output = root / "out.docx"
            _write_minimal_docx(template)

            render_docx_template(
                str(template),
                str(output),
                {
                    "ORG_NAME": "Example Org",
                    "TENDER_ID": "TN-001",
                },
            )
            self.assertTrue(output.exists())
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
