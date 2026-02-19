from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path


def _slug(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9]+", "-", (value or "").strip()).strip("-").lower()
    return clean or "workspace"


def _workspace_dir(base_output_dir: str | Path, dossier_ref: str) -> Path:
    return Path(base_output_dir) / f"workspace-{_slug(dossier_ref)}"


def create_workspace_pack(
    base_output_dir: str | Path,
    dossier_ref: str,
    primary_document_path: str | Path,
    required_attachment_paths: list[str] | None = None,
) -> dict[str, str]:
    base = Path(base_output_dir)
    base.mkdir(parents=True, exist_ok=True)
    primary = Path(primary_document_path)
    if not primary.exists():
        raise ValueError(f"Primary document does not exist: {primary}")

    required = [p for p in (required_attachment_paths or []) if str(p).strip()]
    missing = [p for p in required if not Path(p).exists()]
    if missing:
        raise ValueError("Missing required attachments: " + ", ".join(sorted(missing)))

    ws_dir = _workspace_dir(base, dossier_ref)
    ws_dir.mkdir(parents=True, exist_ok=True)

    primary_name = f"00-primary-{_slug(primary.stem)}{primary.suffix.lower()}"
    primary_dst = ws_dir / primary_name
    shutil.copy2(primary, primary_dst)

    copied_attachments: list[dict[str, str]] = []
    for idx, source in enumerate(sorted(required), start=1):
        src = Path(source)
        dst_name = f"{idx:02d}-attachment-{_slug(src.stem)}{src.suffix.lower()}"
        dst = ws_dir / dst_name
        shutil.copy2(src, dst)
        copied_attachments.append(
            {
                "source_path": str(src),
                "copied_filename": dst_name,
                "status": "ok",
            }
        )

    checklist_path = ws_dir / "checklist.csv"
    with checklist_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["item", "type", "source_path", "copied_filename", "status"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "item": "primary_document",
                "type": "primary",
                "source_path": str(primary),
                "copied_filename": primary_name,
                "status": "ok",
            }
        )
        for i, row in enumerate(copied_attachments, start=1):
            writer.writerow(
                {
                    "item": f"required_attachment_{i}",
                    "type": "attachment",
                    "source_path": row["source_path"],
                    "copied_filename": row["copied_filename"],
                    "status": row["status"],
                }
            )

    manifest = {
        "workspace_dir": str(ws_dir),
        "dossier_ref": dossier_ref,
        "primary_document": primary_name,
        "required_attachment_count": len(copied_attachments),
        "checklist": "checklist.csv",
    }
    manifest_path = ws_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "workspace_dir": str(ws_dir),
        "checklist_path": str(checklist_path),
        "manifest_path": str(manifest_path),
    }

