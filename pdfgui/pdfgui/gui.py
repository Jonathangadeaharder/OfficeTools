import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


class PDFTools:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("PDF Tools")
        self.root.geometry("480x320")
        self.root.resizable(True, True)
        self.root.configure(padx=12, pady=12)

        style = ttk.Style()
        style.theme_use("aqua")

        self._build_ui()

    def _build_ui(self) -> None:
        ttk.Button(
            self.root, text="Select PDFs...", command=self._select
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
            btn_frame, text="Compress", command=self._compress
        ).pack(side="left", padx=4)
        ttk.Button(
            btn_frame, text="OCR", command=self._ocr
        ).pack(side="left", padx=4)

        self.status = ttk.Label(self.root, text="Select PDFs to begin...")
        self.status.pack(pady=(4, 0))

    def _select(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select PDFs",
            filetypes=[("PDF files", "*.pdf")],
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

    def _run_tool(self, tool: str) -> None:
        files = self._get_files()
        if not files:
            messagebox.showwarning("No Files", "Select PDFs first.")
            return

        self.status.configure(text=f"Running {tool} on {len(files)} file(s)...")
        self.root.update()

        for f in files:
            try:
                subprocess.run(
                    [tool, str(f)],
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

        messagebox.showinfo("Complete", f"{tool} finished on {len(files)} file(s).")
        self.listbox.delete(0, "end")
        self._update_status()

    def _compress(self) -> None:
        self._run_tool("pdfcompress")

    def _ocr(self) -> None:
        self._run_tool("pdfocr")

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = PDFTools()
    app.run()
