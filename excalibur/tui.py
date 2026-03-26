from __future__ import annotations

import curses
import json
from pathlib import Path

from exegol_spector.knowledge import SCAN_HEADINGS, extract_scan_profile, load_markdown_file
from exegol_spector.nmap_report import parse_host_reports

from .banner import render_banner
from .runtime import collect_runtime_command_status, extract_container_packages, extract_project_modules


RED = 1
RED_HIGHLIGHT = 2
RED_PANEL = 3


def run_tui(root_dir: Path) -> int:
    curses.wrapper(lambda stdscr: ExcaliburTUI(stdscr, root_dir).run())
    return 0


class ExcaliburTUI:
    def __init__(self, stdscr, root_dir: Path) -> None:
        self.stdscr = stdscr
        self.root_dir = root_dir
        self.selection = 0
        self.focus = "profiles"
        self.status_message = "Arrows to navigate | Tab to switch panes | q to quit"
        self.profile_rows = self._load_profiles()
        self.tool_rows = self._load_tool_rows()
        self.artifact_rows = self._load_artifact_rows()

    def run(self) -> None:
        try:
            curses.curs_set(0)
        except curses.error:
            pass

        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(RED, curses.COLOR_RED, -1)
            curses.init_pair(RED_HIGHLIGHT, curses.COLOR_BLACK, curses.COLOR_RED)
            curses.init_pair(RED_PANEL, curses.COLOR_WHITE, curses.COLOR_RED)
        self.stdscr.keypad(True)

        while True:
            self.artifact_rows = self._load_artifact_rows()
            self._draw()
            key = self.stdscr.getch()

            if key in (ord("q"), 27):
                return
            if key == ord("\t"):
                self.focus = "artifacts" if self.focus == "profiles" else "profiles"
                self.selection = 0
                continue
            if key in (curses.KEY_DOWN, ord("j")):
                self._move_selection(1)
                continue
            if key in (curses.KEY_UP, ord("k")):
                self._move_selection(-1)
                continue
            if key in (ord("r"),):
                self.profile_rows = self._load_profiles()
                self.tool_rows = self._load_tool_rows()
                self.artifact_rows = self._load_artifact_rows()
                self.status_message = "Refreshed"
                continue

    def _move_selection(self, offset: int) -> None:
        rows = self.profile_rows if self.focus == "profiles" else self.artifact_rows
        if not rows:
            self.selection = 0
            return
        self.selection = max(0, min(self.selection + offset, len(rows) - 1))

    def _draw(self) -> None:
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        self._draw_header(width)
        mid = max(38, width // 2)
        self._draw_box(0, 7, mid, height - 10, "Profiles")
        self._draw_box(mid + 1, 7, width - mid - 1, height - 16, "Artifacts")
        self._draw_box(mid + 1, height - 8, width - mid - 1, 6, "Runtime")
        self._draw_status(width, height)
        self._draw_profiles(1, 8, mid - 2, height - 12)
        self._draw_artifacts(mid + 2, 8, width - mid - 4, height - 18)
        self._draw_runtime(mid + 2, height - 7, width - mid - 4, 4)
        self.stdscr.refresh()

    def _draw_header(self, width: int) -> None:
        banner_lines = render_banner().splitlines()
        for index, line in enumerate(banner_lines[:6]):
            self.stdscr.addnstr(index, 1, line, width - 2, curses.color_pair(RED))
        title = "K9s-inspired terminal cockpit"
        self.stdscr.addnstr(0, max(1, width - len(title) - 3), title, len(title), curses.A_BOLD | curses.color_pair(RED))

    def _draw_box(self, x: int, y: int, width: int, height: int, title: str) -> None:
        if width < 10 or height < 4:
            return
        self.stdscr.attron(curses.color_pair(RED))
        self.stdscr.addstr(y, x, "+" + "-" * (width - 2) + "+")
        for row in range(y + 1, y + height - 1):
            self.stdscr.addstr(row, x, "|")
            self.stdscr.addstr(row, x + width - 1, "|")
        self.stdscr.addstr(y + height - 1, x, "+" + "-" * (width - 2) + "+")
        self.stdscr.addnstr(y, x + 2, f"[ {title} ]", width - 4, curses.A_BOLD | curses.color_pair(RED))
        self.stdscr.attroff(curses.color_pair(RED))

    def _draw_status(self, width: int, height: int) -> None:
        status = self.status_message[: max(1, width - 2)]
        self.stdscr.addnstr(height - 1, 0, " " * max(0, width - 1), max(0, width - 1), curses.color_pair(RED_PANEL))
        self.stdscr.addnstr(height - 1, 1, status, max(0, width - 2), curses.A_BOLD | curses.color_pair(RED_PANEL))

    def _draw_profiles(self, x: int, y: int, width: int, height: int) -> None:
        for index, row in enumerate(self.profile_rows[:height]):
            style = curses.color_pair(RED_HIGHLIGHT) if self.focus == "profiles" and index == self.selection else curses.color_pair(RED)
            text = f"{row['name']:<11} {row['status']:<7} {row['count']:>2} cmd(s)"
            self.stdscr.addnstr(y + index, x, text, width, style)

    def _draw_artifacts(self, x: int, y: int, width: int, height: int) -> None:
        if not self.artifact_rows:
            self.stdscr.addnstr(y, x, "No artifacts yet", width, curses.color_pair(RED))
            return

        for index, row in enumerate(self.artifact_rows[:height]):
            style = curses.color_pair(RED_HIGHLIGHT) if self.focus == "artifacts" and index == self.selection else curses.color_pair(RED)
            self.stdscr.addnstr(y + index, x, row, width, style)

    def _draw_runtime(self, x: int, y: int, width: int, height: int) -> None:
        lines = self.tool_rows[:height]
        for index, line in enumerate(lines):
            self.stdscr.addnstr(y + index, x, line, width, curses.color_pair(RED))

    def _load_profiles(self) -> list[dict[str, object]]:
        knowledge_file = self.root_dir / "Cheetsheet.md" / "Nmap.md"
        markdown = load_markdown_file(knowledge_file)
        rows = []
        for scan_type in sorted(SCAN_HEADINGS):
            try:
                profile = extract_scan_profile(markdown, scan_type)
                rows.append({"name": scan_type, "status": "ready", "count": len(profile.commands)})
            except ValueError:
                rows.append({"name": scan_type, "status": "missing", "count": 0})
        return rows

    def _load_tool_rows(self) -> list[str]:
        docker_packages = extract_container_packages(self.root_dir / "Dockerfile")
        project_modules = extract_project_modules(self.root_dir / "Modules")
        command_status = collect_runtime_command_status(["nmap", "ansible-playbook", "docker", "git"])

        package_text = "container: " + ", ".join(docker_packages[:5])
        command_text = "commands: " + ", ".join(
            f"{name}={'ok' if ok else 'missing'}" for name, ok in command_status.items()
        )
        module_text = f"modules: {len(project_modules)} file(s) in Modules/"

        return [package_text, command_text, module_text]

    def _load_artifact_rows(self) -> list[str]:
        artifacts_dir = self.root_dir / "artifacts"
        rows = []
        if not artifacts_dir.exists():
            return rows

        report_file = artifacts_dir / "nmap_report.json"
        if report_file.exists():
            try:
                report_data = json.loads(report_file.read_text(encoding="utf-8"))
                for host in parse_host_reports(report_data):
                    services = ", ".join(f"{port.port}/{port.service_name or 'unknown'}" for port in host.open_ports)
                    rows.append(f"{host.address or 'unknown'} | {services or 'no open ports'}")
            except Exception:
                rows.append("nmap_report.json present but unreadable")

        for artifact in sorted(artifacts_dir.iterdir()):
            if artifact.is_file():
                rows.append(f"file | {artifact.name}")

        return rows[:32]
