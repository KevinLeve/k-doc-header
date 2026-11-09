"""Learns the heading-style signature map from a folder of reference .docx
files (the correctly-styled sample chapters) and writes it to
signature_map.json for the engine to use.

Run this again whenever the client gives new reference chapters that use
styles not seen before.
"""
import json
import glob
import os
import sys
from docx import Document

HEADING_STYLES = [
    "Chap #", "Chap Title", "Part #", "Part Title",
    "Heading 1", "Heading 2", "Heading 3",
    "SB Head", "TB Head",
]


def build_map(reference_folder):
    sig_map = {}
    for f in sorted(glob.glob(os.path.join(reference_folder, "*.docx"))):
        if os.path.basename(f).startswith("~$"):
            continue
        doc = Document(f)
        for name in HEADING_STYLES:
            if name in sig_map:
                continue
            try:
                style = doc.styles[name]
            except KeyError:
                continue
            sz = style.font.size
            fname = style.font.name
            bold = style.font.bold
            if fname is not None:
                sig_map[name] = {
                    "font": fname,
                    "size_pt": round(sz.pt, 1) if sz else None,
                    "bold": bold,
                }
    return sig_map


if __name__ == "__main__":
    ref_folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "Doc files for Coding", "_backup_original"
    )
    out_path = os.path.join(os.path.dirname(__file__), "signature_map.json")

    sig_map = build_map(ref_folder)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(sig_map, fh, indent=2)

    print(f"Learned {len(sig_map)} heading styles from {ref_folder}")
    for name, sig in sig_map.items():
        print(f"  {name}: {sig}")
    print(f"Saved to {out_path}")
