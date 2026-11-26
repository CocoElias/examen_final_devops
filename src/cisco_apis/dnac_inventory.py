"""Módulo de consulta de inventario en Cisco DNA Center para TechCorp."""

import json
import os
from datetime import datetime, timezone
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()


def get_dnac_token(host: str, user: str, password: str) -> str:
    """Obtiene el token de autenticación de Cisco DNA Center."""
    url = f"https://{host}/dna/system/api/v1/auth/token"
    response = requests.post(
        url,
        auth=(user, password),
        headers={"Content-Type": "application/json"},
        verify=False,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["Token"]


def get_network_devices(host: str, token: str) -> list:
    """Consulta el inventario de dispositivos de red en DNA Center."""
    url = f"https://{host}/dna/intent/api/v1/network-device"
    headers = {
        "X-Auth-Token": token,
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers, verify=False, timeout=15)
    response.raise_for_status()
    return response.json().get("response", [])


def save_report(devices: list, output_path: str) -> None:
    """Guarda el reporte de inventario en formato JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    report = {
        "company": "TechCorp",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_devices": len(devices),
        "devices": [
            {
                "hostname": d.get("hostname", "N/A"),
                "ip": d.get("managementIpAddress", "N/A"),
                "platform": d.get("platformId", "N/A"),
                "status": d.get("reachabilityStatus", "N/A"),
            }
            for d in devices
        ],
    }
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)


def main() -> None:
    """Flujo principal de consulta y reporte de inventario."""
    host = os.getenv("DNAC_HOST")
    user = os.getenv("DNAC_USER")
    password = os.getenv("DNAC_PASS")

    if not all([host, user, password]):
        raise ValueError("Faltan variables DNAC en el archivo .env")

    try:
        print(f"[TechCorp] Autenticando en DNA Center ({host})...")
        token = get_dnac_token(host, user, password)
        devices = get_network_devices(host, token)
        print(f"[TechCorp] Dispositivos encontrados: {len(devices)}\n")
        print(f"{'HOSTNAME':<25} {'IP GESTIÓN':<16} {'ESTADO':<12}")
        print("-" * 55)
        for dev in devices:
            name = dev.get("hostname", "N/A")
            ip_addr = dev.get("managementIpAddress", "N/A")
            status = dev.get("reachabilityStatus", "N/A")
            print(f"{name:<25} {ip_addr:<16} {status:<12}")

        report_file = "reports/dnac_inventory.json"
        save_report(devices, report_file)
        print(f"\n[TechCorp] Reporte guardado en: {report_file}")
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Fallo al conectar con DNA Center: {err}")


if __name__ == "__main__":
    main()
