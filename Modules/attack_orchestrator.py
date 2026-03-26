from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from exegol_spector.nmap_report import parse_host_reports

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_REPORT = ROOT_DIR / "artifacts" / "nmap_report.json"

# Legacy service hooks are intentionally empty by default.
# The orchestration layer remains available, but explicit actions must be
# registered consciously instead of being triggered implicitly after each scan.
SERVICE_ACTIONS: dict[int, list[str]] = {}

def execute_service_action(command: list[str], target_ip: str) -> None:
    executable = Path(command[0])
    if executable.suffix and not executable.exists():
        print(f"Skipping missing action: {' '.join(command)}")
        return

    try:
        print(f"Executing service action for {target_ip}: {' '.join(command)}")
        subprocess.run([*command, target_ip], cwd=ROOT_DIR, check=True)
    except subprocess.CalledProcessError as error:
        print(f"Service action failed for {target_ip}: {error}")


def run_cve_search(report_path: Path) -> None:
    cve_search_script = ROOT_DIR / "Modules" / "cve_search.py"
    if not cve_search_script.exists():
        return

    try:
        subprocess.run(
            ["python3", str(cve_search_script), str(report_path)],
            cwd=ROOT_DIR,
            check=True,
        )
        print("CVE search completed successfully.")
    except subprocess.CalledProcessError as error:
        print(f"Failed to complete CVE search: {error}")


def analyze_report_and_launch_actions(report_path: Path) -> None:
    report_data = json.loads(report_path.read_text(encoding="utf-8"))
    for host in parse_host_reports(report_data):
        if not host.address:
            continue

        for port in host.open_ports:
            command = SERVICE_ACTIONS.get(port.port)
            if command:
                execute_service_action(command, host.address)

    run_cve_search(report_path)


def main() -> int:
    report_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_REPORT
    if not report_path.exists():
        print(f"Report not found: {report_path}")
        return 1

    analyze_report_and_launch_actions(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
