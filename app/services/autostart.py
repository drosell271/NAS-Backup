from __future__ import annotations

import sys
import winreg
from pathlib import Path

from app.config import RUN_REGISTRY_NAME


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def enable_autostart(command: str) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, RUN_REGISTRY_NAME, 0, winreg.REG_SZ, command)


def disable_autostart() -> None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, RUN_REGISTRY_NAME)
    except FileNotFoundError:
        pass


def is_autostart_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, RUN_REGISTRY_NAME)
            return True
    except FileNotFoundError:
        return False


def build_autostart_command(main_path: Path, minimized: bool = False) -> str:
    minimized_argument = " --minimized" if minimized else ""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"{minimized_argument}'
    executable = Path(sys.executable)
    pythonw = executable.with_name("pythonw.exe")
    if pythonw.exists():
        executable = pythonw
    return f'"{executable}" "{main_path}"{minimized_argument}'
