"""Confirm best Discord zapret preset before launch."""

from __future__ import annotations

import subprocess
from typing import Callable

import customtkinter as ctk
import tkinter.messagebox as mb

from core.discord import launch_desktop
from core.discord_autostart import persist_discord_preset
from core.engine import BypassEngine, ComponentId
from core.zapret_benchmark import PresetScore, rank_results
from core.zapret_presets import default_preset_name

BG = "#0F172A"
SURFACE = "#1E293B"
SURFACE_2 = "#334155"
TEXT = "#F8FAFC"
TEXT_MUTED = "#94A3B8"
PRIMARY = "#0EA5E9"
OK = "#22C55E"
OUTLINE = "#475569"


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
        self.geometry("560x520")
        self.minsize(500, 460)
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
            text="Выберите настройку и подтвердите запуск Discord",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=20, pady=(0, 12))

        list_frame = ctk.CTkScrollableFrame(
            self, fg_color=SURFACE, corner_radius=12, height=200
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
                command=self._update_details,
            ).pack(anchor="w", padx=12, pady=6)

        ctk.CTkLabel(
            self,
            text="Детали выбранного пресета",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=20, pady=(4, 4))

        self.details = ctk.CTkTextbox(
            self,
            height=120,
            fg_color=SURFACE,
            text_color=TEXT,
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.details.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        self.details.configure(state="disabled")

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

        ctk.CTkButton(
            row,
            text="Применить и запустить Discord",
            fg_color=PRIMARY,
            hover_color="#0284C7",
            command=self._on_confirm,
        ).pack(side="right")

        self._update_details()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _selected(self) -> PresetScore | None:
        name = self._choice.get()
        for item in self._ranked:
            if item.name == name:
                return item
        return self._ranked[0] if self._ranked else None

    def _update_details(self) -> None:
        item = self._selected()
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        if not item:
            self.details.insert("end", "Нет данных")
        elif item.details:
            for key, val in item.details.items():
                self.details.insert("end", f"{key}: {val}\n")
        else:
            self.details.insert(
                "end",
                f"Пресет: {item.name}\n"
                "Полная проверка не выполнена — запасной вариант.",
            )
        self.details.configure(state="disabled")

    def _on_confirm(self) -> None:
        item = self._selected()
        if not item:
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
