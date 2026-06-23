"""Embedded Telegram WS proxy (Flowseal tg-ws-proxy core)."""

from __future__ import annotations

import json
import logging
import socket
import sys
import time
import webbrowser
from pathlib import Path
from typing import Optional

from .paths import DATA_DIR, WINDOWS_ROOT, ensure_dirs

TGWS_CONFIG = DATA_DIR / "tgws_config.json"
TG_SECRET_LEGACY = DATA_DIR / "tg_secret.txt"
DEFAULT_PORT = 1443
DEFAULT_HOST = "127.0.0.1"
# Flowseal / amurcanov: direct WS to DC .220; empty dc_ip = CF-only (fails on some operators)
DEFAULT_DC_IP = [
    "2:149.154.167.220",
    "4:149.154.167.220",
    "203:149.154.167.220",
]

_log = logging.getLogger("tgws")
_logging_ready = False


def _vendor_root() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled = Path(meipass) / "tg-ws-proxy"
            if bundled.is_dir():
                return bundled
    return WINDOWS_ROOT / "third_party" / "tg-ws-proxy"


def _ensure_vendor_path() -> Path:
    root = _vendor_root()
    if not root.is_dir():
        raise FileNotFoundError(
            "Не найден модуль tg-ws-proxy.\n"
            f"Запустите setup.ps1 или положите исходники в:\n{root}"
        )
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    return root


def _load_tgws_config() -> dict:
    _ensure_vendor_path()
    from utils.default_config import default_tray_config

    ensure_dirs()
    defaults = default_tray_config()
    if TGWS_CONFIG.is_file():
        try:
            data = json.loads(TGWS_CONFIG.read_text(encoding="utf-8"))
            for key, value in defaults.items():
                data.setdefault(key, value)
            data["dc_ip"] = _normalize_dc_ip(data.get("dc_ip"))
            return data
        except (json.JSONDecodeError, OSError, TypeError):
            pass

    cfg = dict(defaults)
    cfg["dc_ip"] = _normalize_dc_ip(cfg.get("dc_ip"))
    if TG_SECRET_LEGACY.is_file():
        secret = TG_SECRET_LEGACY.read_text(encoding="utf-8").strip()
        if len(secret) == 32:
            cfg["secret"] = secret
    _save_tgws_config(cfg)
    return cfg


def _normalize_dc_ip(dc_ip: object) -> list[str]:
    if not isinstance(dc_ip, list) or not dc_ip:
        return list(DEFAULT_DC_IP)
    merged = list(dc_ip)
    for entry in DEFAULT_DC_IP:
        if entry not in merged:
            merged.append(entry)
    return merged


def _save_tgws_config(cfg: dict) -> None:
    ensure_dirs()
    TGWS_CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def _patch_tray_paths() -> None:
    import utils.tray_common as tc

    tc.APP_DIR = DATA_DIR
    tc.CONFIG_FILE = TGWS_CONFIG
    tc.LOG_FILE = DATA_DIR / "tgws_proxy.log"


def _setup_logging_once() -> None:
    global _logging_ready
    if _logging_ready:
        return
    import utils.tray_common as tc

    _patch_tray_paths()
    tc.setup_logging(verbose=False)
    _logging_ready = True


def _wait_for_port(host: str, port: int, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


class TgWsService:
    def __init__(self) -> None:
        self._cfg: Optional[dict] = None
        self._tc = None

    def _tray(self):
        if self._tc is None:
            _ensure_vendor_path()
            import utils.tray_common as tc

            _patch_tray_paths()
            _setup_logging_once()
            self._tc = tc
        return self._tc

    @property
    def running(self) -> bool:
        if self._tc is None:
            return False
        thread = getattr(self._tc, "_proxy_thread", None)
        return thread is not None and thread.is_alive()

    def start(self) -> None:
        tc = self._tray()
        if self.running:
            return

        self._cfg = _load_tgws_config()
        host = str(self._cfg.get("host", DEFAULT_HOST))
        port = int(self._cfg.get("port", DEFAULT_PORT))
        errors: list[str] = []

        def on_error(msg: str) -> None:
            errors.append(msg)
            _log.error("%s", msg)

        tc.start_proxy(self._cfg, on_error)
        if not _wait_for_port(host, port):
            tc.stop_proxy()
            detail = errors[0] if errors else f"порт {port} не слушается"
            raise RuntimeError(f"TgWsProxy не запустился: {detail}")

        _log.info("Started on %s:%d", host, port)

    def stop(self) -> None:
        if self._tc is not None:
            self._tc.stop_proxy()

    @staticmethod
    def open_telegram_proxy(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        _ensure_vendor_path()
        cfg = _load_tgws_config()
        cfg.setdefault("host", host)
        cfg.setdefault("port", port)
        import utils.tray_common as tc

        webbrowser.open(tc.tg_proxy_url(cfg))

    @staticmethod
    def is_available() -> bool:
        try:
            _ensure_vendor_path()
            return True
        except FileNotFoundError:
            return False
