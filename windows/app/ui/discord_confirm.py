"""Confirm best Discord zapret preset before launch."""

from __future__ import annotations

import subprocess
import threading
from typing import Callable

import customtkinter as ctk
import tkinter.messagebox as mb

from core.config import load_config
from core.admin import is_admin
from core.discord import launch_desktop
from core.discord_autostart import persist_discord_preset
from core.engine import BypassEngine, ComponentId
from core.zapret_benchmark import PresetScore, live_test_preset, rank_results
from core.zapret_presets import default_preset_name
from core.zapret_runtime import version_label

BG = "#0F172A"
SURFACE = "#1E293B"
SURFACE_2 = "#334155"
TEXT = "#F8FAFC"
TEXT_MUTED = "#94A3B8"
PRIMARY = "#0EA5E9"
OK = "#22C55E"
WARN = "#F59E0B"


class DiscordConfirmDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        engine: BypassEngine,
        results: list[PresetScore],
        suggested: str | None,
        on_applied: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.engine = engine
        self.on_applied = on_applied
        self._choice = ctk.StringVar(value="")
        self._testing = False
        self._last_live: PresetScore | None = None

        ranked = rank_results([r for r in results if r.score > 0])
        if not ranked and suggested:
            ranked = [
                PresetScore(
                    name=suggested,
                    label=suggested,
                    score=0,
                    ok_count=0,
                    details={},
                )
            ]
        if not ranked:
            ranked = [
                PresetScore(
                    name=default_preset_name(),
                    label="general (стандарт)",
                    score=0,
                    ok_count=0,
                    details={},
                )
            ]

        self._ranked = ranked[:10]
        default_name = suggested or self._ranked[0].name
        if not any(r.name == default_name for r in self._ranked):
            default_name = self._ranked[0].name
        self._choice.set(default_name)

        self.title("Результаты проверки Discord")
        self.geometry("580x580")
        self.minsize(520, 500)
        self.configure(fg_color=BG)
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(
            self,
            text="Лучшие пресеты zapret",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT,
        ).pack(anchor="w", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            self,
            text="Выберите → Проверить настройку → Применить",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=20, pady=(0, 8))

        ctk.CTkLabel(
            self,
            text=f"zapret: {version_label()} · запуск как в оригинальном .bat",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=20, pady=(0, 8))

        if not is_admin():
            ctk.CTkLabel(
                self,
                text="⚠ Нужен запуск DpiBypass от администратора",
                font=ctk.CTkFont(size=12),
                text_color=WARN,
            ).pack(anchor="w", padx=20, pady=(0, 8))

        self.test_status = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            anchor="w",
        )
        self.test_status.pack(fill="x", padx=20, pady=(0, 8))

        list_frame = ctk.CTkScrollableFrame(
            self, fg_color=SURFACE, corner_radius=12, height=180
        )
        list_frame.pack(fill="x", padx=20, pady=(0, 10))

        for idx, item in enumerate(self._ranked, start=1):
            badge = " ★ рекомендуем" if item.name == (suggested or "") else ""
            text = f"{idx}. {item.label} — балл {item.score}, {item.ok_count}/5 OK{badge}"
            ctk.CTkRadioButton(
                list_frame,
                text=text,
                variable=self._choice,
                value=item.name,
                font=ctk.CTkFont(size=13),
                text_color=OK if idx == 1 else TEXT,
                fg_color=PRIMARY,
                hover_color="#0284C7",
                command=self._on_selection_changed,
            ).pack(anchor="w", padx=12, pady=6)

        ctk.CTkLabel(
            self,
            text="Детали выбранного пресета",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=20, pady=(4, 4))

        self.details = ctk.CTkTextbox(
            self,
            height=130,
            fg_color=SURFACE,
            text_color=TEXT,
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.details.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        self.details.configure(state="disabled")

        test_row = ctk.CTkFrame(self, fg_color="transparent")
        test_row.pack(fill="x", padx=20, pady=(0, 8))

        self.btn_test = ctk.CTkButton(
            test_row,
            text="Проверить настройку",
            fg_color=SURFACE_2,
            hover_color="#475569",
            command=self._on_test,
        )
        self.btn_test.pack(side="left", padx=(0, 8))

        self.btn_try_discord = ctk.CTkButton(
            test_row,
            text="Открыть Discord (тест)",
            fg_color=SURFACE_2,
            hover_color="#475569",
            command=self._on_try_discord,
        )
        self.btn_try_discord.pack(side="left")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkButton(
            row,
            text="Отмена",
            width=120,
            fg_color=SURFACE,
            hover_color=SURFACE_2,
            command=self._on_cancel,
        ).pack(side="right", padx=(8, 0))

        self.btn_confirm = ctk.CTkButton(
            row,
            text="Применить и запустить Discord",
            fg_color=PRIMARY,
            hover_color="#0284C7",
            command=self._on_confirm,
        )
        self.btn_confirm.pack(side="right")

        self._update_details()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _selected(self) -> PresetScore | None:
        name = self._choice.get()
        for item in self._ranked:
            if item.name == name:
                return item
        return self._ranked[0] if self._ranked else None

    def _on_selection_changed(self) -> None:
        self._last_live = None
        self.test_status.configure(text="", text_color=TEXT_MUTED)
        self._update_details()

    def _set_actions_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.btn_test.configure(state=state)
        self.btn_try_discord.configure(state=state)
        self.btn_confirm.configure(state=state)

    def _update_details(self, live: PresetScore | None = None) -> None:
        item = live or self._selected()
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        if not item:
            self.details.insert("end", "Нет данных")
        else:
            if live:
                self.details.insert("end", "=== Живая проверка ===\n")
                self.details.insert(
                    "end",
                    f"Балл: {item.score} · {item.ok_count}/5 OK\n\n",
                )
            elif item.details:
                self.details.insert("end", "=== Результаты автотеста ===\n\n")
            for key, val in (item.details or {}).items():
                self.details.insert("end", f"{key}: {val}\n")
            if not item.details:
                self.details.insert(
                    "end",
                    f"Пресет: {item.name}\n"
                    "Нажмите «Проверить настройку» для живой проверки.",
                )
        self.details.configure(state="disabled")

    def _on_test(self) -> None:
        item = self._selected()
        if not item or self._testing:
            return
        self._testing = True
        self._set_actions_enabled(False)
        self.btn_test.configure(text="Проверка…")
        self.test_status.configure(
            text=f"Проверяем: {item.label}…",
            text_color=TEXT_MUTED,
        )
        thread = threading.Thread(
            target=self._run_test,
            args=(item.name, item.label),
            daemon=True,
        )
        thread.start()

    def _run_test(self, preset_name: str, label: str) -> None:
        try:
            scored = live_test_preset(self.engine.winws, preset_name, label)
            self.after(0, lambda: self._on_test_done(scored, None))
        except Exception as exc:
            self.after(0, lambda: self._on_test_done(None, exc))

    def _on_test_done(self, scored: PresetScore | None, error: Exception | None) -> None:
        self._testing = False
        self.btn_test.configure(text="Проверить настройку")
        self._set_actions_enabled(True)

        if error:
            self.test_status.configure(
                text=f"Ошибка проверки: {error}",
                text_color=WARN,
            )
            mb.showerror("Проверка", str(error), parent=self)
            return

        assert scored is not None
        self._last_live = scored
        for idx, item in enumerate(self._ranked):
            if item.name == scored.name:
                self._ranked[idx] = scored
                break

        if scored.ok_count >= 4:
            color = OK
            hint = f"✓ {scored.label}: {scored.ok_count}/5 OK — можно применять"
        elif scored.ok_count > 0:
            color = WARN
            hint = f"△ {scored.label}: {scored.ok_count}/5 OK — попробуйте другой пресет"
        else:
            color = WARN
            hint = f"✗ {scored.label}: не прошёл проверку"

        self.test_status.configure(text=hint, text_color=color)
        self._update_details(live=scored)

    def _on_try_discord(self) -> None:
        item = self._selected()
        if not item or self._testing:
            return
        try:
            self.engine.winws.start_preset(item.name)
            subprocess.run(
                ["taskkill", "/IM", "Discord.exe", "/F"],
                creationflags=0x08000000,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            launch_desktop(load_config().socks_port)
            mb.showinfo(
                "Тестовый запуск",
                f"Discord открыт с пресетом:\n{item.name}\n\n"
                "Настройка ещё не сохранена.\n"
                "Если всё работает — нажмите «Применить и запустить Discord».",
                parent=self,
            )
        except Exception as exc:
            mb.showerror("Discord", str(exc), parent=self)

    def _on_confirm(self) -> None:
        item = self._last_live if self._last_live and self._last_live.name == self._choice.get() else self._selected()
        if not item:
            return

        if self._last_live is None or self._last_live.name != item.name:
            if not mb.askyesno(
                "Подтверждение",
                "Вы не проверили эту настройку живым тестом.\n"
                "Всё равно применить?",
                parent=self,
            ):
                return

        preset = item.name
        try:
            cfg = persist_discord_preset(preset)
            if not self.engine.is_running(ComponentId.DISCORD):
                self.engine.start_component(ComponentId.DISCORD, cfg)
            else:
                self.engine.winws.start_preset(preset)

            subprocess.run(
                ["taskkill", "/IM", "Discord.exe", "/F"],
                creationflags=0x08000000,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            launch_desktop(cfg.socks_port)

            if self.on_applied:
                self.on_applied()

            mb.showinfo(
                "Discord",
                f"Применён пресет:\n{preset}\n\nDiscord запускается…",
                parent=self,
            )
            self.grab_release()
            self.destroy()
        except Exception as exc:
            mb.showerror("Discord", str(exc), parent=self)

    def _on_cancel(self) -> None:
        self.grab_release()
        self.destroy()
