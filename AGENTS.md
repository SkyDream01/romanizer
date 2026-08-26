# AGENTS.md

## Overview

Batch file renamer that converts Chinese/Japanese filenames to Roman alphabet (Pinyin for Chinese, Hepburn for Japanese). Also supports audio metadata romanization. Two entry points: CLI and PySide6 GUI.

## Structure

- `romanizer.py` — core library + CLI entry point. Exports the `Romanizer` class, `load_dict`, constants. Must remain importable by the GUI.
- `meta_romanizer.py` — audio metadata romanization module. Exports `MetaRomanizer`, `AUDIO_EXTENSIONS`. Delegates text conversion to `Romanizer._convert_segment()`.
- `RomanizerGUI.py` — PySide6 desktop app. Imports from `romanizer.py` and optionally `meta_romanizer.py`; will not launch without a display or without `PySide6`.
- No tests, no CI, no build system.

## Setup

```bash
pip install pypinyin pykakasi PySide6>=6.5.0 mutagen>=1.47.0
```

Python 3.10+ required (uses `pathlib.Path.with_stem`).

## Running

```bash
# CLI — rename only (original behavior)
python romanizer.py <path> [-l jp|cn] [-s camel|lower|upper] [--sep _] [-d dict.json] [-r] [--dry-run]

# CLI — rename + romanize audio metadata
python romanizer.py <path> --meta [--dry-run]

# CLI — romanize audio metadata only (no rename)
python romanizer.py <path> --meta-only [--dry-run] [--no-backup]

# GUI
python RomanizerGUI.py
```

CLI requires a positional `path` argument — it will error without one.

## Key conventions

- GUI strings are hard-coded in Chinese (Simplified). If adding or modifying UI text, keep it in Chinese to match existing patterns.
- The `Romanizer` class is the single source of truth for rename logic — both CLI and GUI delegate to it. Do not duplicate rename logic in the GUI.
- `process_items()` is a generator yielding `(src, dst, status)`. Status is one of: `success`, `skip`, `error`.
- Conflict resolution appends `-1`, `-2`, etc. to stems when a destination path already exists on disk or in the current batch.
- The JSON dictionary uses long-word-first matching (keys sorted by length descending, compiled into a single regex).
- `test/` is gitignored. Test files, if any, should live there.

## Audio Metadata Romanization

- `meta_romanizer.py` handles audio metadata (MP3/FLAC/OGG/M4A/etc.) via the `mutagen` library.
- `MetaRomanizer` delegates all text romanization to `Romanizer._convert_segment()` — do not reimplement CJK conversion.
- `mutagen` is an optional dependency. The rename feature works without it. CLI `--meta`/`--meta-only` and GUI metadata buttons are disabled if mutagen is not installed.
- Metadata modifications always create a `.bak` backup by default (can be overridden with `--no-backup`).
- GUI metadata strings remain in Chinese (Simplified) to match existing patterns.

## Gotchas

- `romanizer.py` exits with `sys.exit(1)` if `pypinyin`/`pykakasi` are missing — the import check is at module level, before any class definition.
- `meta_romanizer.py` raises `ImportError` if `mutagen` is missing — the import check is at module level. The GUI and CLI guard this with try/except.
- The GUI's `closeEvent` will prompt the user if a worker thread is running. Don't remove that safety check.
- `RomanizerGUI.py` uses `from romanizer import Romanizer, load_dict, ILLEGAL_CHARS_RE`, so both files must be in the same directory or on `sys.path`.
- `MetaRomanizer.process_items()` yields `(filepath, changes_dict, status)` — different from `Romanizer.process_items()` which yields `(src, dst, status)`.
