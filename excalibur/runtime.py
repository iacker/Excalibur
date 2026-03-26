from __future__ import annotations

import re
import shutil
from pathlib import Path


APT_INSTALL_PATTERN = re.compile(r"apt-get install -y --no-install-recommends\s+(.+?)\s+&&", re.S)


def extract_container_packages(dockerfile: Path) -> list[str]:
    if not dockerfile.exists():
        return []

    content = dockerfile.read_text(encoding="utf-8")
    match = APT_INSTALL_PATTERN.search(content)
    if not match:
        return []

    packages = []
    for raw_line in match.group(1).splitlines():
        cleaned = raw_line.strip().rstrip("\\").strip()
        if cleaned:
            packages.append(cleaned)
    return packages


def extract_project_modules(modules_dir: Path) -> list[str]:
    if not modules_dir.exists():
        return []

    return sorted(path.name for path in modules_dir.iterdir() if path.is_file())


def collect_runtime_command_status(commands: list[str]) -> dict[str, bool]:
    return {command: shutil.which(command) is not None for command in commands}
