# -*- coding: utf-8 -*-
"""DpiBypass — Windows desktop (v1.3.3+)."""

from __future__ import annotations

import argparse
import subprocess
import sys
import threading
import tkinter.messagebox as mb
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageDraw

from core import autostart
from core.admin import is_admin, relaunch_as_admin
from core.config import AppConfig, load_config, save_config
from core.engine import BypassEngine
from core.paths import BYEDPI_EXE, WINDOWS_ROOT
from core.presets import PRESET_LABELS
from core.tgws import TgWsService
from core.winws import is_available as winws_available

from ui.discord_tune import DiscordTuneDialog

APP_VERSION = "1.3.6"

# Material 3 palette (synced with Android DpiBypass)
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
    cx, cy = size // 2, size // 2 + 2
    d.polygon(
        [
            (cx, cy - size // 5),
            (cx - size // 4, cy + size // 6),
            (cx - size // 10, cy + size // 10),
            (cx + size // 10, cy + size // 10),
            (cx + size // 4, cy + size // 6),
        ],
        fill="white",
    )
    return img


class MainWindow(ctk.CTk):
    def __init__(self, *, launched_autostart: bool = False) -> None:
        super().__init__()
        self.launched_autostart = launched_autostart
        self.engine = BypassEngine()
        self.cfg = load_config()
        self._tray = None
        self._tray_thread = None
        self._preset_keys = list(PRESET_LABELS.keys())
        self._busy = False

        self.title("DpiBypass")
        self.geometry("460x700")
        self.minsize(420, 640)
        self.configure(fg_color=BG)

        self._build_ui()
        self._sync_autostart_switch()
        self._refresh_status()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if launched_autostart and self.cfg.minimize_to_tray:
            self.after(300, self._hide_to_tray)

        if self.cfg.auto_enable:
            self.after(900, self._try_auto_enable)

    def _card(self, parent, **kwargs) -> ctk.CTkFrame:
        return ctk.CTkFrame(
            parent,
            fg_color=SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=OUTLINE,
            **kwargs,
        )

    def _section_title(self, parent, text: str) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(14, 6))

    def _build_ui(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        hero = self._card(scroll)
        hero.pack(fill="x", padx=20, pady=(20, 12))

        top = ctk.CTkFrame(hero, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(16, 8))

        logo = ctk.CTkLabel(top, text="🛡", font=ctk.CTkFont(size=36))
        logo.pack(side="left", padx=(0, 12))

        titles = ctk.CTkFrame(top, fg_color="transparent")
        titles.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            titles,
            text="DpiBypass",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=TEXT,
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            titles,
            text="Telegram · YouTube · Discord · Instagram",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w")

        admin_hint = " · запущено от администратора" if is_admin() else ""
        self.admin_label = ctk.CTkLabel(
            titles,
            text=f"Discord: WinDivert{admin_hint}",
            font=ctk.CTkFont(size=11),
            text_color=OK if is_admin() else "#F59E0B",
            anchor="w",
        )
        self.admin_label.pack(anchor="w")

        status_row = ctk.CTkFrame(hero, fg_color="transparent")
        status_row.pack(fill="x", padx=18, pady=(4, 16))

        self.status_dot = ctk.CTkLabel(
            status_row, text="●", font=ctk.CTkFont(size=22), text_color=ERR
        )
        self.status_dot.pack(side="left", padx=(0, 8))

        status_col = ctk.CTkFrame(status_row, fg_color="transparent")
        status_col.pack(side="left", fill="x", expand=True)
        self.status_text = ctk.CTkLabel(
            status_col,
            text="Выключено",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT,
            anchor="w",
        )
        self.status_text.pack(anchor="w")
        self.status_hint = ctk.CTkLabel(
            status_col,
            text="Нажмите кнопку ниже для запуска",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            anchor="w",
        )
        self.status_hint.pack(anchor="w")

        bypass = self._card(scroll)
        bypass.pack(fill="x", padx=20, pady=(0, 12))

        self._section_title(bypass, "ОБХОД DPI")

        labels = [PRESET_LABELS[k] for k in self._preset_keys]
        idx = self._preset_keys.index(self.cfg.preset) if self.cfg.preset in self._preset_keys else 0
        self.preset_box = ctk.CTkComboBox(
            bypass,
            values=labels,
            state="readonly",
            width=380,
            height=36,
            fg_color=SURFACE_2,
            border_color=OUTLINE,
            button_color=PRIMARY,
            button_hover_color=PRIMARY_HOVER,
            dropdown_fg_color=SURFACE,
            dropdown_hover_color=SURFACE_2,
        )
        self.preset_box.set(labels[idx])
        self.preset_box.pack(padx=18, pady=(0, 10))

        self.sw_byedpi = ctk.CTkSwitch(
            bypass,
            text="ByeDPI (YouTube / Discord / Instagram)",
            font=ctk.CTkFont(size=14),
            progress_color=PRIMARY,
        )
        if self.cfg.enable_byedpi:
            self.sw_byedpi.select()
        self.sw_byedpi.pack(anchor="w", padx=18, pady=5)

        self.sw_discord = ctk.CTkSwitch(
            bypass,
            text="Discord: WinDivert (нужен запуск от администратора)",
            font=ctk.CTkFont(size=14),
            progress_color=PRIMARY,
            command=self._on_discord_toggle,
        )
        if self.cfg.enable_discord:
            self.sw_discord.select()
        self.sw_discord.pack(anchor="w", padx=18, pady=5)

        self.sw_sys = ctk.CTkSwitch(
            bypass,
            text="Системный SOCKS (браузер + Discord в браузере)",
            font=ctk.CTkFont(size=14),
            progress_color=PRIMARY,
        )
        if self.cfg.enable_sys_proxy:
            self.sw_sys.select()
        self.sw_sys.pack(anchor="w", padx=18, pady=5)

        self.sw_tg = ctk.CTkSwitch(
            bypass,
            text="Telegram WS-прокси",
            font=ctk.CTkFont(size=14),
            progress_color=PRIMARY,
        )
        if self.cfg.enable_tgws:
            self.sw_tg.select()
        self.sw_tg.pack(anchor="w", padx=18, pady=(5, 16))

        startup = self._card(scroll)
        startup.pack(fill="x", padx=20, pady=(0, 12))

        self._section_title(startup, "АВТОЗАПУСК")

        self.sw_autostart = ctk.CTkSwitch(
            startup,
            text="Запускать с Windows",
            font=ctk.CTkFont(size=14),
            progress_color=PRIMARY,
            command=self._on_autostart_toggle,
        )
        if self.cfg.autostart:
            self.sw_autostart.select()
        self.sw_autostart.pack(anchor="w", padx=18, pady=5)

        self.sw_auto_enable = ctk.CTkSwitch(
            startup,
            text="Включать обход при старте приложения",
            font=ctk.CTkFont(size=14),
            progress_color=PRIMARY,
            command=self._persist_switches,
        )
        if self.cfg.auto_enable:
            self.sw_auto_enable.select()
        self.sw_auto_enable.pack(anchor="w", padx=18, pady=5)

        self.sw_tray = ctk.CTkSwitch(
            startup,
            text="Сворачивать в трей при закрытии окна",
            font=ctk.CTkFont(size=14),
            progress_color=PRIMARY,
            command=self._persist_switches,
        )
        if self.cfg.minimize_to_tray:
            self.sw_tray.select()
        self.sw_tray.pack(anchor="w", padx=18, pady=(5, 16))

        self.btn_main = ctk.CTkButton(
            scroll,
            text="Включить обход",
            height=48,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            corner_radius=14,
            command=self._toggle,
        )
        self.btn_main.pack(fill="x", padx=20, pady=(0, 10))

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 8))

        btn_style = {"height": 38, "fg_color": SURFACE, "hover_color": SURFACE_2, "corner_radius": 12}
        ctk.CTkButton(row, text="Discord", width=96, command=self._open_discord, **btn_style).pack(
            side="left", padx=(0, 6)
        )
        ctk.CTkButton(row, text="Telegram", width=96, command=self._open_tg, **btn_style).pack(
            side="left", padx=(0, 6)
        )
        ctk.CTkButton(row, text="Компоненты", width=96, command=self._run_setup, **btn_style).pack(
            side="left", padx=(0, 6)
        )
        ctk.CTkButton(row, text="В трей", width=96, command=self._hide_to_tray, **btn_style).pack(
            side="left"
        )

        ctk.CTkLabel(
            scroll,
            text=f"v{APP_VERSION} · Windows · Discord: автоподбор zapret",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=22, pady=(8, 20))

    def _read_config(self) -> AppConfig:
        label = self.preset_box.get()
        preset = self._preset_keys[[PRESET_LABELS[k] for k in self._preset_keys].index(label)]
        return AppConfig(
            preset=preset,
            enable_byedpi=bool(self.sw_byedpi.get()),
            enable_discord=bool(self.sw_discord.get()),
            enable_tgws=bool(self.sw_tg.get()),
            enable_sys_proxy=bool(self.sw_sys.get()),
            minimize_to_tray=bool(self.sw_tray.get()),
            autostart=bool(self.sw_autostart.get()),
            auto_enable=bool(self.sw_auto_enable.get()),
            socks_port=self.cfg.socks_port,
            zapret_preset=self.cfg.zapret_preset,
        )

    def _on_discord_toggle(self) -> None:
        if bool(self.sw_discord.get()):
            label = PRESET_LABELS.get("universal", "")
            if label in self.preset_box.cget("values"):
                self.preset_box.set(label)
        self._persist_switches()

    def _persist_switches(self) -> None:
        self.cfg = self._read_config()
        save_config(self.cfg)

    def _sync_autostart_switch(self) -> None:
        enabled = autostart.is_enabled()
        if enabled:
            self.sw_autostart.select()
        else:
            self.sw_autostart.deselect()
        if self.cfg.autostart != enabled:
            self.cfg.autostart = enabled
            save_config(self.cfg)

    def _on_autostart_toggle(self) -> None:
        want = bool(self.sw_autostart.get())
        try:
            autostart.set_enabled(want)
            self.cfg = self._read_config()
            self.cfg.autostart = want
            save_config(self.cfg)
        except Exception as e:
            self.sw_autostart.select() if not want else self.sw_autostart.deselect()
            mb.showerror("DpiBypass", f"Не удалось настроить автозапуск:\n{e}")

    def _refresh_status(self) -> None:
        on = self.engine.active
        self.status_dot.configure(text_color=OK if on else ERR)
        self.status_text.configure(text="Обход активен" if on else "Выключено")
        if self.cfg.enable_discord and not is_admin() and not on:
            hint = "Для Discord: запуск от администратора"
        elif on:
            if self.cfg.enable_discord:
                hint = f"ByeDPI + zapret ({self.cfg.zapret_preset})"
            else:
                hint = "ByeDPI и прокси работают в фоне"
        else:
            hint = "Нажмите кнопку ниже для запуска"
        self.status_hint.configure(text=hint)
        self.btn_main.configure(
            text="Выключить обход" if on else "Включить обход",
            fg_color=DISCONNECT if on else PRIMARY,
            hover_color="#DC2626" if on else PRIMARY_HOVER,
        )
        state = "disabled" if on or self._busy else "normal"
        self.preset_box.configure(state="disabled" if on or self._busy else "readonly")
        for w in (self.sw_byedpi, self.sw_discord, self.sw_sys, self.sw_tg):
            w.configure(state=state)

    def _validate_components(self, cfg: AppConfig) -> None:
        if cfg.enable_byedpi and not BYEDPI_EXE.is_file():
            raise FileNotFoundError(
                "Нет ciadpi.exe — нажмите «Компоненты» для установки."
            )
        if cfg.enable_tgws and not TgWsService.is_available():
            raise FileNotFoundError(
                "Нет tg-ws-proxy — нажмите «Компоненты» для установки."
            )
        if cfg.enable_discord:
            if not winws_available():
                raise FileNotFoundError(
                    "Нет winws.exe (zapret) — нажмите «Компоненты» для загрузки."
                )
            if not is_admin():
                raise PermissionError("discord_admin")

    def _handle_start_error(self, e: Exception) -> None:
        if isinstance(e, PermissionError) and str(e) == "discord_admin":
            if mb.askyesno(
                "DpiBypass — права администратора",
                "Discord обходится через WinDivert и требует запуск от администратора.\n\n"
                "Перезапустить DpiBypass с правами администратора?",
            ):
                try:
                    relaunch_as_admin()
                    self.after(400, self._quit_app)
                except OSError as err:
                    mb.showerror("DpiBypass", str(err))
            return
        mb.showerror("DpiBypass", str(e))

    def _start_engine(self) -> None:
        self.cfg = self._read_config()
        save_config(self.cfg)
        self._validate_components(self.cfg)
        self.engine.start(self.cfg)
        self._refresh_status()

    def _try_auto_enable(self) -> None:
        if self.engine.active or self._busy:
            return
        if not self.cfg.auto_enable:
            return
        try:
            self._busy = True
            self._refresh_status()
            self._start_engine()
            if self.launched_autostart and self.cfg.minimize_to_tray:
                self._hide_to_tray()
        except Exception as e:
            if not self.launched_autostart:
                self._handle_start_error(e)
            else:
                self._ensure_tray()
        finally:
            self._busy = False
            self._refresh_status()

    def _toggle(self) -> None:
        try:
            if self.engine.active:
                self.engine.stop()
            else:
                self._start_engine()
            self._refresh_status()
        except Exception as e:
            self._handle_start_error(e)
            self._refresh_status()

    def _open_discord(self) -> None:
        try:
            self.cfg = self._read_config()
            if not self.cfg.enable_discord:
                self.sw_discord.select()
                self.cfg.enable_discord = True
            save_config(self.cfg)

            if not winws_available():
                raise FileNotFoundError(
                    "Нет winws.exe (zapret) — нажмите «Компоненты» для загрузки."
                )
            if not is_admin():
                raise PermissionError("discord_admin")

            if not self.engine.active:
                self._validate_components(self.cfg)
                self.engine.start(self.cfg)
                self._refresh_status()

            DiscordTuneDialog(self, self.engine)
        except Exception as e:
            self._handle_start_error(e)

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
        mb.showinfo(
            "DpiBypass",
            "Запущена установка компонентов.\n"
            "После завершения снова нажмите «Включить обход».",
        )

    def _hide_to_tray(self) -> None:
        self._ensure_tray()
        self.withdraw()

    def _ensure_tray(self) -> None:
        if self._tray is not None:
            return
        import pystray

        def show(_icon=None, _item=None):
            self.after(0, self._show_from_tray)

        def toggle(_icon=None, _item=None):
            self.after(0, self._toggle)

        def quit_app(_icon=None, _item=None):
            self.after(0, self._quit_app)

        menu = pystray.Menu(
            pystray.MenuItem("Открыть", show, default=True),
            pystray.MenuItem("Вкл / выкл обход", toggle),
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

    def _on_close(self) -> None:
        self.cfg = self._read_config()
        save_config(self.cfg)
        if self.cfg.minimize_to_tray:
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
    args = _parse_args()
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    app = MainWindow(launched_autostart=args.autostart)

    if not args.autostart:
        missing = []
        if not BYEDPI_EXE.is_file():
            missing.append("ciadpi")
        if not TgWsService.is_available():
            missing.append("tg-ws-proxy")
        if not winws_available():
            missing.append("zapret/winws")
        if missing:
            mb.showwarning(
                "DpiBypass",
                "Не установлены: " + ", ".join(missing) + ".\n"
                "Нажмите «Компоненты» для загрузки.\n\n"
                "Discord: запускайте DpiBypass от имени администратора.",
            )
        elif not is_admin():
            mb.showinfo(
                "DpiBypass",
                "Для Discord включите обход от имени администратора\n"
                "(ПКМ по DpiBypass.exe → Запуск от имени администратора).",
            )

    app.mainloop()


if __name__ == "__main__":
    main()
