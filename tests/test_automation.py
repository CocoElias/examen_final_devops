"""Pruebas unitarias para los módulos de automatización de TechCorp."""

import json
import pytest
from src.cisco_apis.dnac_inventory import save_report
from src.netconf_restconf.iosxe_manager import restconf_create_loopback


def test_save_report_creates_valid_json(tmp_path):
    """Verifica que el reporte de DNA Center genere un JSON válido."""
    sample_devices = [
        {
            "hostname": "sw1",
            "managementIpAddress": "10.10.20.175",
            "platformId": "C9300-24P",
            "reachabilityStatus": "Reachable",
        }
    ]
    output_file = tmp_path / "dnac_test.json"
    save_report(sample_devices, str(output_file))

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["company"] == "TechCorp"
    assert data["total_devices"] == 1
    assert data["devices"][0]["hostname"] == "sw1"


def test_restconf_rejects_invalid_interface_name():
    """Verifica que RESTCONF rechace interfaces que no sean Loopback."""
    with pytest.raises(ValueError):
        restconf_create_loopback(
            "127.0.0.1", "443", ("user", "pass"),
            "GigabitEthernet1", "10.0.0.1", "255.255.255.0"
        )