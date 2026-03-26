from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

from exegol_spector.nmap_report import parse_host_reports


CVE_API_URL = "https://cve.circl.lu/api/search/"
DEFAULT_OUTPUT = "vulnerabilities_report.json"
REQUEST_TIMEOUT_SECONDS = 10


def load_nmap_report(nmap_json_path: Path) -> dict:
    try:
        return json.loads(nmap_json_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(f"Nmap JSON report not found: {nmap_json_path}") from None


def build_service_queries(service_name: str, product: str, version: str) -> list[str]:
    queries = []
    for value in (
        f"{product} {version}".strip(),
        product.strip(),
        service_name.strip(),
    ):
        if value and value not in queries:
            queries.append(value)
    return queries


def get_cve_for_query(query: str) -> list[dict]:
    try:
        response = requests.get(
            f"{CVE_API_URL}{query}",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as error:
        print(f"CVE lookup failed for '{query}': {error}")
        return []

    if isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            return payload["data"]
        if isinstance(payload.get("results"), list):
            return payload["results"]

    return []


def analyze_services_for_vulnerabilities(nmap_data: dict) -> list[dict]:
    findings: list[dict] = []

    for host in parse_host_reports(nmap_data):
        for port in host.open_ports:
            queries = build_service_queries(
                port.service_name,
                port.service_product,
                port.service_version,
            )
            cve_data: list[dict] = []
            matched_query = ""

            for query in queries:
                cve_data = get_cve_for_query(query)
                if cve_data:
                    matched_query = query
                    break

            if not cve_data:
                continue

            findings.append(
                {
                    "ip_address": host.address,
                    "port": port.port,
                    "service": port.service_name,
                    "product": port.service_product,
                    "version": port.service_version,
                    "matched_query": matched_query,
                    "cve": cve_data,
                }
            )

    return findings


def save_report_to_file(report: list[dict], filename: Path) -> None:
    filename.write_text(json.dumps(report, indent=4), encoding="utf-8")
    print(f"Vulnerability report written to: {filename}")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 Modules/cve_search.py <nmap_report.json> [output.json]")
        return 1

    report_path = Path(sys.argv[1]).resolve()
    output_path = (
        Path(sys.argv[2]).resolve()
        if len(sys.argv) > 2
        else report_path.parent / DEFAULT_OUTPUT
    )

    try:
        nmap_data = load_nmap_report(report_path)
    except FileNotFoundError as error:
        print(error)
        return 1

    findings = analyze_services_for_vulnerabilities(nmap_data)
    save_report_to_file(findings, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
