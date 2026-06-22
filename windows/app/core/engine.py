"""Independent bypass components orchestration."""

from __future__ import annotations

from enum import Enum

from .byedpi import ByeDpiService
from .config import AppConfig
from . import system_proxy
from .tgws import TgWsService
from .winws import WinWsService


class ComponentId(str, Enum):
    BYEDPI = "byedpi"
    DISCORD = "discord"
    TGWS = "tgws"
    SYS_PROXY = "sys_proxy"


class BypassEngine:
    def __init__(self) -> None:
        self.byedpi = ByeDpiService()
        self.tgws = TgWsService()
        self.winws = WinWsService()
        self.config = AppConfig()

    @property
    def active(self) -> bool:
        return any(self.is_running(c) for c in ComponentId)

    def is_running(self, component: ComponentId) -> bool:
        if component == ComponentId.BYEDPI:
            return self.byedpi.running
        if component == ComponentId.DISCORD:
            return self.winws.running
        if component == ComponentId.TGWS:
            return self.tgws.running
        if component == ComponentId.SYS_PROXY:
            return system_proxy.is_enabled()
        return False

    def start(self, cfg: AppConfig) -> None:
        self.config = cfg
        if cfg.enable_byedpi:
            self.start_component(ComponentId.BYEDPI, cfg)
        if cfg.enable_discord:
            self.start_component(ComponentId.DISCORD, cfg)
        if cfg.enable_tgws:
            self.start_component(ComponentId.TGWS, cfg)
        if cfg.enable_sys_proxy:
            self.start_component(ComponentId.SYS_PROXY, cfg)

    def stop(self) -> None:
        self.stop_component(ComponentId.SYS_PROXY)
        self.stop_component(ComponentId.DISCORD)
        self.stop_component(ComponentId.TGWS)
        self.stop_component(ComponentId.BYEDPI)

    def start_component(self, component: ComponentId, cfg: AppConfig | None = None) -> None:
        cfg = cfg or self.config
        self.config = cfg

        if component == ComponentId.BYEDPI:
            if self.byedpi.running:
                return
            self.byedpi.start(cfg.preset)
            if cfg.enable_sys_proxy:
                system_proxy.enable_socks(port=cfg.socks_port)
            return

        if component == ComponentId.DISCORD:
            if self.winws.running:
                return
            preset = cfg.zapret_preset or "general.bat"
            self.winws.start(preset)
            return

        if component == ComponentId.TGWS:
            if self.tgws.running:
                return
            self.tgws.start()
            return

        if component == ComponentId.SYS_PROXY:
            if not cfg.enable_byedpi and not self.byedpi.running:
                raise RuntimeError(
                    "Системный SOCKS требует включённый ByeDPI."
                )
            if not self.byedpi.running:
                self.byedpi.start(cfg.preset)
            system_proxy.enable_socks(port=cfg.socks_port)

    def stop_component(self, component: ComponentId) -> None:
        if component == ComponentId.BYEDPI:
            self.byedpi.stop()
            if not self.config.enable_sys_proxy:
                system_proxy.disable()
            elif not self.byedpi.running:
                system_proxy.disable()
            return

        if component == ComponentId.DISCORD:
            self.winws.stop()
            return

        if component == ComponentId.TGWS:
            self.tgws.stop()
            return

        if component == ComponentId.SYS_PROXY:
            system_proxy.disable()

    def sync_from_config(self, cfg: AppConfig) -> None:
        """Apply config toggles: start/stop only changed components."""
        self.config = cfg
        pairs: list[tuple[ComponentId, bool]] = [
            (ComponentId.BYEDPI, cfg.enable_byedpi),
            (ComponentId.DISCORD, cfg.enable_discord),
            (ComponentId.TGWS, cfg.enable_tgws),
            (ComponentId.SYS_PROXY, cfg.enable_sys_proxy),
        ]
        for component, want in pairs:
            running = self.is_running(component)
            if want and not running:
                self.start_component(component, cfg)
            elif not want and running:
                self.stop_component(component)

    def running_labels(self) -> list[str]:
        labels: list[str] = []
        if self.byedpi.running:
            labels.append("ByeDPI")
        if self.winws.running:
            labels.append(f"zapret ({self.config.zapret_preset})")
        if self.tgws.running:
            labels.append("Telegram")
        if system_proxy.is_enabled():
            labels.append("SOCKS")
        return labels
