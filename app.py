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
OUTPUT_DIR_DEFAULT = None  # None = same folder as input


def resource_path(relative_path):
    """Resolve a bundled asset path, whether running from source or a
    PyInstaller-frozen exe (where data files live under sys._MEIPASS)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("640x480")
        self.root.minsize(520, 360)
        try:
            self.root.iconbitmap(resource_path(os.path.join("assets", "kdoc_header.ico")))
        except tk.TclError:
            pass

        self.drop_frame = tk.Frame(root, bg="#eef2f7", bd=2, relief="groove")
        self.drop_frame.pack(fill="x", padx=16, pady=16, ipady=28)

        drop_text = "Drag & drop .docx files here" if HAS_DND else \
            "Drag & drop unavailable — use 'Choose Files' below"
        self.drop_label = tk.Label(
            self.drop_frame, text=drop_text, bg="#eef2f7",
            fg="#33475b", font=("Segoe UI", 13),
        )
        self.drop_label.pack(expand=True)

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=16)
        tk.Button(btn_frame, text="Choose Files...", command=self.choose_files).pack(side="left")
        tk.Button(btn_frame, text="Clear Log", command=self.clear_log).pack(side="left", padx=8)

        tk.Label(root, text="Log:", anchor="w").pack(fill="x", padx=16, pady=(12, 0))
        self.log_box = scrolledtext.ScrolledText(root, height=16, state="disabled", font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(4, 16))

        if HAS_DND:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind("<<Drop>>", self.on_drop)

    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        self.root.update_idletasks()

    def clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def on_drop(self, event):
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
        self.log(f"\n=== {os.path.basename(path)} ===")
        out_dir = os.path.dirname(path)
        try:
            output_path, report = process_file(path, out_dir, log=self.log)
        except Exception as e:
            self.log(f"  ERROR: {e}")
            messagebox.showerror("Error", f"Failed to process {os.path.basename(path)}:\n{e}")
            traceback.print_exc()
            return

        n_applied = len(report["applied"])
        n_skipped = len(report["skipped_already_styled"])
        n_missing = len(report["skipped_missing_style"])

        self.log(f"  Headings applied: {n_applied}")
        if n_skipped:
            self.log(f"  Already styled (left as-is): {n_skipped}")
        if n_missing:
            self.log(f"  WARNING: predicted style not found in this doc's template: {n_missing}")
        self.log(f"  Saved: {output_path}")


def main():
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
