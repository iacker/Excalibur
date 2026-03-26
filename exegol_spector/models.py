from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScanCommand:
    label: str
    template: str


@dataclass(frozen=True)
class ScanProfile:
    scan_type: str
    heading: str
    commands: list[ScanCommand]


@dataclass(frozen=True)
class RuntimePaths:
    root_dir: Path
    knowledge_file: Path
    output_dir: Path
    playbook_file: Path
    xml_report_file: Path
    json_report_file: Path
