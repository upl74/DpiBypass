"""zapret winws.exe — packet-level DPI bypass for Discord (WinDivert)."""

from __future__ import annotations

import subprocess
from typing import Optional

from .admin import is_admin
from .paths import WINWS_EXE, ZAPRET_BIN_DIR, ZAPRET_LISTS_DIR, ZAPRET_ROOT

CREATE_NO_WINDOW = 0x08000000


def is_available() -> bool:
    return WINWS_EXE.is_file()


def _winws_args() -> list[str]:
    """Strategy from zapret-discord-youtube general.bat (Discord + voice UDP)."""
    b = str(ZAPRET_BIN_DIR).rstrip("\\") + "\\"
    lists = str(ZAPRET_LISTS_DIR).rstrip("\\") + "\\"

    return [
        str(WINWS_EXE),
        "--wf-tcp=80,443,2053,2083,2087,2096,8443",
        "--wf-udp=443,19294-19344,50000-50100",
        "--filter-udp=443",
        f"--hostlist={lists}list-general.txt",
        f"--hostlist={lists}list-general-user.txt",
        f"--hostlist-exclude={lists}list-exclude.txt",
        f"--hostlist-exclude={lists}list-exclude-user.txt",
        f"--ipset-exclude={lists}ipset-exclude.txt",
        f"--ipset-exclude={lists}ipset-exclude-user.txt",
        "--dpi-desync=fake",
        "--dpi-desync-repeats=6",
        f"--dpi-desync-fake-quic={b}quic_initial_www_google_com.bin",
        "--new",
        "--filter-udp=19294-19344,50000-50100",
        "--filter-l7=discord,stun",
        "--dpi-desync=fake",
        f"--dpi-desync-fake-discord={b}quic_initial_dbankcloud_ru.bin",
        f"--dpi-desync-fake-stun={b}quic_initial_dbankcloud_ru.bin",
        "--dpi-desync-repeats=6",
        "--new",
        "--filter-tcp=2053,2083,2087,2096,8443",
        "--hostlist-domains=discord.media",
        "--dpi-desync=multisplit",
        "--dpi-desync-split-seqovl=681",
        "--dpi-desync-split-pos=1",
        f"--dpi-desync-split-seqovl-pattern={b}tls_clienthello_www_google_com.bin",
        "--new",
        "--filter-tcp=443",
        f"--hostlist={lists}list-google.txt",
        "--ip-id=zero",
        "--dpi-desync=multisplit",
        "--dpi-desync-split-seqovl=681",
        "--dpi-desync-split-pos=1",
        f"--dpi-desync-split-seqovl-pattern={b}tls_clienthello_www_google_com.bin",
        "--new",
        "--filter-tcp=80,443",
        f"--hostlist={lists}list-general.txt",
        f"--hostlist={lists}list-general-user.txt",
        f"--hostlist-exclude={lists}list-exclude.txt",
        f"--hostlist-exclude={lists}list-exclude-user.txt",
        f"--ipset-exclude={lists}ipset-exclude.txt",
        f"--ipset-exclude={lists}ipset-exclude-user.txt",
        "--dpi-desync=multisplit",
        "--dpi-desync-split-seqovl=568",
        "--dpi-desync-split-pos=1",
        f"--dpi-desync-split-seqovl-pattern={b}tls_clienthello_4pda_to.bin",
        "--new",
        "--filter-udp=443",
        f"--ipset={lists}ipset-all.txt",
        f"--hostlist-exclude={lists}list-exclude.txt",
        f"--hostlist-exclude={lists}list-exclude-user.txt",
        f"--ipset-exclude={lists}ipset-exclude.txt",
        f"--ipset-exclude={lists}ipset-exclude-user.txt",
        "--dpi-desync=fake",
        "--dpi-desync-repeats=6",
        f"--dpi-desync-fake-quic={b}quic_initial_www_google_com.bin",
        "--new",
        "--filter-tcp=80,443,8443",
        f"--ipset={lists}ipset-all.txt",
        f"--hostlist-exclude={lists}list-exclude.txt",
        f"--hostlist-exclude={lists}list-exclude-user.txt",
        f"--ipset-exclude={lists}ipset-exclude.txt",
        f"--ipset-exclude={lists}ipset-exclude-user.txt",
        "--dpi-desync=multisplit",
        "--dpi-desync-split-seqovl=568",
        "--dpi-desync-split-pos=1",
        f"--dpi-desync-split-seqovl-pattern={b}tls_clienthello_4pda_to.bin",
        "--new",
        "--filter-udp=443",
        f"--ipset={lists}ipset-all.txt",
        f"--hostlist-exclude={lists}list-exclude.txt",
        f"--hostlist-exclude={lists}list-exclude-user.txt",
        f"--ipset-exclude={lists}ipset-exclude.txt",
        f"--ipset-exclude={lists}ipset-exclude-user.txt",
        "--dpi-desync=fake",
        "--dpi-desync-repeats=12",
        "--dpi-desync-any-protocol=1",
        f"--dpi-desync-fake-unknown-udp={b}quic_initial_dbankcloud_ru.bin",
        "--dpi-desync-cutoff=n2",
    ]


class WinWsService:
    def __init__(self) -> None:
        self._proc: Optional[subprocess.Popen] = None

    @property
    def running(self) -> bool:
        if self._proc is not None and self._proc.poll() is None:
            return True
        return _find_winws_pid() is not None

    def start(self) -> None:
        if self.running:
            return
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

        args = _winws_args()
        self._proc = subprocess.Popen(
            args,
            cwd=str(ZAPRET_BIN_DIR),
            creationflags=CREATE_NO_WINDOW,
        )
        if self._proc.poll() is not None:
            code = self._proc.returncode
            self._proc = None
            raise RuntimeError(f"winws.exe завершился с кодом {code}")

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
