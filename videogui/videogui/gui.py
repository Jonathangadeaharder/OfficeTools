import subprocess
import threading
import tkinter as tk
import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


class VideoTools:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Video Tools")
        self.root.geometry("520x400")
        self.root.minsize(440, 320)
        self.root.configure(padx=12, pady=12)

        style = ttk.Style()
        style.theme_use("aqua")

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._setup_logging()
        self._build_ui()
        self._log("Application started")

    def _setup_logging(self) -> None:
        self.log_dir = Path.home() / ".local" / "state" / "OfficeTools" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"{datetime.date.today()}.log"

        for f in self.log_dir.glob("*.log"):
            if f.name != self.log_file.name:
                try:
                    f.unlink()
                except Exception:
                    pass

    def _log(self, message: str) -> None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] [VideoGui] {message}\n")

    def _build_ui(self) -> None:
        ttk.Button(self.root, text="Select Files...", command=self._select).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        frame = ttk.Frame(self.root)
        frame.grid(row=1, column=0, sticky="nsew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            frame,
            selectmode="extended",
            font=("Menlo", 11),
            relief="flat",
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        ttk.Button(self.root, text="Remove Selected", command=self._remove).grid(
            row=2, column=0, sticky="w", pady=(8, 6)
        )

        btn_frame = ttk.Frame(self.root)
        btn_frame.grid(row=3, column=0, sticky="w", pady=(0, 6))

        ttk.Button(btn_frame, text="Extract Audio", command=self._extract_audio).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(btn_frame, text="Add Subtitles", command=self._add_subtitles).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(btn_frame, text="Compress Video", command=self._compress_video).pack(
            side="left"
        )

        self.progress = ttk.Progressbar(
            self.root, orient="horizontal", mode="determinate"
        )
        self.progress.grid(row=4, column=0, sticky="ew", pady=(8, 0))

        self.status = ttk.Label(self.root, text="Select files to begin...")
        self.status.grid(row=5, column=0, sticky="w", pady=(4, 0))

    def _select(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=[("Video files", "*.mp4"), ("Subtitle files", "*.srt")],
        )
        for p in paths:
            if p not in self.listbox.get(0, "end"):
                self.listbox.insert("end", p)
                self._log(f"Added file: {p}")
        self._update_status()

    def _remove(self) -> None:
        selected = list(self.listbox.curselection())
        for idx in reversed(selected):
            p = self.listbox.get(idx)
            self.listbox.delete(idx)
            self._log(f"Removed file: {p}")
        self._update_status()

    def _update_status(self) -> None:
        n = self.listbox.size()
        self.status.configure(text=f"{n} file(s) selected")

    def _get_files(self) -> list[Path]:
        return [Path(self.listbox.get(i)) for i in range(self.listbox.size())]

    def _set_buttons_state(self, state: str) -> None:
        stack: list[tk.Misc] = list(self.root.winfo_children())
        while stack:
            w = stack.pop()
            if isinstance(w, ttk.Button):
                w.configure(state=state)
            stack.extend(w.winfo_children())

    def _disable_buttons(self) -> None:
        self._set_buttons_state("disabled")

    def _enable_buttons(self) -> None:
        self._set_buttons_state("normal")

    def _extract_audio(self) -> None:
        files = self._get_files()
        mp4s = [f for f in files if f.suffix.lower() == ".mp4"]
        if not mp4s:
            messagebox.showwarning("No MP4s", "Select at least one MP4 file.")
            return

        self._disable_buttons()
        self.progress["mode"] = "indeterminate"
        self.progress["maximum"] = len(mp4s)
        self.progress["value"] = 0
        self._log(f"Extracting audio from {len(mp4s)} file(s)")

        self._proc_audio(mp4s, 0)

    def _proc_audio(self, mp4s: list[Path], idx: int) -> None:
        if idx >= len(mp4s):
            self._log("Audio extraction batch complete")
            self.progress.stop()
            self.progress["mode"] = "determinate"
            self.progress["value"] = len(mp4s)
            self._enable_buttons()
            self.listbox.delete(0, "end")
            self._update_status()
            messagebox.showinfo(
                "Complete", f"Audio extracted from {len(mp4s)} file(s)."
            )
            return

        f = mp4s[idx]
        self.status.configure(text=f"Extracting {idx + 1}/{len(mp4s)}: {f.name}...")
        self.progress["value"] = idx
        self.progress.start(15)
        self._log(f"Processing mp4audio: {f}")

        def _run() -> None:
            try:
                subprocess.run(
                    ["mp4audio", str(f)],
                    check=True,
                    text=True,
                    capture_output=True,
                )
                ok = True
            except subprocess.CalledProcessError:
                ok = False

            self.root.after(0, lambda: self._on_audio_done(ok, f, mp4s, idx))

        threading.Thread(target=_run, daemon=True).start()

    def _on_audio_done(self, ok: bool, f: Path, mp4s: list[Path], idx: int) -> None:
        self.progress.stop()
        if not ok:
            self._log(f"Error during mp4audio on {f.name}")
            self._enable_buttons()
            self.progress["mode"] = "determinate"
            messagebox.showerror("Error", f"Failed on {f.name}")
            self._update_status()
            return

        self._log(f"Successfully completed mp4audio: {f.name}")
        self.progress["value"] = idx + 1
        self._proc_audio(mp4s, idx + 1)

    def _add_subtitles(self) -> None:
        files = self._get_files()
        mp4s = [f for f in files if f.suffix.lower() == ".mp4"]
        srts = [f for f in files if f.suffix.lower() == ".srt"]

        if len(mp4s) != 1 or len(srts) != 1:
            messagebox.showwarning(
                "Invalid Selection",
                "Select exactly 1 MP4 and 1 SRT file.",
            )
            return

        self._disable_buttons()
        self.progress["mode"] = "indeterminate"
        self.progress.start(15)
        self.status.configure(text="Adding subtitles...")
        self._log(f"Adding subtitles: {srts[0].name} -> {mp4s[0].name}")

        def _run() -> None:
            try:
                subprocess.run(
                    ["mp4subs", str(mp4s[0]), str(srts[0])],
                    check=True,
                    text=True,
                    capture_output=True,
                )
                ok = True
            except subprocess.CalledProcessError:
                ok = False

            self.root.after(0, lambda: self._on_subs_done(ok))

        threading.Thread(target=_run, daemon=True).start()

    def _on_subs_done(self, ok: bool) -> None:
        self.progress.stop()
        self.progress["mode"] = "determinate"
        self._enable_buttons()
        if not ok:
            self._log("Error adding subtitles")
            messagebox.showerror("Error", "Failed")
            self._update_status()
            return

        self._log("Subtitles added successfully")
        self.progress["value"] = 1
        messagebox.showinfo("Complete", "Subtitles added successfully.")
        self.listbox.delete(0, "end")
        self._update_status()

    def _compress_video(self) -> None:
        files = self._get_files()
        mp4s = [f for f in files if f.suffix.lower() == ".mp4"]
        if not mp4s:
            messagebox.showwarning("No MP4s", "Select at least one MP4 file.")
            return

        self._disable_buttons()
        self.progress["mode"] = "indeterminate"
        self.progress["maximum"] = len(mp4s)
        self.progress["value"] = 0
        self._log(f"Compressing {len(mp4s)} video file(s)")

        self._proc_compress(mp4s, 0)

    def _proc_compress(self, mp4s: list[Path], idx: int) -> None:
        if idx >= len(mp4s):
            self._log("Video compression batch complete")
            self.progress.stop()
            self.progress["mode"] = "determinate"
            self.progress["value"] = len(mp4s)
            self._enable_buttons()
            self.listbox.delete(0, "end")
            self._update_status()
            messagebox.showinfo("Complete", f"Videos compressed: {len(mp4s)} file(s).")
            return

        f = mp4s[idx]
        self.status.configure(text=f"Compressing {idx + 1}/{len(mp4s)}: {f.name}...")
        self.progress["value"] = idx
        self.progress.start(15)
        self._log(f"Processing videocompress: {f}")

        def _run() -> None:
            try:
                subprocess.run(
                    ["videocompress", str(f)],
                    check=True,
                    text=True,
                    capture_output=True,
                )
                ok = True
            except subprocess.CalledProcessError:
                ok = False

            self.root.after(0, lambda: self._on_compress_done(ok, f, mp4s, idx))

        threading.Thread(target=_run, daemon=True).start()

    def _on_compress_done(self, ok: bool, f: Path, mp4s: list[Path], idx: int) -> None:
        self.progress.stop()
        if not ok:
            self._log(f"Error during videocompress on {f.name}")
            self._enable_buttons()
            self.progress["mode"] = "determinate"
            messagebox.showerror("Error", f"Failed on {f.name}")
            self._update_status()
            return

        self._log(f"Successfully completed videocompress: {f.name}")
        self.progress["value"] = idx + 1
        self._proc_compress(mp4s, idx + 1)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = VideoTools()
    app.run()
