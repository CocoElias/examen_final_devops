"""Automatización RESTCONF y NETCONF en Cisco IOS-XE para TechCorp."""

import json
import os
from datetime import datetime, timezone
import requests
import urllib3
from dotenv import load_dotenv
from ncclient import manager

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()


def restconf_get_interfaces(host: str, port: str, auth: tuple) -> list:
    """Consulta las interfaces actuales vía RESTCONF (Pre/Post-check)."""
    url = (
        f"https://{host}:{port}/restconf/data/"
        "ietf-interfaces:interfaces"
    )
    headers = {
        "Accept": "application/yang-data+json",
        "Content-Type": "application/yang-data+json",
    }
    resp = requests.get(
        url, auth=auth, headers=headers, verify=False, timeout=20
    )
    resp.raise_for_status()
    return resp.json().get("ietf-interfaces:interfaces", {}).get(
        "interface", []
    )


def restconf_create_loopback(
    host: str, port: str, auth: tuple, name: str, ip: str, mask: str
) -> int:
    """Crea o actualiza una interfaz Loopback validando el payload JSON."""
    if not name.startswith("Loopback"):
        raise ValueError("El nombre de interfaz debe iniciar con Loopback")

    url = (
        f"https://{host}:{port}/restconf/data/"
        f"ietf-interfaces:interfaces/interface={name}"
    )
    headers = {
        "Accept": "application/yang-data+json",
        "Content-Type": "application/yang-data+json",
    }
    payload = {
        "ietf-interfaces:interface": {
            "name": name,
            "description": "Configurada automaticamente por TechCorp DevOps",
            "type": "iana-if-type:softwareLoopback",
            "enabled": True,
            "ietf-ip:ipv4": {
                "address": [{"ip": ip, "netmask": mask}]
            },
        }
    }
    resp = requests.put(
        url,
        auth=auth,
        headers=headers,
        json=payload,
        verify=False,
        timeout=20,
    )
    resp.raise_for_status()
    return resp.status_code


def netconf_get_hostname(host: str, port: int, user: str, pwd: str) -> str:
    """Consulta el hostname del router usando NETCONF con filtro subtree."""
    hostname_filter = """
    <filter>
      <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
        <hostname/>
      </native>
    </filter>
    """
    with manager.connect(
        host=host,
        port=port,
        username=user,
        password=pwd,
        hostkey_verify=False,
        timeout=20,
    ) as conn:
        reply = conn.get_config(source="running", filter=hostname_filter)
        return reply.xml


def main() -> None:
    """Ejecuta validación antes/después con RESTCONF y consulta NETCONF."""
    host = os.getenv("IOSXE_HOST")
    user = os.getenv("IOSXE_USER")
    pwd = os.getenv("IOSXE_PASS")
    r_port = os.getenv("IOSXE_RESTCONF_PORT", "443")
    n_port = int(os.getenv("IOSXE_NETCONF_PORT", "830"))
    auth = (user, pwd)

    print(f"[TechCorp] Iniciando automatización en {host}...")

    before = restconf_get_interfaces(host, r_port, auth)
    print(f"[Pre-check RESTCONF] Interfaces iniciales: {len(before)}")

    status = restconf_create_loopback(
        host, r_port, auth, "Loopback99", "10.99.99.1", "255.255.255.0"
    )
    print(f"[RESTCONF PUT] Loopback99 aplicada (HTTP {status})")

    after = restconf_get_interfaces(host, r_port, auth)
    found = any(i.get("name") == "Loopback99" for i in after)
    print(
        f"[Post-check RESTCONF] Interfaces finales: {len(after)} | "
        f"Loopback99 verificada: {found}"
    )

    nc_xml = netconf_get_hostname(host, n_port, user, pwd)
    print("[NETCONF] Filtro subtree ejecutado correctamente.")

    report = {
        "company": "TechCorp",
        "host": host,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "restconf_status": status,
        "interfaces_before": len(before),
        "interfaces_after": len(after),
        "loopback99_verified": found,
        "netconf_connected": "<hostname>" in nc_xml,
    }
    os.makedirs("reports", exist_ok=True)
    with open("reports/iosxe_automation.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("[TechCorp] Reporte guardado en: reports/iosxe_automation.json")


if __name__ == "__main__":
    main()
