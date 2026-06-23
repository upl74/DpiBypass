"""Autostart for DpiBypass Lite (registry only, no admin task)."""

from __future__ import annotations

import subprocess
import sys
import winreg

from .paths import WINDOWS_ROOT

CREATE_NO_WINDOW = 0x08000000
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "DpiBypassLite"


def _executable_path() -> str:
    if getattr(sys, "frozen", False):
        return str(sys.executable)
    pythonw = WINDOWS_ROOT / "venv" / "Scripts" / "pythonw.exe"
    main_py = WINDOWS_ROOT / "app" / "main_lite.py"
    if pythonw.is_file() and main_py.is_file():
        return f'"{pythonw}" "{main_py}"'
    bat = WINDOWS_ROOT / "DpiBypassLite.bat"
    if bat.is_file():
        return str(bat)
    raise FileNotFoundError("Не найден DpiBypassLite для автозапуска")


def _launch_command_line() -> str:
    if getattr(sys, "frozen", False):
        return subprocess.list2cmdline([str(sys.executable), "--autostart"])
    exe = _executable_path()
    if exe.endswith(".bat"):
        return subprocess.list2cmdline([exe, "--autostart"])
    return f"{exe} --autostart"


def is_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, _VALUE_NAME)
            return True
    except (FileNotFoundError, OSError):
        return False


def set_enabled(enabled: bool) -> None:
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        _RUN_KEY,
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        if enabled:
            winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, _launch_command_line())
        else:
            try:
                winreg.DeleteValue(key, _VALUE_NAME)
            except FileNotFoundError:
                pass
