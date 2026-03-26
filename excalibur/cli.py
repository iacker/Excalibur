from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from excalibur import __version__
from exegol_spector.config import build_runtime_paths
from exegol_spector.knowledge import SCAN_HEADINGS, extract_scan_profile, load_markdown_file
from exegol_spector.nmap_report import parse_host_reports
from exegol_spector.playbooks import build_playbook, render_nmap_command, write_playbook
from exegol_spector.reports import convert_xml_report_to_json
from exegol_spector.runner import run_ansible_playbook

from .banner import render_banner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Excalibur",
        description="Build, run, and inspect knowledge-driven Nmap scans.",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Disable the startup banner.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Excalibur {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    profiles_parser = subparsers.add_parser(
        "profiles",
        help="List available scan profiles discovered in the knowledge file.",
    )
    profiles_parser.add_argument("--no-banner", action="store_true")
    profiles_parser.add_argument("--knowledge-file")
    profiles_parser.set_defaults(handler=handle_profiles)

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check local runtime dependencies and project wiring.",
    )
    doctor_parser.add_argument("--no-banner", action="store_true")
    doctor_parser.add_argument("--knowledge-file")
    doctor_parser.set_defaults(handler=handle_doctor)

    build_parser_cmd = subparsers.add_parser(
        "build",
        help="Generate the Ansible playbook and metadata without executing the scan.",
    )
    _add_scan_arguments(build_parser_cmd)
    build_parser_cmd.set_defaults(handler=handle_build)

    run_parser = subparsers.add_parser(
        "run",
        help="Generate the playbook, execute Ansible, and convert the report to JSON.",
    )
    _add_scan_arguments(run_parser)
    run_parser.add_argument(
        "--skip-orchestrator",
        action="store_true",
        help="Do not trigger the legacy post-processing orchestrator.",
    )
    run_parser.add_argument(
        "--skip-cve",
        action="store_true",
        help="Skip the CVE enrichment step.",
    )
    run_parser.set_defaults(handler=handle_run)

    report_parser = subparsers.add_parser(
        "report",
        help="Convert an existing Nmap XML report to JSON and optionally enrich it.",
    )
    report_parser.add_argument("--no-banner", action="store_true")
    report_parser.add_argument("--xml-report", required=True)
    report_parser.add_argument("--json-report")
    report_parser.add_argument("--skip-cve", action="store_true")
    report_parser.set_defaults(handler=handle_report)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Summarize an existing JSON report.",
    )
    inspect_parser.add_argument("--no-banner", action="store_true")
    inspect_parser.add_argument("--json-report", required=True)
    inspect_parser.set_defaults(handler=handle_inspect)

    return parser


def _add_scan_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--no-banner", action="store_true")
    parser.add_argument(
        "--type",
        choices=sorted(SCAN_HEADINGS.keys()),
        required=True,
        help="Scan profile to use.",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        required=True,
        help="Target IPs, hostnames, or CIDRs.",
    )
    parser.add_argument("--knowledge-file")
    parser.add_argument("--output-dir", default="artifacts")
    parser.add_argument("--report-prefix", default="nmap_report")


def parse_legacy_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Legacy ExegolSpector entrypoint. Prefer Excalibur subcommands."
    )
    parser.add_argument(
        "--type",
        choices=sorted(SCAN_HEADINGS.keys()),
        required=True,
        help="Scan profile to use.",
    )
    parser.add_argument("--targets", nargs="+", required=True)
    parser.add_argument("--knowledge-file")
    parser.add_argument("--output-dir", default="artifacts")
    parser.add_argument("--report-prefix", default="nmap_report")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-orchestrator", action="store_true")
    parser.add_argument("--skip-cve", action="store_true")
    return parser.parse_args(argv)


def get_root_dir() -> Path:
    env_root = os.environ.get("EXCALIBUR_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    cwd = Path.cwd().resolve()
    if (cwd / "Cheetsheet.md" / "Nmap.md").exists():
        return cwd

    package_root = Path(__file__).resolve().parent.parent
    if (package_root / "Cheetsheet.md" / "Nmap.md").exists():
        return package_root

    return cwd


def build_paths(args: argparse.Namespace) -> object:
    return build_runtime_paths(
        root_dir=get_root_dir(),
        knowledge_file=args.knowledge_file,
        output_dir=args.output_dir,
        report_prefix=args.report_prefix,
    )


def print_banner(disabled: bool) -> None:
    if not disabled:
        print(render_banner())


def write_scan_metadata(
    output_dir: Path,
    scan_type: str,
    targets: list[str],
    commands: list[str],
    playbook_file: Path,
) -> Path:
    metadata_file = output_dir / "scan_metadata.json"
    metadata_file.write_text(
        json.dumps(
            {
                "tool": "Excalibur",
                "scan_type": scan_type,
                "targets": targets,
                "commands": commands,
                "playbook_file": str(playbook_file),
            },
            indent=4,
        ),
        encoding="utf-8",
    )
    return metadata_file


def prepare_scan_artifacts(args: argparse.Namespace) -> tuple[object, object, Path, list[str], Path]:
    paths = build_paths(args)
    paths.output_dir.mkdir(parents=True, exist_ok=True)

    markdown_content = load_markdown_file(paths.knowledge_file)
    profile = extract_scan_profile(markdown_content, args.type)
    playbook = build_playbook(profile, args.targets, paths)
    playbook_file = write_playbook(playbook, paths.playbook_file)
    rendered_commands = [
        render_nmap_command(command, args.targets, paths.xml_report_file)
        for command in profile.commands
    ]
    metadata_file = write_scan_metadata(
        paths.output_dir,
        args.type,
        args.targets,
        rendered_commands,
        playbook_file,
    )
    return paths, profile, playbook_file, rendered_commands, metadata_file


def print_scan_summary(
    paths: object,
    profile: object,
    playbook_file: Path,
    rendered_commands: list[str],
    metadata_file: Path,
) -> None:
    print(f"Knowledge file: {paths.knowledge_file}")
    print(f"Profile: {profile.scan_type} | {profile.heading}")
    print(f"Generated playbook: {playbook_file}")
    print(f"Metadata: {metadata_file}")
    for command in rendered_commands:
        print(f"Prepared command: {command}")


def launch_legacy_orchestrator(root_dir: Path, json_report_file: Path) -> None:
    orchestrator_file = root_dir / "Modules" / "attack_orchestrator.py"
    if orchestrator_file.exists():
        subprocess.run(
            ["python3", str(orchestrator_file), str(json_report_file)],
            cwd=root_dir,
            check=True,
        )


def launch_cve_enrichment(root_dir: Path, json_report_file: Path) -> None:
    cve_script = root_dir / "Modules" / "cve_search.py"
    if cve_script.exists():
        subprocess.run(
            ["python3", str(cve_script), str(json_report_file)],
            cwd=root_dir,
            check=True,
        )


def handle_profiles(args: argparse.Namespace) -> int:
    paths = build_runtime_paths(root_dir=get_root_dir(), knowledge_file=args.knowledge_file)
    markdown_content = load_markdown_file(paths.knowledge_file)

    print(f"Knowledge file: {paths.knowledge_file}")
    for scan_type, heading in SCAN_HEADINGS.items():
        try:
            profile = extract_scan_profile(markdown_content, scan_type)
        except ValueError:
            print(f"- {scan_type:<10} missing | {heading}")
            continue

        print(f"- {scan_type:<10} ready   | {len(profile.commands)} command(s)")
    return 0


def handle_doctor(args: argparse.Namespace) -> int:
    root_dir = get_root_dir()
    paths = build_runtime_paths(root_dir=root_dir, knowledge_file=args.knowledge_file)

    checks = {
        "knowledge_file": paths.knowledge_file.exists(),
        "nmap": shutil.which("nmap") is not None,
        "ansible-playbook": shutil.which("ansible-playbook") is not None,
        "legacy_orchestrator": (root_dir / "Modules" / "attack_orchestrator.py").exists(),
        "cve_search": (root_dir / "Modules" / "cve_search.py").exists(),
    }

    for name, status in checks.items():
        state = "ok" if status else "missing"
        print(f"{name:20} {state}")

    return 0 if all(checks.values()) else 1


def handle_build(args: argparse.Namespace) -> int:
    paths, profile, playbook_file, rendered_commands, metadata_file = prepare_scan_artifacts(args)
    print_scan_summary(paths, profile, playbook_file, rendered_commands, metadata_file)
    print("Build complete.")
    return 0


def handle_run(args: argparse.Namespace) -> int:
    paths, profile, playbook_file, rendered_commands, metadata_file = prepare_scan_artifacts(args)
    print_scan_summary(paths, profile, playbook_file, rendered_commands, metadata_file)

    run_ansible_playbook(playbook_file, paths.root_dir)
    json_report_file = convert_xml_report_to_json(paths.xml_report_file, paths.json_report_file)
    print(f"JSON report written to: {json_report_file}")

    if not args.skip_cve:
        launch_cve_enrichment(paths.root_dir, json_report_file)

    if not args.skip_orchestrator:
        launch_legacy_orchestrator(paths.root_dir, json_report_file)

    return 0


def handle_report(args: argparse.Namespace) -> int:
    root_dir = get_root_dir()
    xml_report = Path(args.xml_report).expanduser().resolve()
    json_report = (
        Path(args.json_report).expanduser().resolve()
        if args.json_report
        else xml_report.with_suffix(".json")
    )

    json_report_file = convert_xml_report_to_json(xml_report, json_report)
    print(f"JSON report written to: {json_report_file}")

    if not args.skip_cve:
        launch_cve_enrichment(root_dir, json_report_file)

    return 0


def handle_inspect(args: argparse.Namespace) -> int:
    json_report = Path(args.json_report).expanduser().resolve()
    report_data = json.loads(json_report.read_text(encoding="utf-8"))
    hosts = parse_host_reports(report_data)

    print(f"Report: {json_report}")
    print(f"Hosts: {len(hosts)}")

    for host in hosts:
        services = ", ".join(
            f"{port.port}/{port.service_name or 'unknown'}" for port in host.open_ports
        )
        print(f"- {host.address or 'unknown'} | {len(host.open_ports)} open port(s) | {services}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    print_banner(args.no_banner)
    return args.handler(args)


def main_legacy(argv: list[str] | None = None) -> int:
    args = parse_legacy_args(argv)
    print(render_banner())

    if args.dry_run:
        paths, profile, playbook_file, rendered_commands, metadata_file = prepare_scan_artifacts(args)
        print_scan_summary(paths, profile, playbook_file, rendered_commands, metadata_file)
        print("Dry run enabled; nothing was executed.")
        return 0

    run_args = argparse.Namespace(
        type=args.type,
        targets=args.targets,
        knowledge_file=args.knowledge_file,
        output_dir=args.output_dir,
        report_prefix=args.report_prefix,
        skip_orchestrator=args.skip_orchestrator,
        skip_cve=args.skip_cve,
    )
    return handle_run(run_args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
