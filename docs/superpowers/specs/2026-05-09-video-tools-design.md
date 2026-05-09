# Video Tools Design Spec

Three Python CLI tools + tkinter GUI for video file operations. Mirrors existing pdfcompress/pdfocr/pdfgui pattern in this repo.

## Projects

### 1. mp4audio — Extract m4a from mp4

**Package:** `mp4audio/` with `pyproject.toml` (hatchling, no Python deps)

**Entry point:** `mp4audio = "mp4audio.cli:main"`

**CLI:**
```
mp4audio <file1.mp4> [file2.mp4 ...] [-o output.m4a] [--reencode] [--bitrate 128]
```

**Arguments:**
- `files` — one or more mp4 files (positional, required)
- `-o / --output` — output path (single file only)
- `--reencode` — re-encode audio to AAC instead of stream copy
- `--bitrate` — AAC bitrate in kbps (default: 128, only with --reencode)

**Core logic (`mp4audio/extract.py`):**
- `_check_ffmpeg()` — verify ffmpeg available via `shutil.which`, else `SystemExit` with install instructions
- Default (stream copy): `ffmpeg -i input.mp4 -vn -c:a copy output.m4a`
  - Zero re-encoding, instant, zero quality loss
  - File size matches audio track already in mp4
- `--reencode`: `ffmpeg -i input.mp4 -vn -c:a aac -b:a {bitrate}k output.m4a`
  - Re-encodes to AAC at specified bitrate
  - Slower but guarantees smaller file size
- Output defaults to `{stem}.m4a`
- Size reporting: `{original} -> {result} ({pct}% smaller)`

**File structure:**
```
mp4audio/
  pyproject.toml
  mp4audio/
    __init__.py
    cli.py
    extract.py
```

**File validation in CLI loop:** skip missing files, skip non-mp4 files (with message).

---

### 2. mp4subs — Add subtitles to mp4

**Package:** `mp4subs/` with `pyproject.toml` (hatchling, no Python deps)

**Entry point:** `mp4subs = "mp4subs.cli:main"`

**CLI:**
```
mp4subs <video.mp4> <subs.srt> [-o output.mp4] [--force] [--language eng] [--crf 23]
```

**Arguments:**
- `video` — mp4 file (positional, required)
- `subs` — srt file (positional, required)
- `-o / --output` — output path
- `--force` — hard-burn subtitles into video frames (default: soft sub)
- `--language` — subtitle track language tag, e.g. eng, deu (default: eng)
- `--crf` — H.264 CRF value for hard burn (default: 23, only with --force)

**Core logic (`mp4subs/subs.py`):**
- `_check_ffmpeg()` — same pattern as mp4audio
- **Soft sub (default):**
  `ffmpeg -i input.mp4 -i subs.srt -c copy -c:s mov_text -metadata:s:s:0 language={lang} output.mp4`
  - Stream copies video + audio (instant, no quality loss)
  - Muxes SRT as MOV text subtitle track (selectable in VLC)
  - Sets language metadata on subtitle track
- **Hard burn (`--force`):**
  `ffmpeg -i input.mp4 -vf "subtitles='{escaped_srt_path}'" -c:v libx264 -crf {crf} -preset fast -c:a copy output.mp4`
  - Renders subtitles onto video frames
  - Re-encodes video with H.264 at specified CRF
  - `-preset fast` for reasonable speed/quality tradeoff
  - Audio stream copied (no loss)
  - SRT path must be escaped for ffmpeg subtitle filter (colons, backslashes, brackets)
- Output defaults to `{stem}_subtitled.mp4`

**File structure:**
```
mp4subs/
  pyproject.toml
  mp4subs/
    __init__.py
    cli.py
    subs.py
```

**File validation:** check both input files exist, check mp4 suffix, check srt suffix.

---

### 3. videogui — tkinter GUI for video tools

**Package:** `videogui/` with `pyproject.toml` (hatchling, no Python deps)

**Entry point:** `videogui = "videogui.gui:main"`

**UI elements:**
- "Select Files..." button — file dialog accepting `.mp4` and `.srt`
- Listbox showing selected files with scrollbar
- "Remove Selected" button
- "Extract Audio" button — runs `mp4audio` on all mp4 files in list
- "Add Subtitles" button — requires exactly 1 mp4 + 1 srt in list, runs `mp4subs`
- Status label at bottom

**Behavior:**
- Calls tools via `subprocess.run([tool, ...args], check=True, capture_output=True, text=True)`
- Error handling: show messagebox on failure
- Success: show info messagebox, clear list
- macOS aqua theme
- Window title: "Video Tools"
- Geometry: 480x320

**File structure:**
```
videogui/
  pyproject.toml
  videogui/
    __init__.py
    gui.py
```

---

## Conventions (matching existing PDF projects)

- **Build system:** hatchling
- **Python:** >=3.10
- **No Python dependencies** — all three tools only need ffmpeg as external binary
- **CLI pattern:** argparse with `main()` function, file validation loop, error messages to stdout
- **External deps:** checked via `shutil.which` with install instructions on failure
- **Output naming:** `{stem}.m4a` / `{stem}_subtitled.mp4` when no `-o` given
- **Size reporting:** shared `_format_size()` helper (bytes -> KB/MB/GB)
- **GUI pattern:** tkinter + ttk, aqua theme, subprocess tool calls

## External dependency

All three tools require **ffmpeg** installed. Install: `brew install ffmpeg`

## Error handling

- ffmpeg not found: `SystemExit("ffmpeg not found. Install: brew install ffmpeg")`
- Input file missing: skip with message
- Wrong file extension: skip with message
- ffmpeg command fails: raise `subprocess.CalledProcessError` (GUI catches and shows messagebox)
