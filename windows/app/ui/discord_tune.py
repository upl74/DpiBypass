"""Discord preset auto-tune dialog."""

from __future__ import annotations

import threading
from threading import Event

import customtkinter as ctk

from core.engine import BypassEngine
from core.zapret_benchmark import run_benchmark
from ui.discord_confirm import DiscordConfirmDialog

BG = "#0F172A"
SURFACE = "#1E293B"
TEXT = "#F8FAFC"
TEXT_MUTED = "#94A3B8"
PRIMARY = "#0EA5E9"


class DiscordTuneDialog(ctk.CTkToplevel):
    def __init__(self, master, engine: BypassEngine) -> None:
        super().__init__(master)
        self.master = master
        self.engine = engine
        self._cancel = Event()
        self._done = False

        self.title("Подбор пресета Discord")
        self.geometry("520x420")
        self.minsize(480, 360)
        self.configure(fg_color=BG)
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(
            self,
            text="Автоподбор пресета zapret",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT,
        ).pack(anchor="w", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            self,
            text="Быстрый отсев → полная проверка лучших кандидатов",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self.progress = ctk.CTkProgressBar(self, width=460, progress_color=PRIMARY)
        self.progress.pack(padx=20, pady=(0, 8))
        self.progress.set(0)

        self.status = ctk.CTkLabel(
            self,
            text="Подготовка…",
            font=ctk.CTkFont(size=13),
            text_color=TEXT,
            anchor="w",
            justify="left",
        )
        self.status.pack(fill="x", padx=20, pady=(0, 8))

        self.log = ctk.CTkTextbox(
            self,
            height=200,
            fg_color=SURFACE,
            text_color=TEXT,
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.log.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        self.log.configure(state="disabled")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 16))

        self.btn_cancel = ctk.CTkButton(
            row,
            text="Отмена",
            width=120,
            fg_color=SURFACE,
            hover_color="#334155",
            command=self._on_cancel,
        )
        self.btn_cancel.pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.after(200, self._start)

    def _append_log(self, line: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _on_progress(self, done: int, total: int, label: str, message: str) -> None:
        def ui() -> None:
            if total > 0:
                self.progress.set(min(1.0, done / total))
            self.status.configure(text=f"[{done}/{total}] {label}")
            self._append_log(message)

        self.after(0, ui)

    def _start(self) -> None:
        thread = threading.Thread(target=self._worker, daemon=True)
        thread.start()

    def _worker(self) -> None:
        def progress(done: int, total: int, label: str, message: str) -> None:
            if not self._cancel.is_set():
                self._on_progress(done, total, label, message)

        def done(best: str | None, score: int, all_results: list) -> None:
            self.after(0, lambda: self._finish(best, score, all_results))

        run_benchmark(self.engine.winws, progress, done, self._cancel)

    def _finish(self, best: str | None, score: int, all_results: list | None = None) -> None:
        if self._done:
            return
        self._done = True

        if self._cancel.is_set():
            self.btn_cancel.configure(text="Закрыть")
            self.status.configure(text="Отменено")
            return

        self.progress.set(1)
        self.status.configure(text="Проверка завершена — выберите пресет…")
        self.grab_release()
        self.destroy()

        def on_applied() -> None:
            if hasattr(self.master, "_sync_boot_switches"):
                self.master._sync_boot_switches()
            if hasattr(self.master, "_refresh_status"):
                self.master._refresh_status()

        DiscordConfirmDialog(
            self.master,
            self.engine,
            all_results or [],
            suggested=best,
            on_applied=on_applied,
        )

    def _on_cancel(self) -> None:
        if not self._done:
            self._cancel.set()
        self.grab_release()
        self.destroy()
