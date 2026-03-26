from __future__ import annotations

from pathlib import Path

from .models import RuntimePaths, ScanCommand, ScanProfile


def render_nmap_command(command: ScanCommand, targets: list[str], xml_report_file: Path) -> str:
    rendered_command = command.template.replace("[target]", " ".join(targets))
    if "[target]" not in command.template:
        rendered_command = f"{rendered_command} {' '.join(targets)}"

    if "-oX" not in rendered_command:
        rendered_command = f"{rendered_command} -oX {xml_report_file}"

    return rendered_command


def build_playbook(profile: ScanProfile, targets: list[str], paths: RuntimePaths) -> list[dict]:
    tasks = []
    for command in profile.commands:
        rendered_command = render_nmap_command(command, targets, paths.xml_report_file)
        tasks.append(
            {
                "name": f"Nmap | {command.label}",
                "ansible.builtin.command": rendered_command,
            }
        )

    return [
        {
            "name": f"Excalibur {profile.scan_type} scan",
            "hosts": "localhost",
            "gather_facts": False,
            "tasks": tasks,
        }
    ]


def _quote_yaml(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _dump_playbook_yaml(playbook: list[dict]) -> str:
    lines: list[str] = []
    for play in playbook:
        lines.extend(
            [
                f"- name: {_quote_yaml(play['name'])}",
                f"  hosts: {_quote_yaml(play['hosts'])}",
                f"  gather_facts: {str(play['gather_facts']).lower()}",
                "  tasks:",
            ]
        )
        for task in play["tasks"]:
            lines.extend(
                [
                    f"    - name: {_quote_yaml(task['name'])}",
                    f"      ansible.builtin.command: {_quote_yaml(task['ansible.builtin.command'])}",
                ]
            )
    return "\n".join(lines) + "\n"


def write_playbook(playbook: list[dict], playbook_file: Path) -> Path:
    playbook_file.parent.mkdir(parents=True, exist_ok=True)
    playbook_file.write_text(_dump_playbook_yaml(playbook), encoding="utf-8")
    return playbook_file
