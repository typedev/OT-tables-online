# OT Tables Compare & Patch

A browser-based tool for comparing and editing OpenType metadata tables across
several fonts side by side, plus a Python CLI for applying the same edits to
font binaries.

**Live:** [typedev.github.io/ot-edit](https://typedev.github.io/ot-edit/)

## Features

- Drag & drop any number of OTF/TTF files; every font gets its own column and
  differing values are highlighted
- Editable side-by-side view of the `head`, `name` and `OS/2` tables, with
  human-readable annotations (weight/width names, decoded bitfields such as
  `fsSelection`, `macStyle` and `head.flags`, PANOSE digits, hex ranges)
- Add missing `name` IDs, and delete existing records by clearing them
- Editing `head.fontRevision` auto-propagates to name ID 5 (Version String)
  and name ID 3 (Unique ID)
- Read-only comparison of `STAT` (design axes and axis values) and `avar`
  (segment maps, labelled with `fvar` axis tags)
- Full table directory with `Del` checkboxes to drop whole tables from the
  rebuilt font
- Two ways out: **Download Modified Fonts** rebuilds the binaries in the
  browser and packs them into a ZIP, or **Export JSON** writes a
  `.changes.json` patch to apply later with `apply_changes.py`

Rebuilt fonts keep all untouched tables byte-for-byte; the table directory is
rewritten with recalculated checksums and a fresh `head.checksumAdjustment`.
Originals are never modified.

## Usage

### Editor

No build step and no server — open `index.html` in a browser, or use the
[hosted version](https://typedev.github.io/ot-edit/). `opentype.js` and
`JSZip` are loaded from a CDN, so the first load needs a network connection.

### Applying an exported patch

```bash
# Install dependencies (fonttools)
uv sync

# Apply every *.changes.json in a folder to the fonts sitting next to it
uv run python apply_changes.py /path/to/folder-with-fonts-and-json
```

Modified copies are written as `<original_name>.modified.<ext>`, leaving the
originals untouched.

## Deployment

`./deploy.sh` copies `index.html` into `$DEPLOY_DEST/index.html`, then commits
and pushes in the destination repository. The target lives in `deploy.config`
(git-ignored):

```bash
cp deploy.config.example deploy.config
$EDITOR deploy.config          # set DEPLOY_DEST
./deploy.sh
```

## Notes

- The editor loads `.otf` and `.ttf`; WOFF/WOFF2 are not accepted.
- `head` fields that must stay consistent (`majorVersion`, `minorVersion`,
  `checksumAdjustment`, `magicNumber`) are shown but not editable.
- Timestamps are read straight from the binary `head` table, because
  opentype.js exposes `created`/`modified` as Unix seconds truncated to the
  low 32 bits of LONGDATETIME.
