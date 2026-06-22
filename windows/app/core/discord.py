"""Discord desktop launcher through local SOCKS proxy."""

from __future__ import annotations

import os
import subprocess
import webbrowser
from pathlib import Path

CREATE_NO_WINDOW = 0x08000000


def _localappdata() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", ""))


def find_discord_exe() -> Path | None:
    update = _localappdata() / "Discord" / "Update.exe"
    if update.is_file():
        return update

    discord_dir = _localappdata() / "Discord"
    if discord_dir.is_dir():
        apps = sorted(discord_dir.glob("app-*/Discord.exe"), reverse=True)
        for exe in apps:
            if exe.is_file():
                return exe
    return None


def _proxy_env(port: int) -> dict[str, str]:
    proxy = f"socks5://127.0.0.1:{port}"
    env = os.environ.copy()
    env["HTTP_PROXY"] = proxy
    env["HTTPS_PROXY"] = proxy
    env["ALL_PROXY"] = proxy
    env["NO_PROXY"] = "localhost,127.0.0.1"
    return env


def launch_desktop(port: int = 1080) -> None:
    target = find_discord_exe()
    if target is None:
        raise FileNotFoundError(
            "Discord не установлен.\n"
            "Скачайте с https://discord.com/download или откройте в браузере."
        )

    env = _proxy_env(port)
    if target.name == "Update.exe":
        subprocess.Popen(
            [str(target), "--processStart", "Discord.exe"],
            env=env,
            creationflags=CREATE_NO_WINDOW,
        )
    else:
        subprocess.Popen(
            [str(target)],
            env=env,
            creationflags=CREATE_NO_WINDOW,
        )


def open_in_browser() -> None:
    webbrowser.open("https://discord.com/app")
