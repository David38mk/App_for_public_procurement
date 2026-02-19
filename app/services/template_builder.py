# -*- coding: utf-8 -*-
import re
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

PLACEHOLDER_PATTERN = re.compile(r"\{\{([A-Za-z0-9_]+)\}\}")
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


def _iter_target_xml_entries(zf: zipfile.ZipFile):
    for name in zf.namelist():
        if not name.startswith("word/") or not name.endswith(".xml"):
            continue
        if not any(token in name for token in ("document.xml", "header", "footer")):
            continue
        yield name


def _replace_placeholders_in_xml(xml_bytes: bytes, values: dict[str, str]) -> bytes:
    root = ET.fromstring(xml_bytes)

    for para in root.findall(".//w:p", NS):
        text_nodes = para.findall(".//w:t", NS)
        if not text_nodes:
            continue

        merged = "".join(node.text or "" for node in text_nodes)
        replaced = merged
        for key, raw_value in values.items():
            replaced = replaced.replace("{{" + key + "}}", raw_value)

        if replaced != merged:
            text_nodes[0].text = replaced
            for extra in text_nodes[1:]:
                extra.text = ""

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def extract_placeholders_from_docx(template_path: str) -> list[str]:
    path = Path(template_path)
    if not path.exists():
        raise FileNotFoundError(template_path)

    placeholders: set[str] = set()
    with zipfile.ZipFile(path, "r") as zf:
        for name in _iter_target_xml_entries(zf):
            xml_bytes = zf.read(name)
            root = ET.fromstring(xml_bytes)
            for para in root.findall(".//w:p", NS):
                text_nodes = para.findall(".//w:t", NS)
                merged = "".join(node.text or "" for node in text_nodes)
                matches = PLACEHOLDER_PATTERN.findall(merged)
                placeholders.update(matches)
    return sorted(placeholders)


def validate_required_template_values(
    template_path: str,
    values: dict[str, str],
    required_fields: list[str] | None = None,
) -> list[str]:
    placeholders = extract_placeholders_from_docx(template_path)
    targets = required_fields if required_fields is not None else placeholders
    missing: list[str] = []

    for field in targets:
        raw = values.get(field, "")
        if not str(raw).strip():
            missing.append(field)

    return sorted(set(missing))


def render_docx_template(template_path: str, output_path: str, values: dict[str, str]) -> None:
    src = Path(template_path)
    dst = Path(output_path)
    dst.parent.mkdir(parents=True, exist_ok=True)

    missing = validate_required_template_values(str(src), values)
    if missing:
        raise ValueError("Missing required template values: " + ", ".join(missing))

    with zipfile.ZipFile(src, "r") as zin:
        target_entries = set(_iter_target_xml_entries(zin))
        with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename in target_entries:
                    data = _replace_placeholders_in_xml(data, values)
                zout.writestr(item, data)
