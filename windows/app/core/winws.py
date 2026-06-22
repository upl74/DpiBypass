"""zapret winws.exe — packet-level DPI bypass for Discord (WinDivert)."""

from __future__ import annotations

import os
import subprocess
import time
from typing import Optional

from .admin import is_admin
from .config import load_config
from .paths import WINWS_EXE, ZAPRET_ROOT
from .zapret_presets import default_preset_name

CREATE_NO_WINDOW = 0x08000000
_WINWS_START_TIMEOUT_S = 8.0


def is_available() -> bool:
    return WINWS_EXE.is_file()


class WinWsService:
    def __init__(self) -> None:
        self._launcher: Optional[subprocess.Popen] = None

    @property
    def running(self) -> bool:
        return _find_winws_pid() is not None

    def start(self, preset_name: str | None = None) -> None:
        if self.running and preset_name is None:
            return
        if preset_name is not None:
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
        bat_path = ZAPRET_ROOT / name
        if not bat_path.is_file():
            bat_path = ZAPRET_ROOT / default_preset_name()
        if not bat_path.is_file():
            raise FileNotFoundError(f"Пресет zapret не найден: {name}")

        env = os.environ.copy()
        env["NO_UPDATE_CHECK"] = "1"

        self._launcher = subprocess.Popen(
            ["cmd.exe", "/c", str(bat_path)],
            cwd=str(ZAPRET_ROOT),
            creationflags=CREATE_NO_WINDOW,
            env=env,
        )

        if not _wait_for_winws():
            code = self._launcher.poll()
            self._launcher = None
            raise RuntimeError(
                f"winws.exe не запустился ({bat_path.name})"
                + (f", код {code}" if code is not None else "")
            )

    def start_preset(self, preset_name: str) -> None:
        self.start(preset_name)

    def stop(self) -> None:
        if self._launcher is not None and self._launcher.poll() is None:
            try:
                self._launcher.terminate()
                self._launcher.wait(timeout=2)
            except (subprocess.TimeoutExpired, OSError):
                pass
        self._launcher = None
        _kill_orphan_winws()


def _wait_for_winws() -> bool:
    deadline = time.monotonic() + _WINWS_START_TIMEOUT_S
    while time.monotonic() < deadline:
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
