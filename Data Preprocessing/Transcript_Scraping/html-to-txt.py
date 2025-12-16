#!/usr/bin/env python3
"""
Convert local HTML files to plain text files.

Features:
- Recursively traverse an input directory and process .html/.htm files
- Extract readable text; uses BeautifulSoup if available, otherwise a robust fallback
- Strip <script>/<style> by default
- Preserve directory structure in the output directory
- Best-effort encoding handling with optional chardet if installed

Usage:
  python data_collection/html-to-txt.py \
      --input /path/to/html_dir \
      --output /path/to/output_txt_dir \
      [--overwrite]

Optionally install:
  pip install beautifulsoup4 chardet
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Tuple
import re
import html as html_std


def try_import_bs4():
    try:
        from bs4 import BeautifulSoup  # type: ignore
        return BeautifulSoup
    except Exception:
        return None


def try_detect_encoding(file_path: Path) -> str:
    """Best-effort encoding detection.

    Tries utf-8 first, falls back to chardet if available, else latin-1.
    """
    # Fast path: UTF-8
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            f.read()
        return "utf-8"
    except Exception:
        pass

    # Optional: chardet
    try:
        import chardet  # type: ignore

        with open(file_path, "rb") as f:
            raw = f.read()
        result = chardet.detect(raw)
        enc = result.get("encoding") or "latin-1"
        return enc
    except Exception:
        # Fallback
        return "latin-1"


def extract_text_with_bs4(html_text: str) -> str:
    BeautifulSoup = try_import_bs4()
    if not BeautifulSoup:
        raise RuntimeError("BeautifulSoup not available")

    soup = BeautifulSoup(html_text, "html.parser")

    # Remove script/style
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Get text with reasonable block separation
    text = soup.get_text("\n")

    # Normalize excessive blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


class _TextExtractorFallback:
    """Basic HTML text extractor without external deps.

    - Removes script/style blocks
    - Strips tags
    - Unescapes HTML entities
    - Collapses excessive blank lines
    """

    _SCRIPT_STYLE_RE = re.compile(
        r"<(script|style|noscript)(.|\n)*?</\1>", re.IGNORECASE
    )
    _TAG_RE = re.compile(r"<[^>]+>")
    _WHITESPACE_RE = re.compile(r"[\t\r\f\v]+")

    def extract(self, html_text: str) -> str:
        text = self._SCRIPT_STYLE_RE.sub("\n", html_text)
        text = self._TAG_RE.sub("\n", text)
        text = html_std.unescape(text)
        text = self._WHITESPACE_RE.sub(" ", text)
        # Normalize newlines and collapse multiples
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        # Trim lines
        lines = [ln.strip() for ln in text.split("\n")]
        # Drop empty runs while preserving paragraph breaks
        cleaned: list[str] = []
        for ln in lines:
            if ln:
                cleaned.append(ln)
            elif cleaned and cleaned[-1] != "":
                cleaned.append("")
        return "\n".join(cleaned).strip()


def extract_text_from_html(html_text: str) -> str:
    try:
        return extract_text_with_bs4(html_text)
    except Exception:
        return _TextExtractorFallback().extract(html_text)


def convert_file(html_path: Path, src_root: Path, dst_root: Path, overwrite: bool) -> Tuple[Optional[Path], Optional[str]]:
    """Convert a single HTML file to .txt preserving relative structure.

    Returns: (output_path or None, error_message or None)
    """
    try:
        rel_path = html_path.relative_to(src_root)
    except ValueError:
        # If not under src_root, flatten
        rel_path = html_path.name

    rel_path = Path(rel_path)
    out_rel = rel_path.with_suffix(".txt")
    out_path = dst_root / out_rel
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and not overwrite:
        return out_path, None

    encoding = try_detect_encoding(html_path)
    try:
        with open(html_path, "r", encoding=encoding, errors="ignore") as f:
            html_text = f.read()
    except Exception as e:
        return None, f"Failed to read {html_path}: {e}"

    try:
        text = extract_text_from_html(html_text)
    except Exception as e:
        return None, f"Failed to parse {html_path}: {e}"

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception as e:
        return None, f"Failed to write {out_path}: {e}"

    return out_path, None


def iter_html_files(root: Path):
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if name.lower().endswith((".html", ".htm")):
                yield Path(dirpath) / name


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert local HTML files to plain text.")
    p.add_argument("--input", required=True, help="Input directory containing HTML files")
    p.add_argument("--output", required=True, help="Output directory for .txt files")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing .txt files")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    src_root = Path(args.input).expanduser().resolve()
    dst_root = Path(args.output).expanduser().resolve()

    if not src_root.exists() or not src_root.is_dir():
        print(f"[error] Input directory not found or not a directory: {src_root}", file=sys.stderr)
        return 2

    dst_root.mkdir(parents=True, exist_ok=True)

    total = 0
    converted = 0
    skipped = 0
    failures = 0

    for html_path in iter_html_files(src_root):
        total += 1
        out_path, err = convert_file(html_path, src_root, dst_root, overwrite=args.overwrite)
        if err:
            failures += 1
            print(f"[fail] {html_path}: {err}", file=sys.stderr)
        elif out_path and out_path.exists():
            if args.overwrite or out_path.stat().st_size == 0:
                converted += 1
            else:
                # If not overwriting and file existed, count as skipped
                skipped += 1
        else:
            skipped += 1

    print(
        f"Processed: {total} | Converted: {converted} | Skipped: {skipped} | Failures: {failures}"
    )
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())


