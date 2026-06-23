import json
from dataclasses import asdict, dataclass, fields

from .paths import CONFIG_FILE, ensure_dirs

CONFIG_VERSION = 1


@dataclass
class LiteConfig:
    config_version: int = CONFIG_VERSION
    minimize_to_tray: bool = True
    autostart: bool = False
    auto_enable: bool = True


def load_lite_config() -> LiteConfig:
    ensure_dirs()
    if not CONFIG_FILE.exists():
        return LiteConfig()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        valid = {f.name for f in fields(LiteConfig)}
        return LiteConfig(**{k: data[k] for k in valid if k in data})
    except (json.JSONDecodeError, TypeError, KeyError):
        return LiteConfig()


def save_lite_config(cfg: LiteConfig) -> None:
    ensure_dirs()
    cfg.config_version = CONFIG_VERSION
    CONFIG_FILE.write_text(
        json.dumps(asdict(cfg), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
