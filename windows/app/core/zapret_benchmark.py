"""Benchmark zapret presets against Discord endpoints."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from threading import Event
from typing import Callable

from .winws import WinWsService
from .zapret_presets import ZapretPreset, default_preset_name, list_presets

CREATE_NO_WINDOW = 0x08000000

# updates.discord.com — зависание на «Checking for updates…»
DISCORD_TARGETS: list[tuple[str, str, int]] = [
    ("Discord Updates", "https://updates.discord.com", 6),
    ("Discord Gateway", "https://gateway.discord.gg", 4),
    ("Discord", "https://discord.com", 3),
    ("Discord CDN", "https://cdn.discordapp.com", 2),
    ("Discord Media", "https://discord.media", 2),
]

DISCORD_MAX_SCORE = sum(w for _, _, w in DISCORD_TARGETS)

_CURL_PROFILES: list[tuple[str, list[str]]] = [
    ("TLS1.3", ["--tlsv1.3", "--tls-max", "1.3"]),
    ("TLS1.2", ["--tlsv1.2", "--tls-max", "1.2"]),
    ("HTTP", ["--http1.1"]),
]

ProgressCb = Callable[[int, int, str, str], None]
DoneCb = Callable[[str | None, int, dict[str, dict[str, str]]], None]


@dataclass
class PresetScore:
    name: str
    label: str
    score: int
    details: dict[str, str]


def probe_url(url: str, timeout: int = 5) -> tuple[bool, str]:
    """Как в zapret test zapret.ps1: успех если curl завершился с кодом 0."""
    last = "no response"
    for label, extra in _CURL_PROFILES:
        try:
            result = subprocess.run(
                [
                    "curl.exe",
                    "-I",
                    "-s",
                    "-m",
                    str(timeout),
                    "-o",
                    "NUL",
                    "-w",
                    "%{http_code}",
                    "--show-error",
                    *extra,
                    url,
                ],
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW,
                timeout=timeout + 3,
            )
            code = (result.stdout or "").strip()
            err = (result.stderr or "").lower()
            last = f"{label}:{code or result.returncode}"

            if any(
                token in err
                for token in (
                    "could not resolve host",
                    "certificate verify failed",
                    "ssl certificate problem",
                    "unable to get local issuer certificate",
                )
            ):
                continue

            if result.returncode == 0:
                return True, last
        except subprocess.TimeoutExpired:
            last = f"{label}:timeout"
        except Exception as exc:
            last = f"{label}:{exc}"

    return False, last


def score_preset(winws: WinWsService, preset: ZapretPreset, settle_s: float = 5.0) -> PresetScore:
    winws.stop()
    time.sleep(0.6)
    winws.start_preset(preset.name)
    time.sleep(settle_s)

    total = 0
    details: dict[str, str] = {}
    for label, url, weight in DISCORD_TARGETS:
        ok, info = probe_url(url)
        details[label] = f"OK {info}" if ok else f"FAIL {info}"
        if ok:
            total += weight
    return PresetScore(name=preset.name, label=preset.label, score=total, details=details)


def run_benchmark(
    winws: WinWsService,
    on_progress: ProgressCb,
    on_done: DoneCb,
    cancel: Event | None = None,
) -> None:
    presets = list_presets()
    if not presets:
        on_done(None, 0, {})
        return

    cancel = cancel or Event()
    all_results: dict[str, dict[str, str]] = {}
    best_name: str | None = None
    best_score = -1

    try:
        for idx, preset in enumerate(presets):
            if cancel.is_set():
                break
            on_progress(
                idx,
                len(presets),
                preset.label,
                f"Проверка: {preset.label}…",
            )
            try:
                scored = score_preset(winws, preset)
            except Exception as exc:
                scored = PresetScore(
                    name=preset.name,
                    label=preset.label,
                    score=0,
                    details={"Ошибка": str(exc)},
                )

            all_results[preset.name] = scored.details
            detail_line = " · ".join(
                f"{k}: {v}" for k, v in scored.details.items()
            )
            on_progress(
                idx + 1,
                len(presets),
                preset.label,
                f"{preset.label} — балл {scored.score}\n{detail_line}",
            )
            if scored.score > best_score:
                best_score = scored.score
                best_name = preset.name
            if scored.score >= DISCORD_MAX_SCORE:
                on_progress(
                    len(presets),
                    len(presets),
                    preset.label,
                    f"{preset.label} — идеальный результат, остальные пресеты пропущены",
                )
                break
    finally:
        chosen = best_name if best_score > 0 else default_preset_name()
        winws.stop()
        time.sleep(0.4)
        try:
            winws.start_preset(chosen)
        except Exception:
            pass
        on_done(best_name if best_score > 0 else None, best_score, all_results)
