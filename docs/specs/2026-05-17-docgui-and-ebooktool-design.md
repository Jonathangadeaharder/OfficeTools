# docgui & ebooktool — Doc Tools Expansion

## Summary

Rename `pdfgui` to `docgui` (GUI now handles PDF + ebook workflows). Add `ebooktool` CLI for bidirectional conversion between ebook formats (epub, mobi) and plain text formats (md, txt, pdf).

## Key Decisions

| Decision | Choice |
|----------|--------|
| Package rename | pdfgui → docgui |
| App name | PDF Tools → Doc Tools |
| New tool name | ebooktool |
| Ebook library | ebooklib for epub read/write |
| PDF output | fpdf2 |
| Mobi read | mobi package (PyPI), fallback to calibre |
| Mobi write | calibre `ebook-convert` subprocess (required) |
| Input formats | epub, mobi |
| Output formats | md, txt, pdf, epub, mobi |

## Directory Changes

```
OfficeTools/
├── docgui/              # renamed from pdfgui
│   ├── pyproject.toml
│   └── docgui/
│       ├── launch.py
│       └── gui.py       # PDF Tools → Doc Tools; file picker now accepts PDF + all
├── ebooktool/           # new
│   ├── pyproject.toml
│   └── ebooktool/
│       ├── cli.py       # argparse CLI
│       └── convert.py   # core conversion logic
```

## CLI Interface

```
ebooktool input.epub                 → input.md (auto-detect)
ebooktool input.epub -o output.txt
ebooktool input.mobi --to pdf
ebooktool input.md -o output.epub
ebooktool input.txt --to mobi        # requires calibre
```

## Conversion Matrix

| Input | → md | → txt | → pdf | → epub | → mobi |
|-------|------|-------|-------|--------|--------|
| epub  | Y    | Y     | Y     | —      | calibre |
| mobi  | Y    | Y     | Y     | calibre| —      |
| md    | —    | —     | —     | Y      | calibre |
| txt   | —    | —     | —     | Y      | calibre |
| pdf   | —    | —     | —     | pdf2md | calibre |

## Dependencies

- **ebooktool runtime:** ebooklib, markdown, fpdf2
- **ebooktool optional:** mobi (for mobi read), calibre (for mobi write)
- **docgui:** no dep changes (tkinter stdlib)
