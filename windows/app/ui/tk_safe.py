"""Safe Tk callbacks after window close."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, TypeVar

T = TypeVar("T")


def is_alive(widget: tk.Misc) -> bool:
    try:
        return bool(widget.winfo_exists())
    except tk.TclError:
        return False


def safe_after(widget: tk.Misc, delay_ms: int, callback: Callable[[], T]) -> str | None:
    def run() -> None:
        try:
            if is_alive(widget):
                callback()
        except tk.TclError:
            pass

    try:
        if is_alive(widget):
            return widget.after(delay_ms, run)
    except tk.TclError:
        pass
    return None
