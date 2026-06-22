"""Parse zapret general*.bat presets into winws.exe argument lists."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .paths import ZAPRET_BIN_DIR, ZAPRET_LISTS_DIR, ZAPRET_ROOT, WINWS_EXE


@dataclass(frozen=True)
class ZapretPreset:
    name: str
    path: Path
    label: str


def list_presets() -> list[ZapretPreset]:
    if not ZAPRET_ROOT.is_dir():
        return []
    files = sorted(
        ZAPRET_ROOT.glob("general*.bat"),
        key=lambda p: _sort_key(p.name),
    )
    return [
        ZapretPreset(name=f.name, path=f, label=_display_label(f.name))
        for f in files
        if f.is_file() and f.name.lower() != "service.bat"
    ]


def default_preset_name() -> str:
    return "general.bat"


def resolve_preset_args(preset_name: str | None = None) -> list[str]:
    name = preset_name or default_preset_name()
    path = ZAPRET_ROOT / name
    if not path.is_file():
        path = ZAPRET_ROOT / default_preset_name()
    if not path.is_file():
        raise FileNotFoundError(f"Пресет zapret не найден: {name}")
    return parse_winws_args(path)


def parse_winws_args(bat_path: Path) -> list[str]:
    raw = bat_path.read_text(encoding="utf-8", errors="replace")
    flat = re.sub(r"\^\s*\r?\n", " ", raw)
    flat = re.sub(r"\s+", " ", flat)

    match = re.search(r'winws\.exe"\s+(.+)', flat, re.I)
    if not match:
        match = re.search(r"winws\.exe\s+(.+)", flat, re.I)
    if not match:
        raise ValueError(f"winws.exe не найден в {bat_path.name}")

    tail = match.group(1).strip()

    bin_p = str(ZAPRET_BIN_DIR).replace("/", "\\")
    if not bin_p.endswith("\\"):
        bin_p += "\\"
    lists_p = str(ZAPRET_LISTS_DIR).replace("/", "\\")
    if not lists_p.endswith("\\"):
        lists_p += "\\"

    tail = tail.replace("%BIN%", bin_p).replace("%LISTS%", lists_p)
    tail = tail.replace("%GameFilterTCP%", "").replace("%GameFilterUDP%", "")
    tail = re.sub(r"(--wf-tcp=[0-9,]+),", r"\1", tail)
    tail = re.sub(r"(--wf-udp=[0-9,\-]+),", r"\1", tail)

    tokens = _tokenize_winws_tail(tail)
    cleaned: list[str] = []
    for token in tokens:
        if "=" in token:
            key, value = token.split("=", 1)
            value = value.strip().strip('"')
            if not value:
                continue
            cleaned.append(f"{key}={value}")
        else:
            cleaned.append(token)

    return [str(WINWS_EXE), *cleaned]


def _tokenize_winws_tail(tail: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    n = len(tail)
    while i < n:
        while i < n and tail[i].isspace():
            i += 1
        if i >= n:
            break
        if tail[i : i + 2] != "--":
            i += 1
            continue

        j = i + 2
        in_quote = False
        while j < n:
            ch = tail[j]
            if ch == '"':
                in_quote = not in_quote
                j += 1
                continue
            if ch == " " and not in_quote:
                k = j
                while k < n and tail[k].isspace():
                    k += 1
                if k < n and tail[k : k + 2] == "--":
                    break
            j += 1

        token = tail[i:j].strip()
        if token:
            tokens.append(token)
        i = j
    return tokens


def _display_label(filename: str) -> str:
    base = filename.removesuffix(".bat")
    if base == "general":
        return "general (стандарт)"
    if base.startswith("general ("):
        return base.replace("general (", "").rstrip(")")
    return base


def _sort_key(name: str) -> str:
    return re.sub(r"(\d+)", lambda m: m.group(1).zfill(4), name.lower())
