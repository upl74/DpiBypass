"""Apply saved Discord zapret preset on boot."""

from __future__ import annotations

from . import autostart
from .admin import is_admin
from .config import AppConfig, load_config, save_config
from .engine import BypassEngine, ComponentId
from .winws import is_available as winws_available


def should_autostart_discord(cfg: AppConfig | None = None) -> bool:
    cfg = cfg or load_config()
    return bool(
        cfg.enable_discord
        and cfg.discord_autostart
        and cfg.zapret_preset
        and winws_available()
    )


def persist_discord_preset(preset_name: str) -> AppConfig:
    """Save preset and enable boot autostart (scheduled task, без UAC при каждой загрузке)."""
    cfg = load_config()
    cfg.zapret_preset = preset_name
    cfg.enable_discord = True
    cfg.discord_autostart = True
    cfg.autostart = True
    cfg.auto_enable = True
    save_config(cfg)
    try:
        autostart.ensure_discord_autostart(True)
    except OSError:
        pass
    return cfg


def autostart_discord(engine: BypassEngine, cfg: AppConfig | None = None) -> bool:
    """Start saved zapret preset. Returns True if winws is running."""
    cfg = cfg or load_config()
    if not should_autostart_discord(cfg):
        return False
    if not is_admin():
        return False
    if engine.is_running(ComponentId.DISCORD):
        return True
    try:
        engine.start_component(ComponentId.DISCORD, cfg)
        return engine.is_running(ComponentId.DISCORD)
    except Exception:
        return False
