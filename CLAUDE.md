# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OT Tables Compare is a two-part tool for inspecting and patching OpenType font metadata:

1. **`index.html`** — A self-contained single-page web app (no build step) that loads OTF/TTF files via drag-and-drop, displays a side-by-side comparison of `head`, `name` and `OS/2` fields (plus read-only `STAT` and `avar`, the latter labelled with `fvar` axis tags), highlights differences, allows inline editing, can mark whole tables for deletion, and either exports a `.changes.json` patch file or rebuilds the font binaries in-browser and downloads them as a ZIP. Uses [opentype.js](https://opentype.js.org/) loaded from CDN. This file was previously called `ot-edit.html`; the earlier drafts it superseded (the original compare-only `index.html`, plus `editor.html` and `index2.html`) were removed.

2. **`apply_changes.py`** — A Python CLI script that reads the `.changes.json` and applies the edits to font binaries using fontTools. Outputs modified copies (`<name>.modified.<ext>`), leaving originals untouched.

## Commands

```bash
# Install Python dependencies (fonttools)
uv sync

# Apply exported changes to fonts
uv run python apply_changes.py /path/to/folder-with-fonts-and-json

# Publish the editor (see Deployment below)
./deploy.sh
```

The HTML app requires no server — open `index.html` directly in a browser.

## Architecture

The workflow is: **browser (compare & edit) → JSON patch → Python (apply to binaries)**, or entirely in-browser via the binary serializer + ZIP download.

- `index.html` is entirely self-contained: all CSS is inline (`<style>` blocks), all JS is in a single `<script>` block. State lives in globals: `fonts[]` (parsed font data), `pendingChanges` (Map of edits keyed by `"fileName|table|field"`) and `deletedTables`.
- Values are read twice: opentype.js provides the convenient object model, while `parseBinaryFont()` keeps the raw table bytes used for rebuilding. Where opentype.js is lossy the binary reader wins — e.g. `head.created`/`modified`, which opentype.js exposes as Unix *seconds* truncated to the low 32 bits of LONGDATETIME, are re-read as `Date` via `readLONGDATETIME()`.
- `apply_changes.py` groups changes by font file, dispatches to table-specific appliers (`apply_name_change`, `apply_os2_change`, `apply_head_change`), and handles value parsing (strips human-readable annotations like `"400 (Regular)"` down to raw integers).
- Both sides share the same field naming conventions for OS/2 and head tables (fontTools attribute names). Name table fields are referenced by numeric ID (0–25).

## Deployment

`./deploy.sh` copies `index.html` to `$DEPLOY_DEST/index.html`, then commits and pushes in the destination repo. `DEPLOY_DEST` lives in `deploy.config` (git-ignored; copy from `deploy.config.example`). Currently published at <https://typedev.github.io/ot-edit/>.

## Python

- Python 3.12, managed via `uv`
- Single dependency: `fonttools`
