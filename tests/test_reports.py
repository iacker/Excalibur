import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from exegol_spector.reports import convert_xml_report_to_json


class ReportTests(unittest.TestCase):
    def test_convert_xml_report_to_json_preserves_nmap_shape(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            xml_file = tmp_path / "report.xml"
            json_file = tmp_path / "report.json"
            xml_file.write_text(
                """
<nmaprun>
  <host>
    <address addr="127.0.0.1" />
    <ports>
      <port portid="80">
        <state state="open" />
        <service name="http" product="nginx" version="1.25.0" />
      </port>
    </ports>
  </host>
</nmaprun>
""".strip(),
                encoding="utf-8",
            )

            convert_xml_report_to_json(xml_file, json_file)

            payload = json.loads(json_file.read_text(encoding="utf-8"))
            self.assertIn("nmaprun", payload)
            self.assertEqual(
                payload["nmaprun"]["host"]["ports"]["port"]["@portid"],
                "80",
            )
            self.assertEqual(
                payload["nmaprun"]["host"]["ports"]["port"]["service"]["@name"],
                "http",
            )


if __name__ == "__main__":
    unittest.main()
