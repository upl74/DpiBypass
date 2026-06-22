"""zapret winws.exe — packet-level DPI bypass for Discord (WinDivert)."""

from __future__ import annotations

import subprocess
from typing import Optional

from .admin import is_admin
from .config import load_config
from .paths import WINWS_EXE, ZAPRET_BIN_DIR
from .zapret_presets import default_preset_name, resolve_preset_args

CREATE_NO_WINDOW = 0x08000000


def is_available() -> bool:
    return WINWS_EXE.is_file()


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
        args = resolve_preset_args(name)
        self._proc = subprocess.Popen(
            args,
            cwd=str(ZAPRET_BIN_DIR),
            creationflags=CREATE_NO_WINDOW,
        )
        if self._proc.poll() is not None:
            code = self._proc.returncode
            self._proc = None
            raise RuntimeError(f"winws.exe завершился с кодом {code}")

    def start_preset(self, preset_name: str) -> None:
        self.start(preset_name)

    def stop(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None
        _kill_orphan_winws()


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
