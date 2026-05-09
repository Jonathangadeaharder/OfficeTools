import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


class VideoTools:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Video Tools")
        self.root.geometry("480x320")
        self.root.resizable(True, True)
        self.root.configure(padx=12, pady=12)

        style = ttk.Style()
        style.theme_use("aqua")

        self._build_ui()

    def _build_ui(self) -> None:
        ttk.Button(
            self.root, text="Select Files...", command=self._select
        ).pack(pady=(0, 8))

        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            frame,
            selectmode="extended",
            font=("Menlo", 11),
            relief="flat",
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(
            self.root, text="Remove Selected", command=self._remove
        ).pack(pady=(8, 6))

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=(0, 6))

        ttk.Button(
            btn_frame, text="Extract Audio", command=self._extract_audio
        ).pack(side="left", padx=4)
        ttk.Button(
            btn_frame, text="Add Subtitles", command=self._add_subtitles
        ).pack(side="left", padx=4)

        self.status = ttk.Label(self.root, text="Select files to begin...")
        self.status.pack(pady=(4, 0))

    def _select(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=[("Video files", "*.mp4"), ("Subtitle files", "*.srt")],
        )
        for p in paths:
            if p not in self.listbox.get(0, "end"):
                self.listbox.insert("end", p)
        self._update_status()

    def _remove(self) -> None:
        selected = list(self.listbox.curselection())
        for idx in reversed(selected):
            self.listbox.delete(idx)
        self._update_status()

    def _update_status(self) -> None:
        n = self.listbox.size()
        self.status.configure(text=f"{n} file(s) selected")

    def _get_files(self) -> list[Path]:
        return [Path(self.listbox.get(i)) for i in range(self.listbox.size())]

    def _extract_audio(self) -> None:
        files = self._get_files()
        mp4s = [f for f in files if f.suffix.lower() == ".mp4"]
        if not mp4s:
            messagebox.showwarning("No MP4s", "Select at least one MP4 file.")
            return

        self.status.configure(text=f"Extracting audio from {len(mp4s)} file(s)...")
        self.root.update()

        for f in mp4s:
            try:
                subprocess.run(
                    ["mp4audio", str(f)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                messagebox.showerror(
                    "Error",
                    f"Failed on {f.name}:\n{e.stderr}",
                )
                self._update_status()
                return

        messagebox.showinfo("Complete", f"Audio extracted from {len(mp4s)} file(s).")
        self.listbox.delete(0, "end")
        self._update_status()

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

        self.status.configure(text="Adding subtitles...")
        self.root.update()

        try:
            subprocess.run(
                ["mp4subs", str(mp4s[0]), str(srts[0])],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            messagebox.showerror(
                "Error",
                f"Failed:\n{e.stderr}",
            )
            self._update_status()
            return

        messagebox.showinfo("Complete", "Subtitles added successfully.")
        self.listbox.delete(0, "end")
        self._update_status()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = VideoTools()
    app.run()
