# Synced with Android DpiDefaults + Discord (zapret-discord-youtube style)

import re
import sys
from pathlib import Path

BIND = "-i 127.0.0.1 -p 1080"
LADDER_FULL = "-d1 -d3+s -s6+s -d9+s -s12+s -d15+s -s20+s -d25+s -s30+s -d35+s"

DISCORD_HOSTS_INLINE = (
    "discord.com discord.gg discordapp.com discordapp.net discord.media "
    "discordcdn.com discordstatus.com gateway.discord.gg cdn.discordapp.com "
    "images-ext-1.discordapp.net media.discordapp.net"
)

# UDP fake + split/disoob — voice and gateway (ByeDPIAndroid #174)
DISCORD_UDP = "-Ku -a3 -An -Kt,h -s1 -q1 -Y -Ar"

PRESETS = {
  # Default on PC: YT + Discord + IG + browser
    "universal": (
        f"{BIND} {DISCORD_UDP} -An -Kt,h {LADDER_FULL} -r1+s -S -a1 "
        f"-As -Kt,h {LADDER_FULL} -S -a1"
    ),
    "youtube": (
        f"{BIND} -Ku -a3 -An -Kt,h {LADDER_FULL} -r1+s -S -a1 "
        f"-As -Kt,h {LADDER_FULL} -S -a1"
    ),
    "discord": f"{BIND} {DISCORD_UDP} -H:{DISCORD_HOSTS_INLINE}",
    "hybrid": (
        f"{BIND} -Kt,h {LADDER_FULL} -r1+s -S -a1 -As -Kt,h {LADDER_FULL} -S -a1 "
        "-d1 -f-1 -t 8 -r1 -Ku -As -d3 -f-1 -t 8 -Ku"
    ),
    "lite": f"{BIND} -Kt,h -d1 -d3+s -s6+s -d9+s -r1+s -S -a1 -d1 -f-1 -t 8 -Ku",
    "minimal": f"{BIND} -d1 -f-1 -t 8 -Ku",
    "light": f"{BIND} -s0 -o1 -d1 -r1+s",
}

PRESET_LABELS = {
    "universal": "YouTube + Discord + Instagram",
    "youtube": "Только YouTube / Instagram",
    "discord": "Только Discord",
    "hybrid": "Hybrid TG + YT",
    "lite": "GoodbyeDPI Lite",
    "minimal": "Минимальный",
    "light": "Лёгкий",
}

DEFAULT_PRESET = "universal"


def _bundled_hosts_file() -> Path | None:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    for candidate in (
        base / "data" / "discord-hosts.txt",
        base / "discord-hosts.txt",
        Path(__file__).resolve().parents[1] / "data" / "discord-hosts.txt",
    ):
        if candidate.is_file():
            return candidate
    return None


def preset_args(name: str) -> list[str]:
    cmd = PRESETS.get(name, PRESETS[DEFAULT_PRESET])
    idx = cmd.find("-")
    tail = cmd[idx:] if idx >= 0 else cmd
    args = [a.strip('"') for a in re.findall(r'[^\s"]+|"[^"]*"', tail)]

    if name == "discord":
        hosts = _bundled_hosts_file()
        if hosts is not None:
            args = [f"-H{hosts}" if a.startswith("-H:") else a for a in args]
    return args
