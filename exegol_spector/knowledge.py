from __future__ import annotations

import re
from pathlib import Path

from .models import ScanCommand, ScanProfile

SCAN_HEADINGS = {
    "basic": "### Basic Scanning Techniques",
    "discovery": "### Discovery Options",
    "advanced": "### Advanced Scanning Options",
    "port": "### Port Scanning Options",
    "version": "### Version Detection",
    "aggressive": "### Firewall Evasion Techniques",
}

COMMAND_PATTERN = re.compile(r"`(nmap[^`]*)`")


def load_markdown_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Knowledge file not found: {path}")
    return path.read_text(encoding="utf-8")


def extract_scan_profile(markdown_content: str, scan_type: str) -> ScanProfile:
    heading = SCAN_HEADINGS.get(scan_type)
    if not heading:
        raise ValueError(f"Unsupported scan type: {scan_type}")

    commands: list[ScanCommand] = []
    in_section = False
    current_label = ""

    for raw_line in markdown_content.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped == heading:
            in_section = True
            continue

        if in_section and stripped.startswith("### "):
            break

        if not in_section or not stripped:
            continue

        if stripped.startswith("* ") and "`nmap" not in stripped:
            current_label = stripped[2:].strip()
            continue

        match = COMMAND_PATTERN.search(stripped)
        if not match:
            continue

        label = current_label or f"{scan_type} command {len(commands) + 1}"
        commands.append(ScanCommand(label=label, template=match.group(1).strip()))

    if not commands:
        raise ValueError(
            f"No Nmap commands found for scan type '{scan_type}' in heading '{heading}'."
        )

    return ScanProfile(scan_type=scan_type, heading=heading, commands=commands)
