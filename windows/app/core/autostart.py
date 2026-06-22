"""Windows autostart via HKCU Run registry."""

from __future__ import annotations

import subprocess
import sys
import winreg

from .paths import WINDOWS_ROOT

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "DpiBypass"


def _launch_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--autostart"]

    pythonw = WINDOWS_ROOT / "venv" / "Scripts" / "pythonw.exe"
    main_py = WINDOWS_ROOT / "app" / "main.py"
    if pythonw.is_file() and main_py.is_file():
        return [str(pythonw), str(main_py), "--autostart"]

    bat = WINDOWS_ROOT / "DpiBypass.bat"
    if bat.is_file():
        return ["cmd.exe", "/c", str(bat)]
    raise FileNotFoundError("Не найден DpiBypass.exe или DpiBypass.bat для автозапуска")


def is_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, _VALUE_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def set_enabled(enabled: bool) -> None:
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        _RUN_KEY,
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        if enabled:
            cmd = subprocess.list2cmdline(_launch_command())
            winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, _VALUE_NAME)
            except FileNotFoundError:
                pass
