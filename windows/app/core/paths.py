import os
import sys
from pathlib import Path


def _windows_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


WINDOWS_ROOT = _windows_root()
BIN_DIR = WINDOWS_ROOT / "bin"
DATA_DIR = Path(os.environ.get("APPDATA", "")) / "DpiBypass"
CONFIG_FILE = DATA_DIR / "config.json"

BYEDPI_EXE = BIN_DIR / "ciadpi.exe"
TGWS_VENDOR = WINDOWS_ROOT / "third_party" / "tg-ws-proxy"
ZAPRET_ROOT = BIN_DIR / "zapret"
ZAPRET_BIN_DIR = ZAPRET_ROOT / "bin"
ZAPRET_LISTS_DIR = ZAPRET_ROOT / "lists"
WINWS_EXE = ZAPRET_BIN_DIR / "winws.exe"


def ensure_dirs() -> None:
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
