from __future__ import annotations

from pathlib import Path

from .models import RuntimePaths


def build_runtime_paths(
    root_dir: Path,
    knowledge_file: str | None = None,
    output_dir: str = "artifacts",
    report_prefix: str = "nmap_report",
) -> RuntimePaths:
    resolved_root = root_dir.resolve()
    resolved_output_dir = (resolved_root / output_dir).resolve()
    resolved_knowledge = (
        Path(knowledge_file).expanduser().resolve()
        if knowledge_file
        else (resolved_root / "Cheetsheet.md" / "Nmap.md").resolve()
    )

    return RuntimePaths(
        root_dir=resolved_root,
        knowledge_file=resolved_knowledge,
        output_dir=resolved_output_dir,
        playbook_file=resolved_output_dir / "nmap_playbook.yml",
        xml_report_file=resolved_output_dir / f"{report_prefix}.xml",
        json_report_file=resolved_output_dir / f"{report_prefix}.json",
    )
