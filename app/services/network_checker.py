from __future__ import annotations

import os
import json
import shutil
import subprocess
import tempfile

from app.services.process_utils import hidden_process_kwargs


LOW_SPACE_THRESHOLD_BYTES = 1024 * 1024 * 1024


def ping_host(ip: str, timeout_ms: int = 1000) -> bool:
    if not ip.strip():
        return False
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout_ms), ip],
            capture_output=True,
            text=True,
            timeout=max(2, timeout_ms / 1000 + 1),
            check=False,
            **hidden_process_kwargs(),
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def get_current_wifi_ssid() -> str | None:
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
            **hidden_process_kwargs(),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("ssid") and "bssid" not in stripped.lower():
            _, _, value = stripped.partition(":")
            return value.strip() or None
    return None


def get_current_network_profiles() -> list[str]:
    profiles: list[str] = []
    profiles.extend(get_active_network_profiles())
    try:
        result = subprocess.run(
            ["netsh", "lan", "show", "profiles"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
            **hidden_process_kwargs(),
        )
    except (OSError, subprocess.SubprocessError):
        result = None
    if result:
        for line in result.stdout.splitlines():
            if ":" in line:
                value = line.split(":", 1)[1].strip()
                if value:
                    profiles.append(value)

    try:
        wlan = subprocess.run(
            ["netsh", "wlan", "show", "profiles"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
            **hidden_process_kwargs(),
        )
    except (OSError, subprocess.SubprocessError):
        wlan = None
    if wlan:
        for line in wlan.stdout.splitlines():
            if ":" in line and ("Perfil" in line or "Profile" in line):
                value = line.split(":", 1)[1].strip()
                if value:
                    profiles.append(value)
    return sorted(set(profiles))


def get_active_network_profiles() -> list[str]:
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        (
            "Get-NetConnectionProfile | "
            "Select-Object Name,InterfaceAlias,InterfaceType | "
            "ConvertTo-Json -Compress"
        ),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
            check=False,
            **hidden_process_kwargs(),
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0 or not result.stdout.strip():
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = [data]

    profiles: list[str] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = str(item.get("Name") or "").strip()
        alias = str(item.get("InterfaceAlias") or "").strip()
        if name:
            profiles.append(name)
        if alias and alias.lower() != name.lower():
            profiles.append(alias)
    return profiles


def get_visible_wifi_networks() -> list[str]:
    networks: list[str] = []
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
            check=False,
            **hidden_process_kwargs(),
        )
    except (OSError, subprocess.SubprocessError):
        return networks
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped.lower().startswith("ssid"):
            continue
        if "bssid" in stripped.lower() or ":" not in stripped:
            continue
        value = stripped.split(":", 1)[1].strip()
        if value:
            networks.append(value)
    return sorted(set(networks))


def get_available_networks() -> list[str]:
    networks: list[str] = []
    current_ssid = get_current_wifi_ssid()
    if current_ssid:
        networks.append(current_ssid)
    networks.extend(get_visible_wifi_networks())
    networks.extend(get_current_network_profiles())
    return sorted(set(networks), key=str.lower)


def is_required_network_active(required_network: str | None) -> bool:
    if not required_network or not required_network.strip():
        return True
    expected = required_network.strip().lower()
    ssid = get_current_wifi_ssid()
    if ssid and ssid.lower() == expected:
        return True
    return expected in {profile.lower() for profile in get_current_network_profiles()}


def is_destination_accessible(path: str) -> bool:
    return bool(path.strip()) and os.path.exists(path)


def is_destination_writable(path: str) -> bool:
    if not is_destination_accessible(path) or not os.path.isdir(path):
        return False
    test_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path,
            prefix=".nas_backup_write_test_",
            suffix=".tmp",
            delete=False,
        ) as handle:
            test_path = handle.name
            handle.write("write test")
        return True
    except OSError:
        return False
    finally:
        if test_path:
            try:
                os.remove(test_path)
            except OSError:
                pass


def get_free_space(path: str) -> tuple[int | None, str | None]:
    try:
        usage = shutil.disk_usage(path)
    except OSError as exc:
        return None, str(exc)
    return usage.free, None


def has_enough_destination_space(path: str) -> tuple[bool, str]:
    free_bytes, error = get_free_space(path)
    if free_bytes is None:
        return True, "Espacio libre desconocido"
    if free_bytes < LOW_SPACE_THRESHOLD_BYTES:
        return False, "Menos de 1 GB libre en destino"
    return True, "Espacio suficiente"


def can_run_task(task) -> tuple[bool, str]:
    if not int(task.enabled):
        return False, "Tarea desactivada"
    if not is_required_network_active(task.required_network):
        return False, "Red requerida no activa"
    if not is_destination_accessible(task.destination_path):
        return False, "Destino no accesible"
    if not is_destination_writable(task.destination_path):
        return False, "Sin permiso de escritura en destino"
    if not ping_host(task.server_ip):
        return True, "Destino accesible; el ping no responde"
    return True, "Lista para ejecutar"
