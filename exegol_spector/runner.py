from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def ensure_command_available(command: str) -> None:
    if shutil.which(command) is None:
        raise RuntimeError(f"Required command not found in PATH: {command}")


def run_ansible_playbook(playbook_file: Path, working_directory: Path) -> None:
    ensure_command_available("ansible-playbook")
    subprocess.run(
        ["ansible-playbook", str(playbook_file)],
        cwd=working_directory,
        check=True,
    )
