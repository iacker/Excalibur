import unittest
from pathlib import Path

from exegol_spector.models import RuntimePaths, ScanCommand, ScanProfile
from exegol_spector.playbooks import build_playbook


class PlaybookTests(unittest.TestCase):
    def test_build_playbook_renders_targets_and_report_path(self) -> None:
        tmp_path = Path("/tmp/exegolspector-test")
        paths = RuntimePaths(
            root_dir=tmp_path,
            knowledge_file=tmp_path / "Nmap.md",
            output_dir=tmp_path / "artifacts",
            playbook_file=tmp_path / "artifacts" / "nmap_playbook.yml",
            xml_report_file=tmp_path / "artifacts" / "nmap_report.xml",
            json_report_file=tmp_path / "artifacts" / "nmap_report.json",
        )
        profile = ScanProfile(
            scan_type="basic",
            heading="### Basic Scanning Techniques",
            commands=[ScanCommand(label="Standard", template="nmap -sV [target]")],
        )

        playbook = build_playbook(profile, ["127.0.0.1"], paths)

        task = playbook[0]["tasks"][0]
        self.assertEqual(task["name"], "Nmap | Standard")
        self.assertEqual(
            task["ansible.builtin.command"],
            f"nmap -sV 127.0.0.1 -oX {paths.xml_report_file}",
        )


if __name__ == "__main__":
    unittest.main()
