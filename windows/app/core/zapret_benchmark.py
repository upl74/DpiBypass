"""Benchmark zapret presets against Discord endpoints."""

from __future__ import annotations

import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Event
from typing import Callable

from .winws import WinWsService
from .zapret_presets import ZapretPreset, list_presets

CREATE_NO_WINDOW = 0x08000000

SETTLE_S = 1.5
SETTLE_QUICK_S = 1.0
STOP_GAP_S = 0.25
CURL_TIMEOUT_S = 2
FULL_TEST_TOP_N = 8

DISCORD_TARGETS: list[tuple[str, str, int]] = [
    ("Discord Updates", "https://updates.discord.com", 6),
    ("Discord Gateway", "https://gateway.discord.gg", 4),
    ("Discord", "https://discord.com", 3),
    ("Discord CDN", "https://cdn.discordapp.com", 2),
    ("Discord Media", "https://discord.media", 2),
]

QUICK_TARGET = DISCORD_TARGETS[0]

_CURL_FAST = ("TLS1.3", ["--tlsv1.3", "--tls-max", "1.3"])
_CURL_FALLBACK = ("TLS1.2", ["--tlsv1.2", "--tls-max", "1.2"])

ProgressCb = Callable[[int, int, str, str], None]
DoneCb = Callable[[str | None, int, list["PresetScore"]], None]


@dataclass
class PresetScore:
    name: str
    label: str
    score: int
    ok_count: int
    details: dict[str, str]
    quick_only: bool = False


def rank_results(results: list[PresetScore]) -> list[PresetScore]:
    return sorted(
        results,
        key=lambda item: (-item.score, -item.ok_count, item.name.lower()),
    )


def probe_url(url: str, timeout: int = CURL_TIMEOUT_S) -> tuple[bool, str]:
    label, extra = _CURL_FAST
    ok, info = _probe_once(url, timeout, label, extra)
    if ok:
        return True, info
    label, extra = _CURL_FALLBACK
    return _probe_once(url, timeout, label, extra)


def _probe_once(
    url: str, timeout: int, label: str, extra: list[str]
) -> tuple[bool, str]:
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
            timeout=timeout + 1,
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
            )
        ):
            return False, last
        if result.returncode == 0:
            return True, last
        return False, last
    except subprocess.TimeoutExpired:
        return False, f"{label}:timeout"
    except Exception as exc:
        return False, f"{label}:{exc}"


def _probe_targets_parallel(
    targets: list[tuple[str, str, int]],
) -> tuple[int, int, dict[str, str]]:
    details: dict[str, str] = {}
    total = 0
    ok_count = 0

    def check(item: tuple[str, str, int]) -> tuple[str, str, int, bool, str]:
        label, url, weight = item
        ok, info = probe_url(url)
        return label, url, weight, ok, info

    with ThreadPoolExecutor(max_workers=len(targets)) as pool:
        futures = [pool.submit(check, t) for t in targets]
        for fut in as_completed(futures):
            label, _url, weight, ok, info = fut.result()
            details[label] = f"OK {info}" if ok else f"FAIL {info}"
            if ok:
                total += weight
                ok_count += 1

    return total, ok_count, details


def _quick_score(winws: WinWsService, preset: ZapretPreset) -> PresetScore:
    winws.stop()
    time.sleep(STOP_GAP_S)
    winws.start_preset(preset.name)
    time.sleep(SETTLE_QUICK_S)

    label, url, weight = QUICK_TARGET
    ok, info = probe_url(url)
    details = {label: f"OK {info}" if ok else f"FAIL {info}"}
    score = weight if ok else 0
    return PresetScore(
        name=preset.name,
        label=preset.label,
        score=score,
        ok_count=1 if ok else 0,
        details=details,
        quick_only=True,
    )


def _full_score(winws: WinWsService, preset: ZapretPreset) -> PresetScore:
    winws.stop()
    time.sleep(STOP_GAP_S)
    winws.start_preset(preset.name)
    time.sleep(SETTLE_S)

    total, ok_count, details = _probe_targets_parallel(DISCORD_TARGETS)
    return PresetScore(
        name=preset.name,
        label=preset.label,
        score=total,
        ok_count=ok_count,
        details=details,
        quick_only=False,
    )


def live_test_preset(winws: WinWsService, preset_name: str, label: str = "") -> PresetScore:
    """Включить пресет и выполнить живую проверку (без сохранения в конфиг)."""
    winws.stop()
    time.sleep(STOP_GAP_S)
    winws.start_preset(preset_name)
    time.sleep(SETTLE_S)

    total, ok_count, details = _probe_targets_parallel(DISCORD_TARGETS)
    return PresetScore(
        name=preset_name,
        label=label or preset_name,
        score=total,
        ok_count=ok_count,
        details=details,
        quick_only=False,
    )


def _pick_best(results: list[PresetScore]) -> PresetScore | None:
    ranked = rank_results(results)
    if not ranked or ranked[0].score <= 0:
        return None
    return ranked[0]


def run_benchmark(
    winws: WinWsService,
    on_progress: ProgressCb,
    on_done: DoneCb,
    cancel: Event | None = None,
) -> None:
    presets = list_presets()
    if not presets:
        on_done(None, 0, [])
        return

    cancel = cancel or Event()
    results: list[PresetScore] = []
    total_steps = len(presets) + min(FULL_TEST_TOP_N, len(presets))
    step = 0

    try:
        quick_hits: list[PresetScore] = []
        for preset in presets:
            if cancel.is_set():
                break
            on_progress(step, total_steps, preset.label, f"Быстрая проверка: {preset.label}…")
            try:
                scored = _quick_score(winws, preset)
            except Exception as exc:
                scored = PresetScore(
                    name=preset.name,
                    label=preset.label,
                    score=0,
                    ok_count=0,
                    details={"Ошибка": str(exc)},
                    quick_only=True,
                )
            step += 1
            if scored.score > 0:
                quick_hits.append(scored)
                on_progress(
                    step,
                    total_steps,
                    preset.label,
                    f"{preset.label} — быстрый тест OK, полная проверка…",
                )
            else:
                results.append(scored)
                on_progress(
                    step,
                    total_steps,
                    preset.label,
                    f"{preset.label} — пропуск (updates.discord.com недоступен)",
                )

        finalists = rank_results(quick_hits)[:FULL_TEST_TOP_N]
        full_by_name: dict[str, PresetScore] = {}

        for preset in finalists:
            if cancel.is_set():
                break
            zp = next(p for p in presets if p.name == preset.name)
            on_progress(step, total_steps, zp.label, f"Полная проверка: {zp.label}…")
            try:
                scored = _full_score(winws, zp)
            except Exception as exc:
                scored = PresetScore(
                    name=zp.name,
                    label=zp.label,
                    score=0,
                    ok_count=0,
                    details={"Ошибка": str(exc)},
                )
            full_by_name[scored.name] = scored
            step += 1
            detail_line = " · ".join(f"{k}: {v}" for k, v in scored.details.items())
            on_progress(
                step,
                total_steps,
                scored.label,
                f"{scored.label} — балл {scored.score} ({scored.ok_count} OK)\n{detail_line}",
            )

        for item in quick_hits:
            if item.name in full_by_name:
                results.append(full_by_name[item.name])
            elif item.name not in {r.name for r in results}:
                results.append(item)

    finally:
        winws.stop()
        time.sleep(STOP_GAP_S)
        best = _pick_best(results)
        if best:
            on_progress(
                total_steps,
                total_steps,
                best.label,
                f"\n>>> Лучший кандидат: {best.name} (балл {best.score})",
            )
        on_done(best.name if best else None, best.score if best else 0, results)
