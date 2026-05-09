# Video Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Three CLI tools (mp4audio, mp4subs, videogui) for extracting audio from mp4 and adding subtitles to mp4, plus a tkinter GUI wrapper.

**Architecture:** Each tool is a standalone uv-installable Python package using hatchling. Core logic calls ffmpeg via subprocess. GUI calls CLI tools via subprocess. Mirrors existing pdfcompress/pdfocr/pdfgui pattern exactly.

**Tech Stack:** Python 3.10+, hatchling, ffmpeg (external binary), tkinter (stdlib)

---

## File Structure

```
OfficeTools/
  mp4audio/
    pyproject.toml
    mp4audio/
      __init__.py
      cli.py
      extract.py
  mp4subs/
    pyproject.toml
    mp4subs/
      __init__.py
      cli.py
      subs.py
  videogui/
    pyproject.toml
    videogui/
      __init__.py
      gui.py
```

---

### Task 1: mp4audio — pyproject.toml + __init__.py

**Files:**
- Create: `mp4audio/pyproject.toml`
- Create: `mp4audio/mp4audio/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "mp4audio"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []

[project.scripts]
mp4audio = "mp4audio.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Create __init__.py**

Empty file.

```python
```

- [ ] **Step 3: Verify the package is installable**

Run: `cd mp4audio && uv pip install -e . && which mp4audio`
Expected: mp4audio command found in path

- [ ] **Step 4: Commit**

```bash
git add mp4audio/pyproject.toml mp4audio/mp4audio/__init__.py
git commit -m "feat(mp4audio): scaffold package structure"
```

---

### Task 2: mp4audio — extract.py (core logic)

**Files:**
- Create: `mp4audio/mp4audio/extract.py`

- [ ] **Step 1: Write extract.py**

```python
import shutil
import subprocess
from pathlib import Path


def _check_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found. Install: brew install ffmpeg")


def _format_size(n_bytes: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} GB"


def extract_audio(
    input_path: Path,
    output_path: Path | None = None,
    reencode: bool = False,
    bitrate: int = 128,
) -> Path:
    _check_ffmpeg()

    if output_path is None:
        output_path = input_path.with_suffix(".m4a")

    if reencode:
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-vn",
            "-c:a", "aac",
            "-b:a", f"{bitrate}k",
            "-y",
            str(output_path),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-vn",
            "-c:a", "copy",
            "-y",
            str(output_path),
        ]

    subprocess.run(cmd, check=True, capture_output=True)

    original = input_path.stat().st_size
    result = output_path.stat().st_size
    reduction = (1 - result / original) * 100

    print(
        f"  {output_path.name}: "
        f"{_format_size(original)} -> {_format_size(result)} "
        f"({reduction:.0f}% smaller)"
    )

    return output_path
```

- [ ] **Step 2: Verify import**

Run: `cd mp4audio && uv run python -c "from mp4audio.extract import extract_audio; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add mp4audio/mp4audio/extract.py
git commit -m "feat(mp4audio): add extract_audio core logic"
```

---

### Task 3: mp4audio — cli.py

**Files:**
- Create: `mp4audio/mp4audio/cli.py`

- [ ] **Step 1: Write cli.py**

```python
import argparse
from pathlib import Path

from .extract import extract_audio


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mp4audio",
        description="Extract m4a audio from mp4 files (stream copy by default)",
    )
    parser.add_argument(
        "files", nargs="+", type=Path, help="MP4 file(s) to extract audio from"
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Output path (single file only)"
    )
    parser.add_argument(
        "--reencode",
        action="store_true",
        help="Re-encode audio to AAC instead of stream copy",
    )
    parser.add_argument(
        "--bitrate",
        type=int,
        default=128,
        help="AAC bitrate in kbps (default: 128, only with --reencode)",
    )
    args = parser.parse_args()

    if args.output and len(args.files) > 1:
        parser.error("-o/--output can only be used with a single input file")

    for path in args.files:
        if not path.exists():
            print(f"  Skipping: {path} not found")
            continue
        if path.suffix.lower() != ".mp4":
            print(f"  Skipping: {path} not an MP4")
            continue

        output = args.output if args.output and len(args.files) == 1 else None
        extract_audio(
            path,
            output,
            reencode=args.reencode,
            bitrate=args.bitrate,
        )
```

- [ ] **Step 2: Verify CLI help**

Run: `cd mp4audio && uv run mp4audio --help`
Expected: usage message showing all arguments

- [ ] **Step 3: Commit**

```bash
git add mp4audio/mp4audio/cli.py
git commit -m "feat(mp4audio): add CLI with argparse"
```

---

### Task 4: mp4subs — pyproject.toml + __init__.py

**Files:**
- Create: `mp4subs/pyproject.toml`
- Create: `mp4subs/mp4subs/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "mp4subs"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []

[project.scripts]
mp4subs = "mp4subs.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Create __init__.py**

Empty file.

```python
```

- [ ] **Step 3: Verify the package is installable**

Run: `cd mp4subs && uv pip install -e . && which mp4subs`
Expected: mp4subs command found in path

- [ ] **Step 4: Commit**

```bash
git add mp4subs/pyproject.toml mp4subs/mp4subs/__init__.py
git commit -m "feat(mp4subs): scaffold package structure"
```

---

### Task 5: mp4subs — subs.py (core logic)

**Files:**
- Create: `mp4subs/mp4subs/subs.py`

- [ ] **Step 1: Write subs.py**

```python
import re
import shutil
import subprocess
from pathlib import Path


def _check_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found. Install: brew install ffmpeg")


def _format_size(n_bytes: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} GB"


def _escape_srt_path(path: Path) -> str:
    escaped = str(path)
    escaped = escaped.replace("\\", "\\\\\\\\")
    escaped = escaped.replace(":", "\\\\:")
    escaped = escaped.replace("'", "\\\\'")
    escaped = escaped.replace("[", "\\\\[")
    escaped = escaped.replace("]", "\\\\]")
    return escaped


def add_subtitles(
    video_path: Path,
    subs_path: Path,
    output_path: Path | None = None,
    force: bool = False,
    language: str = "eng",
    crf: int = 23,
) -> Path:
    _check_ffmpeg()

    if output_path is None:
        output_path = video_path.with_stem(f"{video_path.stem}_subtitled")

    if force:
        escaped_srt = _escape_srt_path(subs_path)
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vf", f"subtitles='{escaped_srt}'",
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", "fast",
            "-c:a", "copy",
            "-y",
            str(output_path),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-i", str(subs_path),
            "-c", "copy",
            "-c:s", "mov_text",
            "-metadata:s:s:0", f"language={language}",
            "-y",
            str(output_path),
        ]

    subprocess.run(cmd, check=True, capture_output=True)

    original = video_path.stat().st_size
    result = output_path.stat().st_size
    delta = result - original

    print(
        f"  {output_path.name}: "
        f"{_format_size(original)} -> {_format_size(result)} "
        f"({'+' if delta >= 0 else ''}{(delta / original) * 100:.0f}%)"
    )

    return output_path
```

- [ ] **Step 2: Verify import**

Run: `cd mp4subs && uv run python -c "from mp4subs.subs import add_subtitles; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add mp4subs/mp4subs/subs.py
git commit -m "feat(mp4subs): add add_subtitles core logic"
```

---

### Task 6: mp4subs — cli.py

**Files:**
- Create: `mp4subs/mp4subs/cli.py`

- [ ] **Step 1: Write cli.py**

```python
import argparse
from pathlib import Path

from .subs import add_subtitles


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mp4subs",
        description="Add SRT subtitles to MP4 (soft sub by default, --force to hard-burn)",
    )
    parser.add_argument(
        "video", type=Path, help="MP4 video file"
    )
    parser.add_argument(
        "subs", type=Path, help="SRT subtitle file"
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Output path"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Hard-burn subtitles into video frames",
    )
    parser.add_argument(
        "--language",
        default="eng",
        help="Subtitle track language tag (default: eng)",
    )
    parser.add_argument(
        "--crf",
        type=int,
        default=23,
        help="H.264 CRF value for hard burn (default: 23)",
    )
    args = parser.parse_args()

    if not args.video.exists():
        parser.error(f"Video file not found: {args.video}")
    if not args.subs.exists():
        parser.error(f"Subtitle file not found: {args.subs}")
    if args.video.suffix.lower() != ".mp4":
        parser.error(f"Video must be an MP4 file, got: {args.video.suffix}")
    if args.subs.suffix.lower() != ".srt":
        parser.error(f"Subtitle must be an SRT file, got: {args.subs.suffix}")

    add_subtitles(
        args.video,
        args.subs,
        args.output,
        force=args.force,
        language=args.language,
        crf=args.crf,
    )
```

- [ ] **Step 2: Verify CLI help**

Run: `cd mp4subs && uv run mp4subs --help`
Expected: usage message showing all arguments

- [ ] **Step 3: Commit**

```bash
git add mp4subs/mp4subs/cli.py
git commit -m "feat(mp4subs): add CLI with argparse"
```

---

### Task 7: videogui — pyproject.toml + __init__.py

**Files:**
- Create: `videogui/pyproject.toml`
- Create: `videogui/videogui/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "videogui"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []

[project.scripts]
videogui = "videogui.gui:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Create __init__.py**

Empty file.

```python
```

- [ ] **Step 3: Verify the package is installable**

Run: `cd videogui && uv pip install -e . && which videogui`
Expected: videogui command found in path

- [ ] **Step 4: Commit**

```bash
git add videogui/pyproject.toml videogui/videogui/__init__.py
git commit -m "feat(videogui): scaffold package structure"
```

---

### Task 8: videogui — gui.py

**Files:**
- Create: `videogui/videogui/gui.py`

- [ ] **Step 1: Write gui.py**

```python
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
```

- [ ] **Step 2: Verify import**

Run: `cd videogui && uv run python -c "from videogui.gui import VideoTools; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add videogui/videogui/gui.py
git commit -m "feat(videogui): add tkinter GUI for mp4audio + mp4subs"
```

---

### Task 9: Install all three tools and smoke test

**Files:** None (verification only)

- [ ] **Step 1: Install all packages**

Run: `uv pip install -e ./mp4audio -e ./mp4subs -e ./videogui`

- [ ] **Step 2: Verify all CLI entry points**

Run: `mp4audio --help && mp4subs --help && videogui --help`
Expected: all three show usage messages

- [ ] **Step 3: Test mp4audio with a real mp4 file (if available)**

Run: `mp4audio /path/to/test.mp4`
Expected: extracts m4a, prints size reduction

- [ ] **Step 4: Test mp4subs soft sub (if test files available)**

Run: `mp4subs /path/to/test.mp4 /path/to/test.srt`
Expected: creates test_subtitled.mp4, subtitles selectable in VLC

- [ ] **Step 5: Test mp4subs hard burn (if test files available)**

Run: `mp4subs /path/to/test.mp4 /path/to/test.srt --force`
Expected: creates test_subtitled.mp4 with burned-in subtitles

- [ ] **Step 6: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: address smoke test findings"
```
