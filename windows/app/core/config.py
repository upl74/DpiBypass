import json
from dataclasses import asdict, dataclass

from .paths import CONFIG_FILE, DATA_DIR, ensure_dirs


@dataclass
class AppConfig:
    preset: str = "youtube"
    enable_byedpi: bool = True
    enable_tgws: bool = True
    enable_sys_proxy: bool = True
    socks_port: int = 1080
    minimize_to_tray: bool = True


def load_config() -> AppConfig:
    ensure_dirs()
    if not CONFIG_FILE.exists():
        return AppConfig()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return AppConfig(**{k: data[k] for k in AppConfig().__dataclass_fields__ if k in data})
    except (json.JSONDecodeError, TypeError, KeyError):
        return AppConfig()


def save_config(cfg: AppConfig) -> None:
    ensure_dirs()
    CONFIG_FILE.write_text(json.dumps(asdict(cfg), indent=2, ensure_ascii=False), encoding="utf-8")
