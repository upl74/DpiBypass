"""Discord launcher helpers."""

from __future__ import annotations

import os
import subprocess
import webbrowser
from pathlib import Path

CREATE_NO_WINDOW = 0x08000000


def _localappdata() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", ""))


def find_discord_exe() -> Path | None:
    discord_dir = _localappdata() / "Discord"
    if discord_dir.is_dir():
        apps = sorted(discord_dir.glob("app-*/Discord.exe"), reverse=True)
        for exe in apps:
            if exe.is_file():
                return exe
    update = _localappdata() / "Discord" / "Update.exe"
    if update.is_file():
        return update
    return None


def _proxy_url(port: int) -> str:
    return f"socks5://127.0.0.1:{port}"


def launch_desktop(port: int = 1080) -> None:
    """Start Discord. With winws active, proxy flags are optional."""
    target = find_discord_exe()
    if target is None:
        raise FileNotFoundError(
            "Discord не установлен.\n"
            "Скачайте с https://discord.com/download"
        )

    proxy = _proxy_url(port)
    env = os.environ.copy()
    env["HTTP_PROXY"] = proxy
    env["HTTPS_PROXY"] = proxy
    env["ALL_PROXY"] = proxy

    if target.name == "Discord.exe":
        subprocess.Popen(
            [str(target), f"--proxy-server={proxy}"],
            env=env,
            creationflags=CREATE_NO_WINDOW,
        )
        return

    # Update.exe — start Discord.exe with proxy flags directly
    app_dir = target.parent
    discord_apps = sorted(app_dir.glob("app-*/Discord.exe"), reverse=True)
    if discord_apps:
        subprocess.Popen(
            [str(discord_apps[0]), f"--proxy-server={proxy}"],
            env=env,
            creationflags=CREATE_NO_WINDOW,
        )
    else:
        subprocess.Popen(
            [str(target), "--processStart", f"Discord.exe --proxy-server={proxy}"],
            env=env,
            creationflags=CREATE_NO_WINDOW,
        )


def open_in_browser() -> None:
    webbrowser.open("https://discord.com/app")
