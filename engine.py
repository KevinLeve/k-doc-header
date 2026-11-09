"""Core detection/styling engine.

Reads a .docx whose headings were typed manually (right font/size/bold but
not tagged with a named Word style) and reapplies the matching named
heading style, so Word's Navigation Pane and auto-generated TOC work.
"""
import json
import os
from docx import Document

HEADING_STYLES = [
    "Chap #", "Chap Title", "Part #", "Part Title",
    "Heading 1", "Heading 2", "Heading 3",
    "SB Head", "TB Head",
]

SIGNATURE_MAP_PATH = os.path.join(os.path.dirname(__file__), "signature_map.json")

# body text runs at ~9.5pt in this template; styles with no explicit size
# (e.g. "Heading 3", "TB Head") inherit that, so we use it as their
# effective size for nearest-match comparisons
BODY_SIZE_PT = 9.5

# how far (in points) a hand-typed heading's size may drift from the
# learned signature and still match; must stay below half the smallest
# gap between two real signature sizes for the same font, or adjacent
# levels become ambiguous
SIZE_TOLERANCE_PT = 2.0


def load_signature_map(path=SIGNATURE_MAP_PATH):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


class HeadingDetector:
    def __init__(self, signature_map):
        self.signature_map = signature_map

    def classify(self, font_name, size_pt, bold):
        if font_name is None:
            return None
        actual_size = size_pt if size_pt is not None else BODY_SIZE_PT

        # bold is a tiebreaker, not a hard filter: authors who change font/size
        # by hand often forget to also bold, and font+size alone already
        # separate every style in this template
        best_style, best_distance = None, None
        for style_name, sig in self.signature_map.items():
            if font_name != sig["font"]:
                continue
            effective_size = sig["size_pt"] if sig["size_pt"] is not None else BODY_SIZE_PT
            distance = abs(actual_size - effective_size)
            if sig["bold"] is not None and bool(bold) != bool(sig["bold"]):
                distance += 0.1  # small penalty, breaks ties only
            if distance <= SIZE_TOLERANCE_PT and (best_distance is None or distance < best_distance):
                best_style, best_distance = style_name, distance
        return best_style


def first_run_format(paragraph):
    """Return (font_name, size_pt, bold) of the first non-empty run."""
    for r in paragraph.runs:
        if r.text.strip():
            size_pt = round(r.font.size.pt, 1) if r.font.size else None
            return r.font.name, size_pt, r.font.bold
    return None, None, None


def process_document(input_path, output_path, detector, log=None):
    """Detect and reapply heading styles. Returns a report dict."""
    doc = Document(input_path)
    report = {"applied": [], "skipped_already_styled": [], "skipped_missing_style": []}

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        current_style = p.style.name if p.style else None
        if current_style in HEADING_STYLES:
            report["skipped_already_styled"].append(text[:60])
            continue

        font_name, size_pt, bold = first_run_format(p)
        predicted = detector.classify(font_name, size_pt, bold)
        if predicted is None:
            continue

        try:
            p.style = doc.styles[predicted]
            report["applied"].append((predicted, text[:60]))
            if log:
                log(f"  + {predicted}: {text[:60]}")
        except KeyError:
            report["skipped_missing_style"].append((predicted, text[:60]))
            if log:
                log(f"  ! style {predicted!r} not in this document's template, skipped: {text[:60]}")

    doc.save(output_path)
    return report


def process_file(input_path, output_dir, log=None):
    """Entry point used by the GUI. Handles .docx only."""
    ext = os.path.splitext(input_path)[1].lower()
    if ext != ".docx":
        raise ValueError(
            f"Unsupported file type {ext!r}. Convert PDFs to .docx with the "
            f"pdf2word tool first, then run this tool on the result."
        )

    signature_map = load_signature_map()
    detector = HeadingDetector(signature_map)

    base = os.path.basename(input_path)
    name, _ = os.path.splitext(base)
    output_path = os.path.join(output_dir, f"{name}_styled.docx")

    report = process_document(input_path, output_path, detector, log=log)
    return output_path, report
