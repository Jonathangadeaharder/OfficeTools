import re
import subprocess
import sys
import tempfile
from pathlib import Path

import ebooklib
import markdown
from ebooklib import epub
from fpdf import FPDF

INPUT_FORMATS = {".epub", ".mobi"}


def convert(input_path: Path, output_path: Path) -> None:
    in_ext = input_path.suffix.lower()
    out_ext = output_path.suffix.lower()

    if in_ext not in INPUT_FORMATS and out_ext not in (".epub", ".mobi"):
        print(f"  Unsupported input format: {in_ext}")
        return

    print(f"  Converting {input_path.name} -> {output_path.name}", flush=True)

    if in_ext == ".epub":
        _from_epub(input_path, output_path, out_ext)
    elif in_ext == ".mobi":
        _from_mobi(input_path, output_path, out_ext)
    elif out_ext == ".epub":
        _to_epub(input_path, output_path)
    elif out_ext == ".mobi":
        _to_mobi(input_path, output_path)
    else:
        print(f"  Unsupported conversion: {in_ext} -> {out_ext}")


# ---------------------------------------------------------------------------
# EPUB -> *
# ---------------------------------------------------------------------------


def _from_epub(input_path: Path, output_path: Path, out_ext: str) -> None:
    book = epub.read_epub(str(input_path))

    if out_ext == ".md":
        _epub_to_md(book, output_path)
    elif out_ext == ".txt":
        _epub_to_txt(book, output_path)
    elif out_ext == ".pdf":
        _epub_to_pdf(book, output_path)


def _epub_to_md(book, output_path: Path) -> None:
    lines: list[str] = []
    title = book.get_metadata("DC", "title")
    if title:
        lines.append(f"# {title[0][0]}\n")

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content = item.get_content().decode("utf-8", errors="replace")
            text = _html_to_text(content)
            name = item.get_name()
            chapter_title = _guess_chapter_title(name, content)
            if chapter_title and chapter_title.lower() not in (
                t.lower() for t in text.split("\n")[:3]
            ):
                lines.append(f"\n## {chapter_title}\n")
            lines.append(text)

    output_path.write_text("\n\n".join(lines), encoding="utf-8")
    kb = output_path.stat().st_size / 1024
    print(f"  \u2713 {output_path.name} ({kb:.1f} KB)", flush=True)


def _epub_to_txt(book, output_path: Path) -> None:
    lines: list[str] = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content = item.get_content().decode("utf-8", errors="replace")
            lines.append(_html_to_text(content))

    output_path.write_text("\n\n".join(lines), encoding="utf-8")
    kb = output_path.stat().st_size / 1024
    print(f"  \u2713 {output_path.name} ({kb:.1f} KB)", flush=True)


def _epub_to_pdf(book, output_path: Path) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=11)

    title = book.get_metadata("DC", "title")
    if title:
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, title[0][0], new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)
        pdf.set_font("Helvetica", size=11)

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content = item.get_content().decode("utf-8", errors="replace")
            text = _html_to_text(content)
            name = item.get_name()
            chapter = _guess_chapter_title(name, content)
            if chapter:
                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 10, chapter, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                pdf.set_font("Helvetica", size=11)
            for paragraph in text.split("\n"):
                paragraph = paragraph.strip()
                if not paragraph:
                    continue
                pdf.multi_cell(0, 5.5, paragraph)
                pdf.ln(1)

    pdf.output(str(output_path))
    kb = output_path.stat().st_size / 1024
    print(f"  \u2713 {output_path.name} ({kb:.1f} KB)", flush=True)


# ---------------------------------------------------------------------------
# MOBI -> *
# ---------------------------------------------------------------------------


def _from_mobi(input_path: Path, output_path: Path, out_ext: str) -> None:
    text = _mobi_to_text(input_path)
    if text is None:
        print(f"  Failed to extract text from {input_path.name}", file=sys.stderr)
        return

    if out_ext == ".md":
        output_path.write_text(text, encoding="utf-8")
    elif out_ext == ".txt":
        output_path.write_text(_strip_markdown(text), encoding="utf-8")
    elif out_ext == ".pdf":
        _text_to_pdf(text, output_path)

    kb = output_path.stat().st_size / 1024
    print(f"  \u2713 {output_path.name} ({kb:.1f} KB)", flush=True)


def _mobi_to_text(input_path: Path) -> str | None:
    try:
        import mobi  # type: ignore[reportMissingImports]

        with tempfile.TemporaryDirectory() as tmp:
            tempdir, filepath = mobi.extract(str(input_path), tmpdir=tmp)
            if filepath:
                content = Path(filepath).read_text(encoding="utf-8", errors="replace")
                return _html_to_text(content)
    except ImportError:
        pass
    except Exception as e:
        print(f"  mobi package failed: {e}", file=sys.stderr)

    return _mobi_to_text_calibre(input_path)


def _mobi_to_text_calibre(input_path: Path) -> str | None:
    try:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "output.txt"
            subprocess.run(
                ["ebook-convert", str(input_path), str(out)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if out.exists():
                return out.read_text(encoding="utf-8", errors="replace")
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"  calibre not available: {e}", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# * -> EPUB
# ---------------------------------------------------------------------------


def _to_epub(input_path: Path, output_path: Path) -> None:
    book = epub.EpubBook()
    book.set_identifier(str(output_path.stem))
    book.set_title(output_path.stem)
    book.set_language("en")

    in_ext = input_path.suffix.lower()
    if in_ext == ".md":
        text = input_path.read_text(encoding="utf-8")
        chapters = _split_markdown_chapters(text)
        for i, (title, body) in enumerate(chapters):
            c = epub.EpubHtml(title=title, file_name=f"chap_{i}.xhtml", lang="en")
            c.content = (
                f"<h1>{title}</h1>\n{_md_to_html(body)}" if title else _md_to_html(body)
            )
            book.add_item(c)
            book.toc.append(c)
            book.spine.append(c)
    elif in_ext == ".txt":
        text = input_path.read_text(encoding="utf-8")
        c = epub.EpubHtml(title=output_path.stem, file_name="content.xhtml", lang="en")
        c.content = f"<pre>{text}</pre>"
        book.add_item(c)
        book.toc.append(c)
        book.spine.append(c)
    elif in_ext == ".pdf":
        _pdf_to_epub(input_path, output_path)
        return

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    epub.write_epub(str(output_path), book)
    kb = output_path.stat().st_size / 1024
    print(f"  \u2713 {output_path.name} ({kb:.1f} KB)", flush=True)


def _pdf_to_epub(input_path: Path, output_path: Path) -> None:
    md_path = output_path.with_suffix(".md.tmp")
    try:
        subprocess.run(
            ["pdf2md", str(input_path), "-o", str(md_path)],
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )
        if md_path.exists():
            _to_epub(md_path, output_path)
    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
    ) as e:
        print(f"  pdf2md failed: {e}", file=sys.stderr)
    finally:
        md_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# * -> MOBI
# ---------------------------------------------------------------------------


def _to_mobi(input_path: Path, output_path: Path) -> None:
    try:
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = Path(tmp) / f"{output_path.stem}_intermediate.epub"
            convert(input_path, epub_path)
            if epub_path.exists():
                subprocess.run(
                    ["ebook-convert", str(epub_path), str(output_path)],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if output_path.exists():
                    kb = output_path.stat().st_size / 1024
                    print(f"  \u2713 {output_path.name} ({kb:.1f} KB)", flush=True)
                    return
        print("  mobi output requires calibre (ebook-convert)", file=sys.stderr)
    except FileNotFoundError:
        print(
            "  mobi output requires calibre: install with `brew install calibre`",
            file=sys.stderr,
        )
    except subprocess.TimeoutExpired:
        print("  calibre timed out", file=sys.stderr)


# ---------------------------------------------------------------------------
# * -> TXT / PDF
# ---------------------------------------------------------------------------


def _text_to_pdf(text: str, output_path: Path) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=11)
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            pdf.ln(3)
            continue
        pdf.multi_cell(0, 5.5, line)
    pdf.output(str(output_path))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _html_to_text(html: str) -> str:
    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"</p>", "\n\n", text)
    text = re.sub(r"</h\d>", "\n", text)
    text = re.sub(r"</li>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&nbsp;", " ", text)
    return text.strip()


def _md_to_html(md: str) -> str:
    return markdown.markdown(md, extensions=["extra"])


def _guess_chapter_title(name: str, content: str) -> str | None:
    m = re.search(r"<h[1-6][^>]*>(.*?)</h[1-6]>", content, re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    stem = Path(name).stem
    if stem and stem != "content":
        return stem.replace("_", " ").replace("-", " ").title()
    return None


def _split_markdown_chapters(text: str) -> list[tuple[str, str]]:
    chapters: list[tuple[str, str]] = []
    lines = text.split("\n")
    current_title = ""
    current_body: list[str] = []

    for line in lines:
        m = re.match(r"^(#{1,3})\s+(.+)$", line)
        if m:
            if current_body or current_title:
                chapters.append((current_title, "\n".join(current_body).strip()))
            current_title = m.group(2)
            current_body = []
        else:
            current_body.append(line)

    if current_body or current_title:
        chapters.append((current_title, "\n".join(current_body).strip()))

    if not chapters:
        chapters = [("", text)]
    return chapters


def _strip_markdown(text: str) -> str:
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_]{1,3}", "", text)
    text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip()
