import unittest

from excalibur.banner import render_banner
from exegol_spector.knowledge import extract_scan_profile


class KnowledgeTests(unittest.TestCase):
    def test_banner_contains_sword_and_name(self) -> None:
        banner = render_banner()

        self.assertIn("/\\", banner)
        self.assertIn("Excalibur", banner)

    def test_extract_scan_profile_returns_labeled_commands(self) -> None:
        markdown = """
# Nmap Cheat Sheet

### Basic Scanning Techniques
* Scan standard
        * `nmap -sV -sC [target]`
* Scan rapide
        * `nmap -F [target]`
"""

        profile = extract_scan_profile(markdown, "basic")

        self.assertEqual(profile.scan_type, "basic")
        self.assertEqual(
            [command.label for command in profile.commands],
            ["Scan standard", "Scan rapide"],
        )
        self.assertEqual(
            [command.template for command in profile.commands],
            ["nmap -sV -sC [target]", "nmap -F [target]"],
        )


if __name__ == "__main__":
    unittest.main()
