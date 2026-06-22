"""zapret winws.exe — packet-level DPI bypass for Discord (WinDivert)."""

from __future__ import annotations

import os
import subprocess
import time
from typing import Optional

from .admin import is_admin
from .config import load_config
from .paths import WINWS_EXE, ZAPRET_BIN_DIR, ZAPRET_ROOT
from .zapret_presets import default_preset_name, resolve_preset_args

CREATE_NO_WINDOW = 0x08000000
_WINWS_START_TIMEOUT_S = 8.0


def is_available() -> bool:
    return WINWS_EXE.is_file()


def _hidden_startupinfo() -> subprocess.STARTUPINFO:
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0  # SW_HIDE
    return si


def _prepare_zapret_lists() -> None:
    subprocess.run(
        ["cmd.exe", "/c", "service.bat", "load_user_lists"],
        cwd=str(ZAPRET_ROOT),
        creationflags=CREATE_NO_WINDOW,
        env={**os.environ, "NO_UPDATE_CHECK": "1"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class WinWsService:
    def __init__(self) -> None:
        self._proc: Optional[subprocess.Popen] = None

    @property
    def running(self) -> bool:
        if self._proc is not None and self._proc.poll() is None:
            return True
        return _find_winws_pid() is not None

    def start(self, preset_name: str | None = None) -> None:
        if self.running and preset_name is None:
            return
        if preset_name is not None or self.running:
            self.stop()

        if not is_available():
            raise FileNotFoundError(
                "Нет winws.exe (zapret).\n"
                "Нажмите «Компоненты» для загрузки."
            )
        if not is_admin():
            raise PermissionError(
                "Discord требует права администратора (драйвер WinDivert).\n"
                "Закройте приложение и запустите DpiBypass «От имени администратора»."
            )

        name = preset_name or load_config().zapret_preset or default_preset_name()
        _prepare_zapret_lists()
        args = resolve_preset_args(name)

        self._proc = subprocess.Popen(
            args,
            cwd=str(ZAPRET_BIN_DIR),
            creationflags=CREATE_NO_WINDOW,
            startupinfo=_hidden_startupinfo(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not _wait_for_winws(self._proc):
            code = self._proc.poll()
            self._proc = None
            raise RuntimeError(
                f"winws.exe не запустился ({name})"
                + (f", код {code}" if code is not None else "")
            )

    def start_preset(self, preset_name: str) -> None:
        self.start(preset_name)

    def stop(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=2)
            except (subprocess.TimeoutExpired, OSError):
                try:
                    self._proc.kill()
                except OSError:
                    pass
        self._proc = None
        _kill_orphan_winws()


def _wait_for_winws(proc: subprocess.Popen) -> bool:
    deadline = time.monotonic() + _WINWS_START_TIMEOUT_S
    while time.monotonic() < deadline:
        if proc.poll() is not None and proc.returncode not in (None, 0):
            return False
        if _find_winws_pid() is not None:
            return True
        time.sleep(0.15)
    return _find_winws_pid() is not None


def _find_winws_pid() -> int | None:
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq winws.exe", "/FO", "CSV", "/NH"],
            creationflags=CREATE_NO_WINDOW,
            text=True,
            errors="replace",
        )
        for line in out.splitlines():
            if "winws.exe" in line.lower():
                parts = line.split(",")
                if len(parts) >= 2:
                    return int(parts[1].strip('"'))
    except Exception:
        pass
    return None


def _kill_orphan_winws() -> None:
    subprocess.run(
        ["taskkill", "/IM", "winws.exe", "/F"],
        creationflags=CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
