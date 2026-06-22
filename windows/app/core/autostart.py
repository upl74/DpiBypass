"""Windows autostart: registry (обычный) или задача планировщика (Discord / WinDivert)."""

from __future__ import annotations

import subprocess
import sys
import winreg

from .admin import is_admin
from .paths import WINDOWS_ROOT

CREATE_NO_WINDOW = 0x08000000
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "DpiBypass"
_TASK_NAME = "DpiBypass"


def _executable_path() -> str:
    if getattr(sys, "frozen", False):
        return str(sys.executable)
    pythonw = WINDOWS_ROOT / "venv" / "Scripts" / "pythonw.exe"
    main_py = WINDOWS_ROOT / "app" / "main.py"
    if pythonw.is_file() and main_py.is_file():
        return str(pythonw)
    bat = WINDOWS_ROOT / "DpiBypass.bat"
    if bat.is_file():
        return str(bat)
    raise FileNotFoundError("Не найден DpiBypass.exe для автозапуска")


def _launch_command() -> list[str]:
    exe = _executable_path()
    if exe.endswith(".bat"):
        return ["cmd.exe", "/c", exe, "--autostart"]
    return [exe, "--autostart"]


def _launch_command_line() -> str:
    return subprocess.list2cmdline(_launch_command())


def _registry_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, _VALUE_NAME)
            return True
    except (FileNotFoundError, OSError):
        return False


def _set_registry(enabled: bool) -> None:
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


def _task_exists() -> bool:
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", _TASK_NAME],
        creationflags=CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def _delete_task() -> None:
    if not _task_exists():
        return
    subprocess.run(
        ["schtasks", "/Delete", "/TN", _TASK_NAME, "/F"],
        creationflags=CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _create_task() -> None:
    tr = _launch_command_line()
    args = [
        "schtasks",
        "/Create",
        "/TN",
        _TASK_NAME,
        "/TR",
        tr,
        "/SC",
        "ONLOGON",
        "/RL",
        "HIGHEST",
        "/F",
    ]
    result = subprocess.run(
        args,
        creationflags=CREATE_NO_WINDOW,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return
    err = (result.stderr or result.stdout or "").lower()
    if "access is denied" in err or "отказано в доступе" in err:
        raise PermissionError("task_admin")
    raise RuntimeError(result.stderr or result.stdout or "schtasks failed")


def _create_task_elevated() -> None:
    tr = _launch_command_line().replace('"', '`"')
    ps = (
        f'schtasks /Create /TN "{_TASK_NAME}" /TR "{tr}" '
        f'/SC ONLOGON /RL HIGHEST /F'
    )
    import ctypes

    rc = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        "powershell.exe",
        f'-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "{ps}"',
        None,
        0,
    )
    if rc <= 32:
        raise OSError(f"Не удалось создать задачу автозапуска (код {rc})")


def is_enabled() -> bool:
    return _registry_enabled() or _task_exists()


def uses_elevated_task() -> bool:
    return _task_exists()


def set_enabled(enabled: bool, *, elevated: bool = False) -> None:
    _set_registry(False)
    _delete_task()
    if not enabled:
        return

    if elevated:
        try:
            _create_task()
        except PermissionError:
            if is_admin():
                raise
            _create_task_elevated()
        return

    _set_registry(True)


def ensure_discord_autostart(enabled: bool) -> None:
    """Включить автозагрузку с повышенными правами для WinDivert (один раз UAC)."""
    set_enabled(enabled, elevated=True)
