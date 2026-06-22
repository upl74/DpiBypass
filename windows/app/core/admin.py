"""Windows administrator check / UAC relaunch."""

from __future__ import annotations

import ctypes
import sys


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> None:
    """Restart current app elevated (UAC prompt)."""
    params = " ".join(f'"{a}"' if " " in a else a for a in sys.argv[1:])
    exe = sys.executable
    if getattr(sys, "frozen", False):
        exe = f'"{exe}"'
    rc = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        params or None,
        None,
        1,
    )
    if rc <= 32:
        raise OSError(f"UAC elevation failed (code {rc})")
