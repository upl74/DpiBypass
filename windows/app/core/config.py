import json
from dataclasses import asdict, dataclass, fields

from .paths import CONFIG_FILE, ensure_dirs

CONFIG_VERSION = 5


@dataclass
class AppConfig:
    config_version: int = CONFIG_VERSION
    preset: str = "universal"
    enable_byedpi: bool = True
    enable_discord: bool = True
    enable_tgws: bool = True
    enable_sys_proxy: bool = True
    socks_port: int = 1080
    minimize_to_tray: bool = True
    autostart: bool = False
    auto_enable: bool = False
    zapret_preset: str = "general.bat"
    discord_autostart: bool = True


def load_config() -> AppConfig:
    ensure_dirs()
    if not CONFIG_FILE.exists():
        return AppConfig()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        valid = {f.name for f in fields(AppConfig)}
        cfg = AppConfig(**{k: data[k] for k in valid if k in data})
        if cfg.config_version < CONFIG_VERSION and cfg.preset == "youtube":
            cfg.preset = "universal"
        return cfg
    except (json.JSONDecodeError, TypeError, KeyError):
        return AppConfig()


def save_config(cfg: AppConfig) -> None:
    ensure_dirs()
    cfg.config_version = CONFIG_VERSION
    CONFIG_FILE.write_text(
        json.dumps(asdict(cfg), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
