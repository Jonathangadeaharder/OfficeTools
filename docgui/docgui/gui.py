import subprocess
import threading
import tkinter as tk
import datetime
import re
import os
from pathlib import Path
from tkinter import filedialog, messagebox, ttk, scrolledtext

CONVERT_FORMATS = ["md", "txt", "pdf", "epub", "mobi"]


class DocTools:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Doc Tools")
        self.root.geometry("600x550")
        self.root.minsize(500, 450)
        self.root.configure(padx=12, pady=12)

        style = ttk.Style()
        style.theme_use("aqua")

        # Layout weights
        self.root.grid_rowconfigure(1, weight=1)  # listbox expands
        self.root.grid_rowconfigure(5, weight=1)  # log expands
        self.root.grid_columnconfigure(0, weight=1)

        self._setup_logging()
        self._build_ui()
        self._log("Application started")

    def _setup_logging(self) -> None:
        self.log_dir = Path.home() / ".local" / "state" / "OfficeTools" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"{datetime.date.today()}.log"

        # Cleanup: remove logs older than today
        for f in self.log_dir.glob("*.log"):
            if f.name != self.log_file.name:
                try:
                    f.unlink()
                except Exception:
                    pass

    def _log(self, message: str) -> None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        with open(self.log_file, "a") as f:
            f.write(f"[DocGui] {log_entry}")

        if hasattr(self, "log_area"):
            self.log_area.configure(state="normal")
            self.log_area.insert("end", log_entry)
            self.log_area.see("end")
            self.log_area.configure(state="disabled")

    def _build_ui(self) -> None:
        # Selection
        ttk.Button(self.root, text="Select Documents...", command=self._select).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        # File List
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

        # List Actions
        ttk.Button(self.root, text="Remove Selected", command=self._remove).grid(
            row=2, column=0, sticky="w", pady=(8, 6)
        )

        # Tool Buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.grid(row=3, column=0, sticky="w", pady=(0, 8))

        ttk.Button(btn_frame, text="Compress", command=self._compress).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(btn_frame, text="OCR", command=self._ocr).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(btn_frame, text="To Markdown", command=self._to_markdown).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(btn_frame, text="Merge", command=self._merge).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(btn_frame, text="Split", command=self._split).pack(side="left")

        # Convert Tools Frame
        convert_frame = ttk.Frame(self.root)
        convert_frame.grid(row=4, column=0, sticky="w", pady=(0, 8))

        ttk.Label(convert_frame, text="Convert to:").pack(side="left", padx=(0, 4))
        self.format_var = tk.StringVar(value=CONVERT_FORMATS[0])
        self.format_combo = ttk.Combobox(
            convert_frame,
            textvariable=self.format_var,
            values=CONVERT_FORMATS,
            width=6,
            state="readonly",
        )
        self.format_combo.pack(side="left", padx=(0, 6))
        ttk.Button(convert_frame, text="Convert", command=self._convert).pack(
            side="left"
        )

        # Log Area (Information requested by user)
        log_frame = ttk.LabelFrame(self.root, text="Process Output")
        log_frame.grid(row=5, column=0, sticky="nsew", pady=(0, 8))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            font=("Menlo", 10),
            state="disabled",
            height=10,
            relief="flat",
            bg="#1e1e1e",
            fg="#cccccc",
            insertbackground="white",
        )
        self.log_area.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # Progress and Status
        self.progress = ttk.Progressbar(
            self.root, orient="horizontal", mode="determinate", maximum=100
        )
        self.progress.grid(row=6, column=0, sticky="ew")
        self.progress["value"] = 0.1

        self.status = ttk.Label(self.root, text="Select documents to begin...")
        self.status.grid(row=7, column=0, sticky="w", pady=(4, 0))

    def _select(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select Documents",
            filetypes=[
                ("Document files", "*.pdf *.epub *.mobi *.txt *.md"),
                ("PDF files", "*.pdf"),
                ("EPUB files", "*.epub"),
                ("MOBI files", "*.mobi"),
                ("Text files", "*.txt"),
                ("Markdown files", "*.md"),
                ("All files", "*.*"),
            ],
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

    def _run_tool(self, tool: str, label: str, extra_args: list[str] | None = None) -> None:
        files = self._get_files()
        if not files:
            messagebox.showwarning("No Files", "Select documents first.")
            return

        self._disable_buttons()
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")

        # Reset progress to a tiny non-zero value to force determinate visual
        self.progress.configure(value=0.1)

        self._log(f"Running {label} on {len(files)} file(s)")

        self._proc_files(files, tool, label, 0, extra_args=extra_args)

    def _proc_files(
        self,
        files: list[Path],
        tool: str,
        label: str,
        idx: int,
        extra_args: list[str] | None = None,
    ) -> None:
        if idx >= len(files):
            self._log(f"Batch {label} complete")
            self.progress.configure(value=100)
            self._enable_buttons()
            self.listbox.delete(0, "end")
            self._update_status()
            messagebox.showinfo(
                "Complete", f"{label} finished on {len(files)} file(s)."
            )
            return

        f = files[idx]
        self.status.configure(text=f"Processing {idx + 1}/{len(files)}: {f.name}...")
        self._log(f"--- Processing {label}: {f.name} ---")

        # Start file progress at the base percentage for this file index
        base_val = (idx / len(files)) * 100
        self.progress["value"] = max(base_val, 0.1)

        def _set_progress(val_within_file: float) -> None:
            # Scale 0-100% within file to its portion of the batch
            # Cap at 98% to avoid jumping to next file prematurely
            p_val = min(val_within_file, 98.0)
            base = (idx / len(files)) * 100
            weight = 100.0 / len(files)
            self.progress["value"] = max(base + (p_val / 100.0) * weight, 0.1)

        def _log_line(line: str) -> None:
            self._log(line)

            # PROGRESS: lines take priority — direct percentage
            if line.startswith("PROGRESS:"):
                try:
                    p = float(line.split(":")[1].strip())
                    _set_progress(p)
                    return
                except (ValueError, IndexError):
                    pass

            # Parse percentage
            m = re.search(r"(\d+)%", line)
            if m:
                try:
                    p = float(m.group(1))
                    if "Loading weights" in line or "Loading models" in line:
                        _set_progress(p * 0.15)
                    else:
                        _set_progress(p)
                except ValueError:
                    pass
            elif "[DOCLING] Starting" in line:
                _set_progress(2.0)
            elif "Processing document" in line:
                _set_progress(20.0)
            elif "[DOCLING] Exporting" in line:
                _set_progress(90.0)
            elif "\u2713" in line and "KB markdown" in line:
                _set_progress(100.0)

        def _run() -> None:
            try:
                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1"

                cmd = [tool, str(f)]
                if extra_args:
                    cmd.extend(extra_args)

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env,
                )

                if process.stdout:
                    buffer = ""
                    while True:
                        char = process.stdout.read(1)
                        if not char:
                            if buffer:
                                line = buffer.strip()
                                if line:
                                    self.root.after(0, lambda ln=line: _log_line(ln))
                            break
                        buffer += char
                        if char in ("\r", "\n"):
                            line = buffer.strip()
                            if line:
                                self.root.after(0, lambda ln=line: _log_line(ln))
                            buffer = ""

                process.wait()
                ok = process.returncode == 0
                err_msg = f"Exit code: {process.returncode}" if not ok else ""
            except Exception as e:
                ok = False
                err_msg = str(e)

            self.root.after(
                0,
                lambda: self._on_file_done(
                    ok, err_msg, f, files, tool, label, idx, extra_args=extra_args
                ),
            )

        threading.Thread(target=_run, daemon=True).start()

    def _on_file_done(
        self,
        ok: bool,
        err_msg: str,
        f: Path,
        files: list[Path],
        tool: str,
        label: str,
        idx: int,
        extra_args: list[str] | None = None,
    ) -> None:
        if not ok:
            self._log(f"ERROR: {label} failed on {f.name}: {err_msg}")
            self._enable_buttons()
            messagebox.showerror("Error", f"Failed on {f.name}")
            self._update_status()
            return

        self._log(f"SUCCESS: {label} completed for {f.name}")
        self._proc_files(
            files, tool, label, idx + 1, extra_args=extra_args
        )

    def _disable_buttons(self) -> None:
        self._set_buttons_state("disabled")

    def _enable_buttons(self) -> None:
        self._set_buttons_state("normal")

    def _set_buttons_state(self, state: str) -> None:
        stack: list[tk.Misc] = list(self.root.winfo_children())
        while stack:
            w = stack.pop()
            if isinstance(w, ttk.Button):
                w.configure(state=state)
            stack.extend(w.winfo_children())

    def _compress(self) -> None:
        self._run_tool("pdfcompress", "Compress")

    def _ocr(self) -> None:
        self._run_tool("pdfocr", "OCR")

    def _to_markdown(self) -> None:
        self._run_tool("pdf2md", "Markdown")

    def _merge(self) -> None:
        files = self._get_files()
        if len(files) < 2:
            messagebox.showwarning("Not Enough Files", "Select 2+ PDFs to merge.")
            return

        output = filedialog.asksaveasfilename(
            title="Save Merged PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="merged.pdf",
        )
        if not output:
            return

        self._disable_buttons()
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")
        self.progress.configure(value=0.1)
        self.status.configure(text=f"Merging {len(files)} files...")
        self._log(f"Running Merge on {len(files)} files -> {output}")

        def _run() -> None:
            try:
                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1"
                cmd = ["pdfconcat", "-o", output] + [str(f) for f in files]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env,
                )
                if process.stdout:
                    for line in process.stdout:
                        stripped = line.strip()
                        if stripped:
                            self.root.after(0, lambda ln=stripped: self._log(ln))
                process.wait()
                ok = process.returncode == 0
                err_msg = f"Exit code: {process.returncode}" if not ok else ""
            except Exception as e:
                ok = False
                err_msg = str(e)

            self.root.after(0, lambda: self._on_merge_done(ok, err_msg, output))

        threading.Thread(target=_run, daemon=True).start()

    def _on_merge_done(self, ok: bool, err_msg: str, output: str) -> None:
        if not ok:
            self._log(f"ERROR: Merge failed: {err_msg}")
            self._enable_buttons()
            self.progress.configure(value=0.1)
            messagebox.showerror("Error", f"Merge failed:\n{err_msg}")
            self._update_status()
            return

        self._log(f"SUCCESS: Merged -> {output}")
        self.progress.configure(value=100)
        self._enable_buttons()
        self.listbox.delete(0, "end")
        self._update_status()
        messagebox.showinfo("Complete", f"Merged PDF saved:\n{output}")

    def _split(self) -> None:
        self._run_tool("pdfsplit", "Split")

    def _convert(self) -> None:
        files = self._get_files()
        if not files:
            messagebox.showwarning("No Files", "Select documents first.")
            return

        fmt = self.format_var.get()
        self._run_tool("ebooktool", f"Convert to {fmt}", ["--to", fmt])

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = DocTools()
    app.run()
