import subprocess
from typing import Optional

from .paths import BYEDPI_EXE
from .presets import preset_args

CREATE_NO_WINDOW = 0x08000000


class ByeDpiService:
    def __init__(self) -> None:
        self._proc: Optional[subprocess.Popen] = None

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def start(self, preset: str = "youtube") -> None:
        if self.running:
            return
        if not BYEDPI_EXE.is_file():
            raise FileNotFoundError(f"Нет ciadpi.exe — запустите setup.ps1\n{BYEDPI_EXE}")
        args = [str(BYEDPI_EXE), *preset_args(preset)]
        self._proc = subprocess.Popen(
            args,
            creationflags=CREATE_NO_WINDOW,
            cwd=str(BYEDPI_EXE.parent),
        )

    def stop(self) -> None:
        if self._proc is None:
            return
        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None
