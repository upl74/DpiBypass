# -*- coding: utf-8 -*-
"""DpiBypass — Windows UI."""

from __future__ import annotations

import subprocess
import sys
import threading
import tkinter.messagebox as mb
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageDraw

from core.config import AppConfig, load_config, save_config
from core.engine import BypassEngine
from core.paths import BYEDPI_EXE, WINDOWS_ROOT
from core.tgws import TgWsService
from core.presets import PRESET_LABELS

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT = "#1a8cff"
BG = "#0d1117"
CARD = "#161b22"
TEXT_MUTED = "#8b949e"
OK = "#3fb950"
ERR = "#f85149"


def _make_tray_image(size: int = 64) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, size - 4, size - 4), fill=ACCENT)
    d.rectangle((size // 2 - 6, size // 3, size // 2 + 6, size * 2 // 3), fill="white")
    return img


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.engine = BypassEngine()
        self.cfg = load_config()
        self._tray = None
        self._tray_thread = None
        self._preset_keys = list(PRESET_LABELS.keys())

        self.title("DpiBypass")
        self.geometry("420x520")
        self.minsize(400, 480)
        self.configure(fg_color=BG)

        self._build_ui()
        self._refresh_status()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        pad = {"padx": 20, "pady": (0, 8)}

        header = ctk.CTkFrame(self, fg_color=CARD, corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 12))

        ctk.CTkLabel(
            header,
            text="DpiBypass",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 0))

        ctk.CTkLabel(
            header,
            text="Telegram · YouTube · Instagram",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=16, pady=(0, 12))

        self.status_dot = ctk.CTkLabel(header, text="●", font=ctk.CTkFont(size=28), text_color=ERR)
        self.status_dot.pack(anchor="w", padx=16, pady=(0, 0))

        self.status_text = ctk.CTkLabel(
            header,
            text="Выключено",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.status_text.pack(anchor="w", padx=16, pady=(0, 14))

        card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=12)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        ctk.CTkLabel(card, text="Пресет ByeDPI", anchor="w").pack(fill="x", padx=16, pady=(16, 4))
        labels = [PRESET_LABELS[k] for k in self._preset_keys]
        idx = self._preset_keys.index(self.cfg.preset) if self.cfg.preset in self._preset_keys else 0
        self.preset_box = ctk.CTkComboBox(card, values=labels, state="readonly", width=360)
        self.preset_box.set(labels[idx])
        self.preset_box.pack(padx=16, pady=(0, 12))

        self.sw_byedpi = ctk.CTkSwitch(card, text="YouTube / Instagram (ByeDPI)")
        self.sw_byedpi.select() if self.cfg.enable_byedpi else self.sw_byedpi.deselect()
        self.sw_byedpi.pack(anchor="w", padx=16, pady=6)

        self.sw_sys = ctk.CTkSwitch(card, text="Системный SOCKS-прокси (браузер)")
        self.sw_sys.select() if self.cfg.enable_sys_proxy else self.sw_sys.deselect()
        self.sw_sys.pack(anchor="w", padx=16, pady=6)

        self.sw_tg = ctk.CTkSwitch(card, text="Telegram WS-прокси")
        self.sw_tg.select() if self.cfg.enable_tgws else self.sw_tg.deselect()
        self.sw_tg.pack(anchor="w", padx=16, pady=(6, 16))

        self.btn_main = ctk.CTkButton(
            self,
            text="Включить обход",
            height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=ACCENT,
            hover_color="#1466cc",
            command=self._toggle,
        )
        self.btn_main.pack(fill="x", padx=20, pady=(0, 8))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkButton(row, text="Telegram", width=120, fg_color=CARD, hover_color="#21262d", command=self._open_tg).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(row, text="Компоненты", width=120, fg_color=CARD, hover_color="#21262d", command=self._run_setup).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(row, text="Свернуть", width=120, fg_color=CARD, hover_color="#21262d", command=self._hide_to_tray).pack(
            side="left"
        )

        hint = (
            "TG: включите обход и нажмите «Telegram» для ссылки на прокси.\n"
            "YT/IG: откройте в Edge или Chrome."
        )
        ctk.CTkLabel(self, text=hint, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, justify="left").pack(
            anchor="w", padx=22, pady=(4, 16)
        )

    def _read_config(self) -> AppConfig:
        label = self.preset_box.get()
        preset = self._preset_keys[[PRESET_LABELS[k] for k in self._preset_keys].index(label)]
        return AppConfig(
            preset=preset,
            enable_byedpi=bool(self.sw_byedpi.get()),
            enable_tgws=bool(self.sw_tg.get()),
            enable_sys_proxy=bool(self.sw_sys.get()),
            minimize_to_tray=self.cfg.minimize_to_tray,
        )

    def _refresh_status(self) -> None:
        on = self.engine.active
        self.status_dot.configure(text_color=OK if on else ERR)
        self.status_text.configure(text="Обход активен" if on else "Выключено")
        self.btn_main.configure(text="Выключить обход" if on else "Включить обход")
        state = "disabled" if on else "normal"
        self.preset_box.configure(state="disabled" if on else "readonly")
        self.sw_byedpi.configure(state=state)
        self.sw_sys.configure(state=state)
        self.sw_tg.configure(state=state)

    def _toggle(self) -> None:
        try:
            if self.engine.active:
                self.engine.stop()
            else:
                self.cfg = self._read_config()
                save_config(self.cfg)
                if self.cfg.enable_byedpi and not BYEDPI_EXE.is_file():
                    raise FileNotFoundError("Сначала установите компоненты (кнопка «Компоненты»).")
                if self.cfg.enable_tgws and not TgWsService.is_available():
                    raise FileNotFoundError("Нет модуля tg-ws-proxy — нажмите «Компоненты».")
                self.engine.start(self.cfg)
            self._refresh_status()
        except Exception as e:
            mb.showerror("DpiBypass", str(e))

    def _open_tg(self) -> None:
        try:
            if not self.engine.tgws.running:
                self.engine.tgws.start()
                self._refresh_status()
            TgWsService.open_telegram_proxy()
        except Exception as e:
            mb.showerror("DpiBypass", str(e))

    def _run_setup(self) -> None:
        setup = WINDOWS_ROOT / "setup.ps1"
        subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(setup)],
            cwd=str(WINDOWS_ROOT),
        )
        mb.showinfo("DpiBypass", "Откроется установка компонентов.\nПосле завершения включите обход снова.")

    def _hide_to_tray(self) -> None:
        self._ensure_tray()
        self.withdraw()

    def _ensure_tray(self) -> None:
        if self._tray is not None:
            return
        import pystray

        def show(_icon=None, _item=None):
            self.after(0, self._show_from_tray)

        def quit_app(_icon=None, _item=None):
            self.after(0, self._quit_app)

        menu = pystray.Menu(
            pystray.MenuItem("Открыть", show, default=True),
            pystray.MenuItem("Выключить обход", lambda *_: self.after(0, self._stop_and_show)),
            pystray.MenuItem("Выход", quit_app),
        )
        self._tray = pystray.Icon("DpiBypass", _make_tray_image(), "DpiBypass", menu)

        def run_tray():
            self._tray.run()

        self._tray_thread = threading.Thread(target=run_tray, daemon=True)
        self._tray_thread.start()

    def _show_from_tray(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()

    def _stop_and_show(self) -> None:
        if self.engine.active:
            self.engine.stop()
            self._refresh_status()
        self._show_from_tray()

    def _on_close(self) -> None:
        self.cfg = self._read_config()
        save_config(self.cfg)
        if self.cfg.minimize_to_tray and self.engine.active:
            self._hide_to_tray()
            return
        self._quit_app()

    def _quit_app(self) -> None:
        if self.engine.active:
            self.engine.stop()
        if self._tray:
            self._tray.stop()
        self.destroy()


def main() -> None:
    app = MainWindow()
    missing = []
    if not BYEDPI_EXE.is_file():
        missing.append("ciadpi")
    if not TgWsService.is_available():
        missing.append("tg-ws-proxy")
    if missing:
        mb.showwarning(
            "DpiBypass",
            "Не установлены: " + ", ".join(missing) + ".\n"
            "Нажмите «Компоненты» для загрузки.",
        )
    app.mainloop()


if __name__ == "__main__":
    main()
