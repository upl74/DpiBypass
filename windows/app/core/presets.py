# Synced with app/.../DpiDefaults.kt

BIND = "-i 127.0.0.1 -p 1080"
LADDER_FULL = "-d1 -d3+s -s6+s -d9+s -s12+s -d15+s -s20+s -d25+s -s30+s -d35+s"

PRESETS = {
    "youtube": f"{BIND} {LADDER_FULL} -r1+s -S -a1 -As {LADDER_FULL} -S -a1",
    "hybrid": (
        f"{BIND} -Kt,h {LADDER_FULL} -r1+s -S -a1 -As -Kt,h {LADDER_FULL} -S -a1 "
        "-d1 -f-1 -t 8 -r1 -Ku -As -d3 -f-1 -t 8 -Ku"
    ),
    "lite": f"{BIND} -Kt,h -d1 -d3+s -s6+s -d9+s -r1+s -S -a1 -d1 -f-1 -t 8 -Ku",
    "minimal": f"{BIND} -d1 -f-1 -t 8 -Ku",
    "light": f"{BIND} -s0 -o1 -d1 -r1+s",
}

PRESET_LABELS = {
    "youtube": "YouTube / Instagram",
    "hybrid": "Hybrid TG + YT",
    "lite": "GoodbyeDPI Lite",
    "minimal": "Минимальный",
    "light": "Лёгкий",
}

DEFAULT_PRESET = "youtube"


def preset_args(name: str) -> list[str]:
    import re

    cmd = PRESETS.get(name, PRESETS[DEFAULT_PRESET])
    idx = cmd.find("-")
    tail = cmd[idx:] if idx >= 0 else cmd
    return [a.strip('"') for a in re.findall(r'[^\s"]+|"[^"]*"', tail)]
