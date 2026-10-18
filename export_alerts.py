"""CSV export with a standard Save As dialog."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from database import get_alert_history


def write_alerts_csv(filepath, rows) -> int:
    filepath = Path(filepath)
    with filepath.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("Time", "Severity", "Alert Message"))
        count = 0
        for ts, severity, message in rows:
            writer.writerow((ts, severity, message))
            count += 1
    return count


def export_alerts():
    path = filedialog.asksaveasfilename(
        title="Export TraceNest alert history",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        initialfile=f"tracenest_alerts_{datetime.now():%Y%m%d_%H%M%S}.csv",
    )
    if not path:
        return
    try:
        count = write_alerts_csv(path, get_alert_history(limit=100000))
        messagebox.showinfo("Export complete", f"Saved {count} alert(s) to:\n{path}")
    except Exception as exc:
        messagebox.showerror("Export failed", str(exc))
