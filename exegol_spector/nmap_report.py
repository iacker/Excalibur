from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OpenPort:
    port: int
    service_name: str
    service_product: str
    service_version: str


@dataclass(frozen=True)
class HostReport:
    address: str
    open_ports: list[OpenPort]


def ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def parse_host_reports(report_data: dict) -> list[HostReport]:
    hosts = ensure_list(report_data.get("nmaprun", {}).get("host"))
    parsed_hosts: list[HostReport] = []

    for host in hosts:
        address = host.get("address", {}).get("@addr", "")
        open_ports: list[OpenPort] = []

        for port_data in ensure_list(host.get("ports", {}).get("port")):
            if port_data.get("state", {}).get("@state") != "open":
                continue

            port_id = port_data.get("@portid")
            if port_id is None:
                continue

            try:
                normalized_port = int(port_id)
            except (TypeError, ValueError):
                continue

            service = port_data.get("service", {})
            open_ports.append(
                OpenPort(
                    port=normalized_port,
                    service_name=service.get("@name", ""),
                    service_product=service.get("@product", ""),
                    service_version=service.get("@version", ""),
                )
            )

        parsed_hosts.append(HostReport(address=address, open_ports=open_ports))

    return parsed_hosts
