from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET


def _xml_element_to_dict(element: ET.Element) -> dict | str:
    children = list(element)
    attributes = {f"@{key}": value for key, value in element.attrib.items()}

    if not children:
        text = (element.text or "").strip()
        if attributes:
            if text:
                attributes["#text"] = text
            return attributes
        return text

    grouped_children: dict[str, list] = {}
    for child in children:
        grouped_children.setdefault(child.tag, []).append(_xml_element_to_dict(child))

    node: dict[str, object] = dict(attributes)
    for key, values in grouped_children.items():
        node[key] = values[0] if len(values) == 1 else values

    text = (element.text or "").strip()
    if text:
        node["#text"] = text

    return node


def convert_xml_report_to_json(xml_report_file: Path, json_report_file: Path) -> Path:
    if not xml_report_file.exists():
        raise FileNotFoundError(f"Nmap XML report not found: {xml_report_file}")

    json_report_file.parent.mkdir(parents=True, exist_ok=True)
    root = ET.fromstring(xml_report_file.read_text(encoding="utf-8"))
    json_report_file.write_text(
        json.dumps({root.tag: _xml_element_to_dict(root)}, indent=4),
        encoding="utf-8",
    )
    return json_report_file
