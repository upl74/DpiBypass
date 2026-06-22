from .byedpi import ByeDpiService
from .config import AppConfig, effective_preset
from . import system_proxy
from .tgws import TgWsService


class BypassEngine:
    def __init__(self) -> None:
        self.byedpi = ByeDpiService()
        self.tgws = TgWsService()
        self.config = AppConfig()

    @property
    def active(self) -> bool:
        return self.byedpi.running or self.tgws.running

    def start(self, cfg: AppConfig) -> None:
        self.config = cfg
        if cfg.enable_byedpi:
            self.byedpi.start(effective_preset(cfg))
            if cfg.enable_sys_proxy:
                system_proxy.enable_socks(port=cfg.socks_port)
        if cfg.enable_tgws:
            self.tgws.start()

    def stop(self) -> None:
        self.byedpi.stop()
        self.tgws.stop()
        system_proxy.disable()
