
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
        self.geometry("720x520")
        self.resizable(True, True)

        # Variables
        self.csv_path_var = tk.StringVar()
        self.expected_var = tk.StringVar(value="9")
        self.failed_dir_var = tk.StringVar()
        self.assume_img_dir_var = tk.BooleanVar(value=True)
        self.img_dir_var = tk.StringVar()

        # UI Layout
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True)

        # Row 1: CSV selector
        ttk.Label(frm, text="CSV file to analyze:").grid(row=0, column=0, sticky="w", **pad)
        csv_entry = ttk.Entry(frm, textvariable=self.csv_path_var, width=70)
        csv_entry.grid(row=0, column=1, sticky="we", **pad)
        ttk.Button(frm, text="Browse…", command=self.browse_csv).grid(row=0, column=2, **pad)

        # Row 2: Expected max
        ttk.Label(frm, text="Expected BlobNumResults (max):").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.expected_var, width=10).grid(row=1, column=1, sticky="w", **pad)

        # Row 3: Failed folder selector
        ttk.Label(frm, text="Destination folder for failed BMPs:").grid(row=2, column=0, sticky="w", **pad)
        failed_entry = ttk.Entry(frm, textvariable=self.failed_dir_var, width=70)
        failed_entry.grid(row=2, column=1, sticky="we", **pad)
        ttk.Button(frm, text="Browse…", command=self.browse_failed_dir).grid(row=2, column=2, **pad)

        # Row 4: Source images folder (optional)
        ttk.Checkbutton(frm, text="Images live in the SAME folder as the CSV", variable=self.assume_img_dir_var, command=self.toggle_img_dir).grid(row=3, column=0, columnspan=3, sticky="w", **pad)
        ttk.Label(frm, text="(Optional) Source images folder:").grid(row=4, column=0, sticky="w", **pad)
        img_entry = ttk.Entry(frm, textvariable=self.img_dir_var, width=70, state="disabled")
        img_entry.grid(row=4, column=1, sticky="we", **pad)
        self.img_entry_widget = img_entry
        ttk.Button(frm, text="Browse…", command=self.browse_img_dir).grid(row=4, column=2, **pad)

        # Row 5: Actions
        actions = ttk.Frame(frm)
        actions.grid(row=5, column=0, columnspan=3, sticky="we", **pad)
        ttk.Button(actions, text="Analyze (no move)", command=self.analyze_only).pack(side="left", padx=6)
        ttk.Button(actions, text="Analyze & Move Failed", command=self.analyze_and_move).pack(side="left", padx=6)

        # Row 6: Results area
        ttk.Label(frm, text="Results:").grid(row=6, column=0, sticky="w", **pad)
        self.text = tk.Text(frm, height=16, wrap="word")
        self.text.grid(row=7, column=0, columnspan=3, sticky="nsew", **pad)

        # Make the text area expandable
        frm.rowconfigure(7, weight=1)
        frm.columnconfigure(1, weight=1)

    def toggle_img_dir(self):
        if self.assume_img_dir_var.get():
            self.img_entry_widget.configure(state="disabled")
        else:
            self.img_entry_widget.configure(state="normal")

    def browse_csv(self):
        path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.csv_path_var.set(path)

    def browse_failed_dir(self):
        path = filedialog.askdirectory(title="Select destination folder for FAILED images")
        if path:
            self.failed_dir_var.set(path)

    def browse_img_dir(self):
        path = filedialog.askdirectory(title="Select SOURCE folder containing BMP images")
        if path:
            self.img_dir_var.set(path)

    def analyze_only(self):
        self._run(analyze_only=True)

    def analyze_and_move(self):
        self._run(analyze_only=False)

    def _run(self, analyze_only=True):
        self.text.delete("1.0", tk.END)

        csv_path = self.csv_path_var.get().strip()
        failed_dir = self.failed_dir_var.get().strip()
        expected_str = self.expected_var.get().strip()

        if not csv_path or not os.path.exists(csv_path):
            messagebox.showerror(APP_TITLE, "Please select a valid CSV file.")
            return

        try:
            expected_max = int(expected_str)
        except Exception:
            messagebox.showerror(APP_TITLE, "Expected max must be an integer.")
            return

        if not analyze_only and not failed_dir:
            messagebox.showerror(APP_TITLE, "Please select a destination folder for FAILED images.")
            return

        # Determine source images folder
        if self.assume_img_dir_var.get():
            img_src_dir = os.path.dirname(csv_path)
        else:
            img_src_dir = self.img_dir_var.get().strip()
            if not img_src_dir:
                messagebox.showerror(APP_TITLE, "Please select the source images folder.")
                return
            if not os.path.isdir(img_src_dir):
                messagebox.showerror(APP_TITLE, "Invalid source images folder.")
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
            if val != val:  # NaN check
                continue
            if val < expected_max:
                under_max.append((r.get("ImageName", ""), val))

        # Output summary
        self.text.insert(tk.END, f"CSV: {csv_path}\n")
        self.text.insert(tk.END, f"Total rows: {total_rows}\n")
        self.text.insert(tk.END, f"Expected max: {expected_max}\n")
        self.text.insert(tk.END, f"Under-max count: {len(under_max)}\n\n")

        # Save a log next to CSV
        ts = time.strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(os.path.dirname(csv_path), f"failed_log_{ts}.csv")
        with open(log_path, "w", newline="", encoding="utf-8") as lf:
            w = csv.writer(lf)
            w.writerow(["ImageName", "BlobNumResults", "Moved", "Note"])

            moved_count = 0
            missing_count = 0

            for img_name, val in under_max:
                moved = ""
                note = ""

                if not analyze_only:
                    # Ensure failed dir exists
                    os.makedirs(failed_dir, exist_ok=True)

                    src = os.path.join(img_src_dir, img_name)
                    dst = os.path.join(failed_dir, img_name)
                    if os.path.exists(src):
                        try:
                            # Make sure destination subdirs exist if any
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                            shutil.move(src, dst)
                            moved = "yes"
                            moved_count += 1
                        except Exception as e:
                            moved = "no"
                            note = f"move-error: {e}"
                    else:
                        moved = "no"
                        note = "source-missing"
                        missing_count += 1

                w.writerow([img_name, val, moved, note])

        # Show details in the UI
        if under_max:
            self.text.insert(tk.END, "Under-max files:\n")
            for img_name, val in under_max[:200]:
                self.text.insert(tk.END, f"  {img_name} -> {int(val) if val==int(val) else val}\n")
            if len(under_max) > 200:
                self.text.insert(tk.END, f"... and {len(under_max)-200} more.\n")
        else:
            self.text.insert(tk.END, "All files meet the expected max.\n")

        self.text.insert(tk.END, f"\nLog written to: {log_path}\n")
        if not analyze_only:
            self.text.insert(tk.END, f"Moved: {moved_count}, Missing at source: {missing_count}\n")
            messagebox.showinfo(APP_TITLE, f"Done. Moved {moved_count} files.\nLog: {os.path.basename(log_path)}")
        else:
            messagebox.showinfo(APP_TITLE, f"Analysis complete.\nUnder-max: {len(under_max)}\nLog: {os.path.basename(log_path)}")

if __name__ == "__main__":
    App().mainloop()
