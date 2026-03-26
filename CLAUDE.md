# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OT Tables Compare is a two-part tool for inspecting and patching OpenType font metadata:

1. **`index.html`** — A self-contained single-page web app (no build step) that loads OTF/TTF/WOFF/WOFF2 files via drag-and-drop, displays a side-by-side comparison of `head`, `name`, and `OS/2` table fields, highlights differences, allows inline editing, and exports a `.changes.json` patch file. Uses [opentype.js](https://opentype.js.org/) loaded from CDN.

2. **`apply_changes.py`** — A Python CLI script that reads the `.changes.json` and applies the edits to font binaries using fontTools. Outputs modified copies (`<name>.modified.<ext>`), leaving originals untouched.

## Commands

```bash
# Install Python dependencies (fonttools)
uv sync

# Apply exported changes to fonts
uv run python apply_changes.py /path/to/folder-with-fonts-and-json
```

The HTML app requires no server — open `index.html` directly in a browser.

## Architecture

The workflow is: **browser (compare & edit) → JSON patch → Python (apply to binaries)**.

- `index.html` is entirely self-contained: all CSS is inline (`<style>` blocks), all JS is in a single `<script>` block. State lives in two globals: `fonts[]` (parsed font data) and `pendingChanges` (Map of edits keyed by `"fileName|table|field"`).
- `apply_changes.py` groups changes by font file, dispatches to table-specific appliers (`apply_name_change`, `apply_os2_change`, `apply_head_change`), and handles value parsing (strips human-readable annotations like `"400 (Regular)"` down to raw integers).
- Both sides share the same field naming conventions for OS/2 and head tables (fontTools attribute names). Name table fields are referenced by numeric ID (0–25).

## Python

- Python 3.12, managed via `uv`
- Single dependency: `fonttools`
