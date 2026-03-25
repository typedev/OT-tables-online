#!/usr/bin/env python3
"""
OT Tables Apply — applies name/OS2/head changes from a JSON patch file to font files.

Usage:
    python apply_changes.py /path/to/working/folder

The folder must contain:
  - A .changes.json file (exported from OT Tables Compare)
  - The font files referenced in the JSON

Modified fonts are saved as <original_name>.modified.<ext>
Originals are left untouched.
"""

import sys
import json
import struct
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
except ImportError:
    print("ERROR: fontTools not found. Install it:")
    print("  pip install fonttools")
    sys.exit(1)


# ── name table helpers ──

NAME_FIELD_TO_ID = {
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10, "11": 11, "12": 12,
    "13": 13, "14": 14, "16": 16, "17": 17, "18": 18, "19": 19,
    "20": 20, "21": 21, "22": 22, "23": 23, "24": 24, "25": 25,
}


def apply_name_change(font, name_id, new_value):
    """Set a name record across all platform/encoding/language combos."""
    name_id = int(name_id)
    name_table = font["name"]

    # Collect existing records for this nameID to preserve platform/encoding/lang
    existing = [r for r in name_table.names if r.nameID == name_id]

    if existing:
        for record in existing:
            name_table.setName(
                new_value,
                record.nameID,
                record.platformID,
                record.platEncID,
                record.langID,
            )
    else:
        # No existing record — create Windows Unicode BMP (3,1,0x0409)
        # and Macintosh Roman (1,0,0)
        name_table.setName(new_value, name_id, 3, 1, 0x0409)
        name_table.setName(new_value, name_id, 1, 0, 0x0000)

    return True


# ── OS/2 table helpers ──

OS2_INT_FIELDS = {
    "version", "xAvgCharWidth", "usWeightClass", "usWidthClass", "fsType",
    "ySubscriptXSize", "ySubscriptYSize", "ySubscriptXOffset", "ySubscriptYOffset",
    "ySuperscriptXSize", "ySuperscriptYSize", "ySuperscriptXOffset", "ySuperscriptYOffset",
    "yStrikeoutSize", "yStrikeoutPosition", "sFamilyClass",
    "ulUnicodeRange1", "ulUnicodeRange2", "ulUnicodeRange3", "ulUnicodeRange4",
    "fsSelection", "usFirstCharIndex", "usLastCharIndex",
    "sTypoAscender", "sTypoDescender", "sTypoLineGap",
    "usWinAscent", "usWinDescent",
    "ulCodePageRange1", "ulCodePageRange2",
    "sxHeight", "sCapHeight", "usDefaultChar", "usBreakChar", "usMaxContext",
    "usLowerOpticalPointSize", "usUpperOpticalPointSize",
}

OS2_STR_FIELDS = {"achVendID"}


def parse_int_value(val_str):
    """Parse int from string, supporting hex (0x...) notation."""
    val_str = val_str.strip()
    # Strip any annotation like "400 (Regular)" or "64 — REGULAR"
    for sep in [" —", " (", "  "]:
        if sep in val_str:
            val_str = val_str[:val_str.index(sep)].strip()
    if val_str.startswith("0x") or val_str.startswith("0X"):
        return int(val_str, 16)
    return int(val_str)


def apply_os2_change(font, field, new_value):
    """Set an OS/2 table field."""
    if "OS/2" not in font:
        print(f"  WARNING: Font has no OS/2 table, skipping {field}")
        return False

    os2 = font["OS/2"]

    if field == "panose":
        # panose value like "2 11 6 4 2 2 2 2 2 4"
        parts = new_value.strip().split()
        if len(parts) == 10:
            panose_keys = [
                "bFamilyType", "bSerifStyle", "bWeight", "bProportion",
                "bContrast", "bStrokeVariation", "bArmStyle", "bLetterform",
                "bMidline", "bXHeight",
            ]
            panose = os2.panose
            for key, val in zip(panose_keys, parts):
                setattr(panose, key, int(val))
            return True
        else:
            print(f"  WARNING: panose needs 10 values, got {len(parts)}")
            return False

    if field in OS2_INT_FIELDS:
        setattr(os2, field, parse_int_value(str(new_value)))
        return True

    if field in OS2_STR_FIELDS:
        setattr(os2, field, str(new_value))
        return True

    print(f"  WARNING: Unknown OS/2 field '{field}', skipping")
    return False


# ── head table helpers ──

HEAD_INT_FIELDS = {
    "flags", "unitsPerEm", "macStyle", "lowestRecPPEM",
    "fontDirectionHint", "indexToLocFormat", "glyphDataFormat",
}

HEAD_FLOAT_FIELDS = {"fontRevision"}


def apply_head_change(font, field, new_value):
    """Set a head table field."""
    if "head" not in font:
        print(f"  WARNING: Font has no head table, skipping {field}")
        return False

    head = font["head"]

    if field in HEAD_INT_FIELDS:
        val_str = str(new_value).strip()
        for sep in [" —", " (", "  "]:
            if sep in val_str:
                val_str = val_str[:val_str.index(sep)].strip()
        setattr(head, field, int(val_str))
        return True

    if field in HEAD_FLOAT_FIELDS:
        setattr(head, field, float(str(new_value).strip()))
        return True

    if field in ("xMin", "yMin", "xMax", "yMax"):
        setattr(head, field, int(str(new_value).strip()))
        return True

    print(f"  WARNING: head.{field} is read-only or unknown, skipping")
    return False


# ── Main ──

def process_changes(folder_path):
    folder = Path(folder_path)
    if not folder.is_dir():
        print(f"ERROR: '{folder}' is not a directory")
        sys.exit(1)

    # Find .changes.json files
    json_files = list(folder.glob("*.changes.json"))
    if not json_files:
        print(f"ERROR: No .changes.json files found in '{folder}'")
        sys.exit(1)

    for jf in json_files:
        print(f"\n{'='*60}")
        print(f"Processing: {jf.name}")
        print(f"{'='*60}")

        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)

        changes = data.get("changes", [])
        if not changes:
            print("  No changes found in file.")
            continue

        # Group changes by font file
        by_font = {}
        for ch in changes:
            fname = ch["file"]
            by_font.setdefault(fname, []).append(ch)

        for font_file, file_changes in by_font.items():
            font_path = folder / font_file
            if not font_path.exists():
                print(f"\n  SKIP: '{font_file}' not found in folder")
                continue

            print(f"\n  Font: {font_file} ({len(file_changes)} changes)")

            try:
                font = TTFont(str(font_path))
            except Exception as e:
                print(f"  ERROR loading font: {e}")
                continue

            applied = 0
            for ch in file_changes:
                table = ch["table"]
                field = ch["field"]
                new_val = ch["new_value"]

                ok = False
                if table == "name":
                    ok = apply_name_change(font, field, new_val)
                elif table == "OS/2":
                    ok = apply_os2_change(font, field, new_val)
                elif table == "head":
                    ok = apply_head_change(font, field, new_val)
                else:
                    print(f"    SKIP: Unknown table '{table}'")
                    continue

                status = "OK" if ok else "FAIL"
                print(f"    [{status}] {table}.{field} = {new_val!r}")
                if ok:
                    applied += 1

            # Save
            stem = font_path.stem
            ext = font_path.suffix
            out_path = folder / f"{stem}.modified{ext}"
            try:
                font.save(str(out_path))
                print(f"  SAVED: {out_path.name} ({applied}/{len(file_changes)} changes applied)")
            except Exception as e:
                print(f"  ERROR saving: {e}")
            finally:
                font.close()

    print(f"\nDone.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    process_changes(sys.argv[1])
