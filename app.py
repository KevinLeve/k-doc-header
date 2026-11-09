"""K-Doc Header - drag-and-drop desktop app.

Drop a .docx manuscript in; it detects manually-formatted headings and
reapplies the correct named Word heading styles, so the Navigation Pane
and auto-TOC work. Output is saved next to the input as "<name>_styled.docx".
"""
import os
import sys
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

from engine import process_file

APP_NAME = "K-Doc Header"
APP_TAGLINE = "Heading style detector for Word documents"
APP_VERSION = "1.1.0"

# --- palette (matches the app's navy/blue logo) -----------------------------
NAVY = "#0B1E3C"
NAVY_LIGHT = "#13335E"
ACCENT = "#2F7FE0"
ACCENT_HOVER = "#2567BD"
ACCENT_SOFT = "#EAF2FD"
LIGHT_BG = "#F4F6FA"
CARD_BG = "#FFFFFF"
BORDER = "#E1E6ED"
TEXT_MAIN = "#1C2733"
TEXT_MUTED = "#6B7686"
SUCCESS = "#1E8E5A"
WARNING = "#B8720A"
ERROR = "#C62828"


def resource_path(relative_path):
    """Resolve a bundled asset path, whether running from source or a
    PyInstaller-frozen exe (where data files live under sys._MEIPASS)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


def round_rect(canvas, x1, y1, x2, y2, r=16, **kwargs):
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class FlatButton(tk.Button):
    """A flat, cursor-aware button with a hover color change."""

    def __init__(self, master, bg, hover_bg, fg="white", **kwargs):
        super().__init__(
            master, bg=bg, fg=fg, activebackground=hover_bg, activeforeground=fg,
            relief="flat", bd=0, padx=18, pady=9, cursor="hand2",
            font=("Segoe UI Semibold", 10), **kwargs,
        )
        self._bg, self._hover_bg = bg, hover_bg
        self.bind("<Enter>", lambda e: self.configure(bg=hover_bg))
        self.bind("<Leave>", lambda e: self.configure(bg=self._bg))


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("760x620")
        self.root.minsize(620, 480)
        self.root.configure(bg=LIGHT_BG)
        try:
            self.root.iconbitmap(resource_path(os.path.join("assets", "kdoc_header.ico")))
        except tk.TclError:
            pass

        self.processed_count = 0

        self._build_header()
        self._build_body()

    # ------------------------------------------------------------------ UI
    def _build_header(self):
        header = tk.Frame(self.root, bg=NAVY, height=84)
        header.pack(fill="x")
        header.pack_propagate(False)

        inner = tk.Frame(header, bg=NAVY)
        inner.pack(side="left", padx=24, pady=14)

        try:
            self._logo_img = tk.PhotoImage(file=resource_path(os.path.join("assets", "kdoc_header_header.png")))
            tk.Label(inner, image=self._logo_img, bg=NAVY).pack(side="left", padx=(0, 14))
        except tk.TclError:
            pass

        text_col = tk.Frame(inner, bg=NAVY)
        text_col.pack(side="left")
        tk.Label(text_col, text=APP_NAME, bg=NAVY, fg="white",
                 font=("Segoe UI Semibold", 18)).pack(anchor="w")
        tk.Label(text_col, text=APP_TAGLINE, bg=NAVY, fg="#9FB3D1",
                 font=("Segoe UI", 10)).pack(anchor="w")

    def _build_body(self):
        body = tk.Frame(self.root, bg=LIGHT_BG)
        body.pack(fill="both", expand=True, padx=24, pady=20)

        self._build_drop_zone(body)
        self._build_buttons(body)
        self._build_log_card(body)
        self._build_status_bar()

    def _build_drop_zone(self, parent):
        self.drop_canvas = tk.Canvas(parent, height=140, bg=LIGHT_BG, highlightthickness=0)
        self.drop_canvas.pack(fill="x", pady=(0, 16))
        self.drop_canvas.bind("<Configure>", lambda e: self._redraw_drop_zone())
        self.drop_canvas.bind("<Button-1>", lambda e: self.choose_files())
        self.drop_canvas.bind("<Enter>", lambda e: self._set_drop_hover(True))
        self.drop_canvas.bind("<Leave>", lambda e: self._set_drop_hover(False))

        if HAS_DND:
            self.drop_canvas.drop_target_register(DND_FILES)
            self.drop_canvas.dnd_bind("<<Drop>>", self.on_drop)
            self.drop_canvas.dnd_bind("<<DropEnter>>", lambda e: self._set_drop_hover(True))
            self.drop_canvas.dnd_bind("<<DropLeave>>", lambda e: self._set_drop_hover(False))

        self._drop_hover = False
        self.root.after(10, self._redraw_drop_zone)

    def _set_drop_hover(self, hovering):
        self._drop_hover = hovering
        self._redraw_drop_zone()

    def _redraw_drop_zone(self):
        c = self.drop_canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 10 or h < 10:
            return
        border_color = ACCENT if self._drop_hover else "#C7D1DF"
        fill_color = ACCENT_SOFT if self._drop_hover else CARD_BG
        round_rect(c, 2, 2, w - 2, h - 2, r=18, fill=fill_color, outline=border_color, width=2)
        # dashed inner outline for the "drop target" affordance
        c.create_line(0, 0, 0, 0)  # no-op to keep ordering stable

        title = "Drag & drop .docx files here" if HAS_DND else "Click to choose .docx files"
        subtitle = "or click to browse" if HAS_DND else "drag & drop isn't available in this build"
        c.create_text(w / 2, h / 2 - 12, text="⬆", font=("Segoe UI Symbol", 20),
                       fill=ACCENT if self._drop_hover else TEXT_MUTED)
        c.create_text(w / 2, h / 2 + 16, text=title, font=("Segoe UI Semibold", 12), fill=TEXT_MAIN)
        c.create_text(w / 2, h / 2 + 38, text=subtitle, font=("Segoe UI", 9), fill=TEXT_MUTED)

    def _build_buttons(self, parent):
        btn_row = tk.Frame(parent, bg=LIGHT_BG)
        btn_row.pack(fill="x", pady=(0, 16))

        FlatButton(btn_row, bg=ACCENT, hover_bg=ACCENT_HOVER,
                   text="Choose Files...", command=self.choose_files).pack(side="left")
        FlatButton(btn_row, bg=CARD_BG, hover_bg="#EDEFF3", fg=TEXT_MAIN,
                   text="Clear Log", command=self.clear_log).pack(side="left", padx=(10, 0))

    def _build_log_card(self, parent):
        card = tk.Frame(parent, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="both", expand=True)

        header = tk.Frame(card, bg=CARD_BG)
        header.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(header, text="Activity", bg=CARD_BG, fg=TEXT_MAIN,
                 font=("Segoe UI Semibold", 11)).pack(side="left")

        self.log_box = scrolledtext.ScrolledText(
            card, height=14, state="disabled", font=("Consolas", 10),
            bg=CARD_BG, fg=TEXT_MAIN, relief="flat", bd=0, wrap="word",
            padx=16, pady=4,
        )
        self.log_box.pack(fill="both", expand=True, padx=2, pady=(0, 12))
        self.log_box.tag_config("header", foreground=NAVY, font=("Consolas", 10, "bold"))
        self.log_box.tag_config("success", foreground=SUCCESS)
        self.log_box.tag_config("warning", foreground=WARNING)
        self.log_box.tag_config("error", foreground=ERROR)
        self.log_box.tag_config("muted", foreground=TEXT_MUTED)
        self.log_box.tag_config("info", foreground=TEXT_MAIN)

        placeholder = "Drop a .docx file above to see activity here."
        self.log_box.configure(state="normal")
        self.log_box.insert("end", placeholder, "muted")
        self.log_box.configure(state="disabled")
        self._placeholder_shown = True

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=NAVY_LIGHT, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status_label = tk.Label(bar, text="Ready", bg=NAVY_LIGHT, fg="#C7D4E8",
                                      font=("Segoe UI", 9))
        self.status_label.pack(side="left", padx=14)
        tk.Label(bar, text=f"v{APP_VERSION}", bg=NAVY_LIGHT, fg="#6E85A8",
                 font=("Segoe UI", 9)).pack(side="right", padx=14)

    # -------------------------------------------------------------- logic
    def log(self, msg, tag=None):
        if tag is None:
            stripped = msg.strip()
            if stripped.startswith("==="):
                tag = "header"
            elif stripped.startswith("+"):
                tag = "success"
            elif stripped.startswith("!") or "WARNING" in stripped:
                tag = "warning"
            elif "ERROR" in stripped:
                tag = "error"
            else:
                tag = "info"

        self.log_box.configure(state="normal")
        if getattr(self, "_placeholder_shown", False):
            self.log_box.delete("1.0", "end")
            self._placeholder_shown = False
        self.log_box.insert("end", msg + "\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        self.root.update_idletasks()

    def clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self._placeholder_shown = False
        self.status_label.configure(text="Ready")

    def on_drop(self, event):
        self._set_drop_hover(False)
        paths = self.root.tk.splitlist(event.data)
        self.process_paths(paths)

    def choose_files(self):
        paths = filedialog.askopenfilenames(
            title="Choose Word documents",
            filetypes=[("Word documents", "*.docx")],
        )
        if paths:
            self.process_paths(paths)

    def process_paths(self, paths):
        for path in paths:
            self.process_one(path)

    def process_one(self, path):
        self.status_label.configure(text=f"Processing {os.path.basename(path)}...")
        self.log(f"\n=== {os.path.basename(path)} ===")
        out_dir = os.path.dirname(path)
        try:
            output_path, report = process_file(path, out_dir, log=self.log)
        except Exception as e:
            self.log(f"  ERROR: {e}")
            self.status_label.configure(text="Error - see activity log")
            messagebox.showerror("Error", f"Failed to process {os.path.basename(path)}:\n{e}")
            traceback.print_exc()
            return

        n_applied = len(report["applied"])
        n_skipped = len(report["skipped_already_styled"])
        n_missing = len(report["skipped_missing_style"])

        self.log(f"  + Headings applied: {n_applied}")
        if n_skipped:
            self.log(f"  Already styled (left as-is): {n_skipped}")
        if n_missing:
            self.log(f"  ! WARNING: predicted style not found in this doc's template: {n_missing}")
        self.log(f"  Saved: {output_path}")

        self.processed_count += 1
        self.status_label.configure(
            text=f"Done - {self.processed_count} file(s) processed this session"
        )


def main():
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
