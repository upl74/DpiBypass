# -*- coding: utf-8 -*-
"""DpiBypass Lite — Telegram WS-proxy only."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
import tkinter.messagebox as mb

# Separate config from full DpiBypass (must be before core imports).
os.environ.setdefault("DPIBYPASS_APPDATA", "DpiBypassLite")

import customtkinter as ctk
from PIL import Image, ImageDraw

from core.lite_autostart import is_enabled as autostart_enabled
from core.lite_autostart import set_enabled as set_autostart
from core.lite_config import LiteConfig, load_lite_config, save_lite_config
from core.paths import WINDOWS_ROOT
from core.tgws import TgWsService
from ui.tk_safe import is_alive, safe_after

APP_VERSION = "1.0.0"

PRIMARY = "#0EA5E9"
PRIMARY_HOVER = "#0284C7"
BG = "#0F172A"
SURFACE = "#1E293B"
SURFACE_2 = "#334155"
TEXT = "#F8FAFC"
TEXT_MUTED = "#94A3B8"
OK = "#22C55E"
ERR = "#94A3B8"
DISCONNECT = "#EF4444"
OUTLINE = "#475569"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--autostart", action="store_true")
    return parser.parse_args()


def _make_tray_image(size: int = 64) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, 2, size - 2, size - 2), radius=14, fill=PRIMARY)
    d.ellipse((size // 4, size // 4, size * 3 // 4, size * 3 // 4), outline="white", width=3)
    return img


class LiteWindow(ctk.CTk):
    def __init__(self, *, launched_autostart: bool = False) -> None:
        super().__init__()
        self.launched_autostart = launched_autostart
        self.tgws = TgWsService()
        self.cfg = load_lite_config()
        self._tray = None
        self._tray_thread = None
        self._busy = False
        self._quitting = False

        self.title("DpiBypass Lite")
        self.geometry("400x420")
        self.minsize(360, 380)
        self.configure(fg_color=BG)

        self._build_ui()
        self._sync_autostart_switch()
        self._refresh_status()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if launched_autostart and self.cfg.minimize_to_tray:
            safe_after(self, 300, self._hide_to_tray)
        if self.cfg.auto_enable or launched_autostart:
            safe_after(self, 800, self._try_auto_enable)

    def _card(self, parent, **kwargs) -> ctk.CTkFrame:
        return ctk.CTkFrame(
            parent,
            fg_color=SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=OUTLINE,
            **kwargs,
        )

    def _build_ui(self) -> None:
        hero = self._card(self)
        hero.pack(fill="x", padx=20, pady=(20, 12))

        ctk.CTkLabel(
            hero,
            text="DpiBypass Lite",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT,
            anchor="w",
        ).pack(anchor="w", padx=18, pady=(16, 0))

        ctk.CTkLabel(
            hero,
            text="Telegram WS-прокси · 127.0.0.1:1443",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", padx=18, pady=(0, 12))

        status_row = ctk.CTkFrame(hero, fg_color="transparent")
        status_row.pack(fill="x", padx=18, pady=(0, 16))

        self.status_dot = ctk.CTkLabel(
            status_row, text="●", font=ctk.CTkFont(size=22), text_color=ERR
        )
        self.status_dot.pack(side="left", padx=(0, 8))

        col = ctk.CTkFrame(status_row, fg_color="transparent")
        col.pack(side="left", fill="x", expand=True)
        self.status_text = ctk.CTkLabel(
            col,
            text="Выключено",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT,
            anchor="w",
        )
        self.status_text.pack(anchor="w")
        self.status_hint = ctk.CTkLabel(
            col,
            text="Локальный MTProto → WebSocket",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            anchor="w",
        )
        self.status_hint.pack(anchor="w")

        opts = self._card(self)
        opts.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(
            opts,
            text="НАСТРОЙКИ",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(14, 6))

        self.sw_autostart = ctk.CTkSwitch(
            opts,
            text="Запускать с Windows",
            font=ctk.CTkFont(size=14),
            progress_color=PRIMARY,
            command=self._on_autostart_toggle,
        )
        self.sw_autostart.pack(anchor="w", padx=18, pady=5)

        self.sw_auto_enable = ctk.CTkSwitch(
            opts,
            text="Включать прокси при старте",
            font=ctk.CTkFont(size=14),
            progress_color=PRIMARY,
            command=self._persist,
        )
        if self.cfg.auto_enable:
            self.sw_auto_enable.select()
        self.sw_auto_enable.pack(anchor="w", padx=18, pady=5)

        self.sw_tray = ctk.CTkSwitch(
            opts,
            text="Сворачивать в трей при закрытии",
            font=ctk.CTkFont(size=14),
            progress_color=PRIMARY,
            command=self._persist,
        )
        if self.cfg.minimize_to_tray:
            self.sw_tray.select()
        self.sw_tray.pack(anchor="w", padx=18, pady=(5, 16))

        self.btn_main = ctk.CTkButton(
            self,
            text="Включить прокси",
            height=48,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            corner_radius=14,
            command=self._toggle,
        )
        self.btn_main.pack(fill="x", padx=20, pady=(0, 10))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 8))

        btn_style = {"height": 38, "fg_color": SURFACE, "hover_color": SURFACE_2, "corner_radius": 12}
        ctk.CTkButton(row, text="Telegram", width=120, command=self._open_tg, **btn_style).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(row, text="Установка", width=120, command=self._run_setup, **btn_style).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(row, text="В трей", width=120, command=self._hide_to_tray, **btn_style).pack(
            side="left"
        )

        ctk.CTkLabel(
            self,
            text=f"v{APP_VERSION} · без ByeDPI и Discord",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=22, pady=(8, 16))

    def _read_config(self) -> LiteConfig:
        return LiteConfig(
            minimize_to_tray=bool(self.sw_tray.get()),
            autostart=bool(self.sw_autostart.get()),
            auto_enable=bool(self.sw_auto_enable.get()),
        )

    def _persist(self) -> None:
        self.cfg = self._read_config()
        save_lite_config(self.cfg)

    def _sync_autostart_switch(self) -> None:
        enabled = autostart_enabled()
        if enabled:
            self.sw_autostart.select()
        else:
            self.sw_autostart.deselect()
        if self.cfg.autostart != enabled:
            self.cfg.autostart = enabled
            save_lite_config(self.cfg)

    def _on_autostart_toggle(self) -> None:
        want = bool(self.sw_autostart.get())
        try:
            set_autostart(want)
            self.cfg = self._read_config()
            self.cfg.autostart = want
            save_lite_config(self.cfg)
        except Exception as e:
            self.sw_autostart.select() if not want else self.sw_autostart.deselect()
            mb.showerror("DpiBypass Lite", f"Не удалось настроить автозапуск:\n{e}")

    def _refresh_status(self) -> None:
        on = self.tgws.running
        self.status_dot.configure(text_color=OK if on else ERR)
        self.status_text.configure(text="Прокси активен" if on else "Выключено")
        self.status_hint.configure(
            text="127.0.0.1:1443 · нажмите Telegram для ссылки" if on else "Локальный MTProto → WebSocket"
        )
        self.btn_main.configure(
            text="Выключить прокси" if on else "Включить прокси",
            fg_color=DISCONNECT if on else PRIMARY,
            hover_color="#DC2626" if on else PRIMARY_HOVER,
            state="disabled" if self._busy else "normal",
        )

    def _ensure_tgws(self) -> None:
        if not TgWsService.is_available():
            raise FileNotFoundError(
                "Нет модуля tg-ws-proxy.\nНажмите «Установка» для загрузки."
            )
        if not self.tgws.running:
            self.tgws.start()

    def _start(self) -> None:
        self._ensure_tgws()
        self._refresh_status()

    def _stop(self) -> None:
        self.tgws.stop()
        self._refresh_status()

    def _toggle(self) -> None:
        try:
            if self.tgws.running:
                self._stop()
            else:
                self._start()
        except Exception as e:
            mb.showerror("DpiBypass Lite", str(e))
            self._refresh_status()

    def _try_auto_enable(self) -> None:
        if self._quitting or not is_alive(self) or self.tgws.running or self._busy:
            return
        self.cfg = load_lite_config()
        if not self.cfg.auto_enable and not self.launched_autostart:
            return
        try:
            self._busy = True
            self._refresh_status()
            self._start()
            if self.launched_autostart and self.cfg.minimize_to_tray:
                self._hide_to_tray()
        except Exception as e:
            if not self.launched_autostart:
                mb.showerror("DpiBypass Lite", str(e))
            else:
                self._ensure_tray()
        finally:
            self._busy = False
            self._refresh_status()

    def _open_tg(self) -> None:
        try:
            self._start()
            TgWsService.open_telegram_proxy()
        except Exception as e:
            mb.showerror("DpiBypass Lite", str(e))

    def _run_setup(self) -> None:
        setup = WINDOWS_ROOT / "setup-lite.ps1"
        subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(setup)],
            cwd=str(WINDOWS_ROOT),
        )
        mb.showinfo(
            "DpiBypass Lite",
            "Запущена установка tg-ws-proxy.\nПосле завершения включите прокси снова.",
        )

    def _hide_to_tray(self) -> None:
        if self._quitting or not is_alive(self):
            return
        self._ensure_tray()
        self.withdraw()

    def _ensure_tray(self) -> None:
        if self._tray is not None:
            return
        import pystray

        def show(_icon=None, _item=None):
            safe_after(self, 0, self._show_from_tray)

        def toggle(_icon=None, _item=None):
            safe_after(self, 0, self._toggle)

        def quit_app(_icon=None, _item=None):
            safe_after(self, 0, self._quit_app)

        menu = pystray.Menu(
            pystray.MenuItem("Открыть", show, default=True),
            pystray.MenuItem("Вкл / выкл прокси", toggle),
            pystray.MenuItem("Выход", quit_app),
        )
        self._tray = pystray.Icon("DpiBypassLite", _make_tray_image(), "DpiBypass Lite", menu)

        def run_tray():
            self._tray.run()

        self._tray_thread = threading.Thread(target=run_tray, daemon=True)
        self._tray_thread.start()

    def _show_from_tray(self) -> None:
        if self._quitting or not is_alive(self):
            return
        self.deiconify()
        self.lift()
        self.focus_force()

    def _on_close(self) -> None:
        self.cfg = self._read_config()
        save_lite_config(self.cfg)
        if self.cfg.minimize_to_tray:
            self._hide_to_tray()
            return
        self._quit_app()

    def _quit_app(self) -> None:
        if self._quitting:
            return
        self._quitting = True
        if self.tgws.running:
            self.tgws.stop()
        if self._tray:
            try:
                self._tray.stop()
            except Exception:
                pass
        try:
            self.quit()
        except Exception:
            pass
        try:
            if is_alive(self):
                self.destroy()
        except Exception:
            pass


def main() -> None:
    args = _parse_args()
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    app = LiteWindow(launched_autostart=args.autostart)

    if not args.autostart and not TgWsService.is_available():
        mb.showwarning(
            "DpiBypass Lite",
            "Модуль tg-ws-proxy не установлен.\nНажмите «Установка».",
        )

    try:
        app.mainloop()
    except Exception:
        pass


if __name__ == "__main__":
    main()
