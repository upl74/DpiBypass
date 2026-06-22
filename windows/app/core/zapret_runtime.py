"""Zapret runtime: version, prepare, launch via original .bat files."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

from .paths import ZAPRET_BIN_DIR, ZAPRET_ROOT, WINWS_EXE
from .zapret_presets import resolve_preset_args

CREATE_NO_WINDOW = 0x08000000
ZAPRET_RELEASE = "1.9.9c"
ZAPRET_RELEASE_URL = (
    "https://github.com/Flowseal/zapret-discord-youtube/releases/download/"
    f"{ZAPRET_RELEASE}/zapret-discord-youtube-{ZAPRET_RELEASE}.zip"
)
VERSION_FILE = ZAPRET_ROOT / "dpibypass_version.txt"
LAUNCHER_BAT = ZAPRET_ROOT / "dpibypass_launch.bat"

_LAUNCHER_CONTENT = """@echo off
chcp 65001 >nul
cd /d "%~dp0"
set NO_UPDATE_CHECK=1
call service.bat status_zapret
call service.bat load_game_filter
call service.bat load_user_lists
call "%~dp0%~1"
exit /b 0
"""


def ensure_launcher() -> Path:
    ZAPRET_ROOT.mkdir(parents=True, exist_ok=True)
    if not LAUNCHER_BAT.is_file() or LAUNCHER_BAT.read_text(encoding="utf-8") != _LAUNCHER_CONTENT:
        LAUNCHER_BAT.write_text(_LAUNCHER_CONTENT, encoding="utf-8")
    return LAUNCHER_BAT


def read_installed_version() -> str | None:
    service = ZAPRET_ROOT / "service.bat"
    if service.is_file():
        text = service.read_text(encoding="utf-8", errors="replace")
        match = re.search(r'LOCAL_VERSION=([^\r\n"]+)', text)
        if match:
            return match.group(1).strip()
    if VERSION_FILE.is_file():
        return VERSION_FILE.read_text(encoding="utf-8").strip() or None
    return None


def fetch_latest_release() -> str:
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/Flowseal/zapret-discord-youtube/releases/latest",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "DpiBypass"},
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        tag = str(data.get("tag_name", ZAPRET_RELEASE)).lstrip("v")
        return tag
    except Exception:
        return ZAPRET_RELEASE


def is_installed() -> bool:
    return WINWS_EXE.is_file()


def is_up_to_date() -> bool:
    if not is_installed():
        return False
    installed = read_installed_version()
    if not installed:
        return False
    return installed == fetch_latest_release()


def version_label() -> str:
    if not is_installed():
        return "не установлен"
    installed = read_installed_version() or "?"
    latest = fetch_latest_release()
    if installed == latest:
        return f"{installed} (актуальная)"
    return f"{installed} (доступна {latest})"


def prepare_zapret() -> None:
    if not ZAPRET_ROOT.is_dir():
        return
    for step in ("status_zapret", "load_game_filter", "load_user_lists"):
        subprocess.run(
            ["cmd.exe", "/c", "service.bat", step],
            cwd=str(ZAPRET_ROOT),
            creationflags=CREATE_NO_WINDOW,
            env={**os.environ, "NO_UPDATE_CHECK": "1"},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def launch_preset_bat(preset_name: str) -> subprocess.Popen:
    """service.bat prep + winws.exe без консольного окна (general*.bat использует start)."""
    ensure_launcher()
    bat = ZAPRET_ROOT / preset_name
    if not bat.is_file():
        raise FileNotFoundError(f"Пресет не найден: {preset_name}")

    prepare_zapret()
    args = resolve_preset_args(preset_name)

    env = os.environ.copy()
    env["NO_UPDATE_CHECK"] = "1"
    return subprocess.Popen(
        args,
        cwd=str(ZAPRET_BIN_DIR),
        creationflags=CREATE_NO_WINDOW,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def write_version_stamp(version: str = ZAPRET_RELEASE) -> None:
    VERSION_FILE.write_text(version + "\n", encoding="utf-8")
