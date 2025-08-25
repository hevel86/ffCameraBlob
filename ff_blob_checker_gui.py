
import os
import csv
import shutil
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "FastForward Blob Checker"

def parse_csv(csv_path):
    #
    # Parse the CSV exported by the vision application.
    # The first line is metadata and must be skipped.
    # Fields are ';' separated. Returns a list of dict rows.
    #
    rows = []
    with open(csv_path, "r", newline="", encoding="utf-8", errors="ignore") as f:
        # Skip the metadata line
        _ = f.readline()
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            rows.append(row)
    return rows

def to_float(val, default=float("nan")):
    try:
        return float(val)
    except Exception:
        return default

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("820x620")
        self.resizable(True, True)

        # Variables
        self.csv_path_var = tk.StringVar()
        self.expected_var = tk.StringVar(value="9")

        # Image source dir controls
        self.img_from_parent_var = tk.BooleanVar(value=True)  # default: one directory above CSV
        self.img_dir_var = tk.StringVar()

        # Failed dir controls
        self.failed_same_as_csv_var = tk.BooleanVar(value=True)  # default: same as CSV folder
        self.failed_dir_var = tk.StringVar()

        # Action mode: move or copy
        self.action_mode_var = tk.StringVar(value="copy")  # "move" or "copy"

        # UI Layout
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True)

        # Row 0: CSV selector
        ttk.Label(frm, text="CSV file to analyze:").grid(row=0, column=0, sticky="w", **pad)
        csv_entry = ttk.Entry(frm, textvariable=self.csv_path_var, width=70)
        csv_entry.grid(row=0, column=1, sticky="we", **pad)
        ttk.Button(frm, text="Browse…", command=self.browse_csv).grid(row=0, column=2, **pad)

        # Row 1: Expected max
        ttk.Label(frm, text="Expected BlobNumResults (max):").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.expected_var, width=10).grid(row=1, column=1, sticky="w", **pad)

        # Separator
        ttk.Separator(frm).grid(row=2, column=0, columnspan=3, sticky="we", padx=10)

        # Row 3-5: Image source location
        ttk.Label(frm, text="Source images folder (where the BMPs live):").grid(row=3, column=0, columnspan=3, sticky="w", **pad)

        self.chk_img_parent = ttk.Checkbutton(
            frm,
            text="Use folder ONE LEVEL ABOVE the CSV (default)",
            variable=self.img_from_parent_var,
            command=self._toggle_img_dir_controls,
        )
        self.chk_img_parent.grid(row=4, column=0, columnspan=3, sticky="w", **pad)

        ttk.Label(frm, text="Or specify a custom images folder:").grid(row=5, column=0, sticky="w", **pad)
        self.img_entry = ttk.Entry(frm, textvariable=self.img_dir_var, width=70, state="disabled")
        self.img_entry.grid(row=5, column=1, sticky="we", **pad)
        ttk.Button(frm, text="Browse…", command=self.browse_img_dir).grid(row=5, column=2, **pad)

        # Separator
        ttk.Separator(frm).grid(row=6, column=0, columnspan=3, sticky="we", padx=10)

        # Row 7-9: Failed folder
        ttk.Label(frm, text="Destination 'failed' folder:").grid(row=7, column=0, columnspan=3, sticky="w", **pad)

        self.chk_failed_same = ttk.Checkbutton(
            frm,
            text="Use the SAME folder as the CSV (default)",
            variable=self.failed_same_as_csv_var,
            command=self._toggle_failed_dir_controls,
        )
        self.chk_failed_same.grid(row=8, column=0, columnspan=3, sticky="w", **pad)

        ttk.Label(frm, text="Or specify a custom failed folder:").grid(row=9, column=0, sticky="w", **pad)
        self.failed_entry = ttk.Entry(frm, textvariable=self.failed_dir_var, width=70, state="disabled")
        self.failed_entry.grid(row=9, column=1, sticky="we", **pad)
        ttk.Button(frm, text="Browse…", command=self.browse_failed_dir).grid(row=9, column=2, **pad)

        # Separator
        ttk.Separator(frm).grid(row=10, column=0, columnspan=3, sticky="we", padx=10)

        # Row 11: Action mode (move/copy)
        ttk.Label(frm, text="When handling under-max images:").grid(row=11, column=0, sticky="w", **pad)
        actions_frame = ttk.Frame(frm)
        actions_frame.grid(row=11, column=1, columnspan=2, sticky="w", **pad)
        ttk.Radiobutton(actions_frame, text="Move (destructive)", value="move", variable=self.action_mode_var).pack(side="left", padx=6)
        ttk.Radiobutton(actions_frame, text="Copy (non-destructive)", value="copy", variable=self.action_mode_var).pack(side="left", padx=6)

        # Row 12: Buttons
        actions2 = ttk.Frame(frm)
        actions2.grid(row=12, column=0, columnspan=3, sticky="we", **pad)
        ttk.Button(actions2, text="Analyze (no move/copy)", command=self.analyze_only).pack(side="left", padx=6)
        ttk.Button(actions2, text="Analyze & Execute", command=self.analyze_and_execute).pack(side="left", padx=6)

        # Row 13-14: Results
        ttk.Label(frm, text="Results:").grid(row=13, column=0, sticky="w", **pad)
        self.text = tk.Text(frm, height=16, wrap="word")
        self.text.grid(row=14, column=0, columnspan=3, sticky="nsew", **pad)

        # Expand config
        frm.rowconfigure(14, weight=1)
        frm.columnconfigure(1, weight=1)

        # Initialize disabled states correctly
        self._toggle_img_dir_controls()
        self._toggle_failed_dir_controls()

    def _toggle_img_dir_controls(self):
        if self.img_from_parent_var.get():
            self.img_entry.configure(state="disabled")
        else:
            self.img_entry.configure(state="normal")

    def _toggle_failed_dir_controls(self):
        if self.failed_same_as_csv_var.get():
            self.failed_entry.configure(state="disabled")
        else:
            self.failed_entry.configure(state="normal")

    def browse_csv(self):
        path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.csv_path_var.set(path)
            # Auto-populate defaults based on chosen CSV
            csv_dir = os.path.dirname(path)
            parent_dir = os.path.dirname(csv_dir)

            # Default image source = parent of CSV
            self.img_from_parent_var.set(True)
            self.img_dir_var.set(parent_dir)

            # Default failed folder = same as CSV directory
            self.failed_same_as_csv_var.set(True)
            self.failed_dir_var.set(csv_dir)

            # Refresh states
            self._toggle_img_dir_controls()
            self._toggle_failed_dir_controls()

    def browse_img_dir(self):
        path = filedialog.askdirectory(title="Select SOURCE folder containing BMP images")
        if path:
            self.img_dir_var.set(path)
            self.img_from_parent_var.set(False)
            self._toggle_img_dir_controls()

    def browse_failed_dir(self):
        path = filedialog.askdirectory(title="Select destination folder for FAILED images")
        if path:
            self.failed_dir_var.set(path)
            self.failed_same_as_csv_var.set(False)
            self._toggle_failed_dir_controls()

    def analyze_only(self):
        self._run(execute=False)

    def analyze_and_execute(self):
        self._run(execute=True)

    def _resolve_dirs(self):
        csv_path = self.csv_path_var.get().strip()
        if not csv_path or not os.path.exists(csv_path):
            raise ValueError("Please select a valid CSV file.")

        csv_dir = os.path.dirname(csv_path)
        parent_dir = os.path.dirname(csv_dir)

        # Resolve image source directory
        if self.img_from_parent_var.get():
            img_src_dir = parent_dir
        else:
            img_src_dir = self.img_dir_var.get().strip()
            if not img_src_dir:
                raise ValueError("Please select the source images folder.")
            if not os.path.isdir(img_src_dir):
                raise ValueError("Invalid source images folder.")

        # Resolve failed folder
        if self.failed_same_as_csv_var.get():
            failed_dir = csv_dir
        else:
            failed_dir = self.failed_dir_var.get().strip()
            if not failed_dir:
                raise ValueError("Please select a destination folder for FAILED images.")

        return csv_path, img_src_dir, failed_dir

    def _run(self, execute=False):
        # Clear UI
        self.text.delete("1.0", tk.END)

        try:
            csv_path, img_src_dir, failed_dir = self._resolve_dirs()
        except Exception as e:
            messagebox.showerror(APP_TITLE, str(e))
            return

        # Parse expected max
        try:
            expected_max = int(self.expected_var.get().strip())
        except Exception:
            messagebox.showerror(APP_TITLE, "Expected max must be an integer.")
            return

        # Parse CSV
        try:
            rows = parse_csv(csv_path)
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Failed to parse CSV:\n{e}")
            return

        total_rows = len(rows)
        under_max = []
        for r in rows:
            val = to_float(r.get("BlobNumResults", ""))
            if val != val:  # NaN
                continue
            if val < expected_max:
                under_max.append((r.get("ImageName", ""), val))

        # Prepare timestamp & log path
        ts = time.strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(os.path.dirname(csv_path), f"failed_log_{ts}.csv")

        # Create failed dir and timestamped subdir if executing
        run_failed_dir = None
        moved_count = 0
        missing_count = 0
        action_desc = self.action_mode_var.get()

        if execute:
            # Ensure base failed dir exists
            os.makedirs(failed_dir, exist_ok=True)
            # Create timestamped run subdir
            run_failed_dir = os.path.join(failed_dir, f"failed_{ts}")
            os.makedirs(run_failed_dir, exist_ok=True)

        # Write log and (optionally) execute
        with open(log_path, "w", newline="", encoding="utf-8") as lf:
            w = csv.writer(lf)
            w.writerow(["ImageName", "BlobNumResults", "Action", "Note"])

            for img_name, val in under_max:
                action = ""
                note = ""
                if execute:
                    src = os.path.join(img_src_dir, img_name)
                    dst = os.path.join(run_failed_dir, img_name)
                    if os.path.exists(src):
                        try:
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                            if action_desc == "move":
                                shutil.move(src, dst)
                                action = "moved"
                            else:
                                shutil.copy2(src, dst)
                                action = "copied"
                            moved_count += 1
                        except Exception as e:
                            action = "error"
                            note = f"{action_desc}-error: {e}"
                    else:
                        action = "missing"
                        note = "source-missing"
                        missing_count += 1

                w.writerow([img_name, val, action, note])

        # UI Summary
        self.text.insert(tk.END, f"CSV: {csv_path}\n")
        self.text.insert(tk.END, f"Total rows: {total_rows}\n")
        self.text.insert(tk.END, f"Expected max: {expected_max}\n")
        self.text.insert(tk.END, f"Under-max count: {len(under_max)}\n")
        self.text.insert(tk.END, f"Log written to: {log_path}\n")
        if execute:
            self.text.insert(tk.END, f"Action: {action_desc}\n")
            self.text.insert(tk.END, f"Processed: {moved_count}, Missing at source: {missing_count}\n")
            self.text.insert(tk.END, f"Run folder: {run_failed_dir}\n")

        if under_max:
            self.text.insert(tk.END, "\nUnder-max files (first 200):\n")
            for img_name, val in under_max[:200]:
                self.text.insert(tk.END, f"  {img_name} -> {int(val) if val==int(val) else val}\n")
            if len(under_max) > 200:
                self.text.insert(tk.END, f"... and {len(under_max)-200} more.\n")
        else:
            self.text.insert(tk.END, "\nAll files meet the expected max.\n")

        # Final toast
        if execute:
            messagebox.showinfo(APP_TITLE, f"Done ({action_desc}).\nProcessed: {moved_count}\nMissing: {missing_count}\nLog: {os.path.basename(log_path)}")
        else:
            messagebox.showinfo(APP_TITLE, f"Analysis complete.\nUnder-max: {len(under_max)}\nLog: {os.path.basename(log_path)}")

if __name__ == "__main__":
    App().mainloop()
