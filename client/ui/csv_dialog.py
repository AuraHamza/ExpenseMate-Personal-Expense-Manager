"""
CSV Import / Export Dialog & View
Module Owner: Rafay (Frontend / Desktop Client Module)

Provides interface for importing transactions from CSV files with row-level
validation reporting, and exporting filtered transactions into CSV format.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Callable, Dict
from client.api_client import ApiClient, ApiClientError


class CsvView(ttk.Frame):
    """View component for CSV import and export operations."""

    def __init__(
        self,
        parent: tk.Widget,
        api_client: ApiClient,
        on_data_changed: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, padding=15, **kwargs)
        self.api_client = api_client
        self.on_data_changed = on_data_changed

        self.categories_map: Dict[str, int] = {}
        self._create_widgets()
        self.load_categories()

    def _create_widgets(self):
        # Configure layout
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # -------------------------------------------------------------
        # Left Panel: CSV Import
        # -------------------------------------------------------------
        import_box = ttk.LabelFrame(
            self, text="Import Transactions from CSV", padding=15
        )
        import_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        import_box.columnconfigure(0, weight=1)

        info_text = (
            "Select a CSV file containing transactions.\n"
            "Required headers: type, amount, date, category\n"
            "Optional header: description\n\n"
            "Example format:\n"
            "type,amount,date,category,description\n"
            "expense,35.50,2026-09-15,Food & Dining,Dinner\n"
            "income,2500.00,2026-09-01,Salary,Monthly Pay"
        )
        ttk.Label(
            import_box, text=info_text, justify="left", font=("Consolas", 8)
        ).pack(anchor="w", pady=(0, 10))

        file_select_f = ttk.Frame(import_box)
        file_select_f.pack(fill="x", pady=5)
        file_select_f.columnconfigure(0, weight=1)

        self.file_path_var = tk.StringVar()
        ttk.Entry(file_select_f, textvariable=self.file_path_var).grid(
            row=0, column=0, sticky="ew", padx=(0, 5)
        )
        ttk.Button(file_select_f, text="Browse...", command=self._browse_csv).grid(
            row=0, column=1
        )

        ttk.Button(
            import_box, text="Import Transactions Now", command=self._import_csv
        ).pack(fill="x", pady=(10, 5))

        self.import_status_lbl = ttk.Label(
            import_box, text="", font=("Segoe UI", 9, "italic")
        )
        self.import_status_lbl.pack(anchor="w", pady=5)

        # -------------------------------------------------------------
        # Right Panel: CSV Export
        # -------------------------------------------------------------
        export_box = ttk.LabelFrame(self, text="Export Transactions to CSV", padding=15)
        export_box.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)
        export_box.columnconfigure(1, weight=1)

        ttk.Label(
            export_box, text="Filter criteria for export (leave blank for all):"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Date Range
        ttk.Label(export_box, text="From Date:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.exp_start_var = tk.StringVar()
        ttk.Entry(export_box, textvariable=self.exp_start_var).grid(
            row=1, column=1, sticky="ew", pady=5
        )

        ttk.Label(export_box, text="To Date:").grid(row=2, column=0, sticky="w", pady=5)
        self.exp_end_var = tk.StringVar()
        ttk.Entry(export_box, textvariable=self.exp_end_var).grid(
            row=2, column=1, sticky="ew", pady=5
        )

        # Category
        ttk.Label(export_box, text="Category:").grid(
            row=3, column=0, sticky="w", pady=5
        )
        self.exp_cat_var = tk.StringVar(value="All Categories")
        self.exp_cat_combo = ttk.Combobox(
            export_box, textvariable=self.exp_cat_var, state="readonly"
        )
        self.exp_cat_combo.grid(row=3, column=1, sticky="ew", pady=5)

        # Type
        ttk.Label(export_box, text="Type:").grid(row=4, column=0, sticky="w", pady=5)
        self.exp_type_var = tk.StringVar(value="All")
        ttk.Combobox(
            export_box,
            textvariable=self.exp_type_var,
            values=["All", "expense", "income"],
            state="readonly",
        ).grid(row=4, column=1, sticky="ew", pady=5)

        # Export Button
        ttk.Button(
            export_box, text="Export to CSV File...", command=self._export_csv
        ).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(20, 5))

        self.export_status_lbl = ttk.Label(
            export_box, text="", font=("Segoe UI", 9, "italic")
        )
        self.export_status_lbl.grid(row=6, column=0, columnspan=2, sticky="w", pady=5)

    def load_categories(self):
        """Load categories for export dropdown."""
        try:
            cats = self.api_client.get_categories()
            self.categories_map = {c["name"]: c["id"] for c in cats}
            self.exp_cat_combo["values"] = ["All Categories"] + sorted(
                list(self.categories_map.keys())
            )
        except ApiClientError:
            pass

    def _browse_csv(self):
        filename = filedialog.askopenfilename(
            title="Select Transactions CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if filename:
            self.file_path_var.set(filename)

    def _import_csv(self):
        filepath = self.file_path_var.get().strip()
        if not filepath:
            messagebox.showwarning("Notice", "Please select a CSV file first.")
            return

        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File does not exist: {filepath}")
            return

        try:
            self.import_status_lbl.config(text="Uploading and importing...")
            self.update_idletasks()

            res = self.api_client.import_csv_file(filepath)
            imported = res.get("imported_count", 0)
            failed = res.get("failed_count", 0)
            errors = res.get("errors", [])
            alerts = res.get("alerts", [])

            msg = (
                f"Import completed:\n"
                f"- Successfully imported: {imported} rows\n"
                f"- Failed / Skipped: {failed} rows"
            )

            if alerts:
                msg += f"\n\nBudget Alerts triggered ({len(alerts)}):"
                for a in alerts[:3]:
                    msg += f"\n• {a['message']}"

            if errors:
                msg += f"\n\nFirst {min(3, len(errors))} Error(s):"
                for err in errors[:3]:
                    msg += f"\n• Row {err['row_number']}: {err['error']}"

            self.import_status_lbl.config(text=f"Imported {imported} transactions.")
            messagebox.showinfo("Import Results", msg)

            if self.on_data_changed:
                self.on_data_changed()

        except ApiClientError as e:
            self.import_status_lbl.config(text="Import failed.")
            messagebox.showerror("Import Error", e.message)

    def _export_csv(self):
        dest_file = filedialog.asksaveasfilename(
            title="Save Exported Transactions",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile="transactions_export.csv",
        )
        if not dest_file:
            return

        start_date = self.exp_start_var.get().strip() or None
        end_date = self.exp_end_var.get().strip() or None
        cat_name = self.exp_cat_var.get()
        category_id = (
            self.categories_map.get(cat_name) if cat_name != "All Categories" else None
        )
        t_type = self.exp_type_var.get()
        trans_type = None if t_type == "All" else t_type

        try:
            self.export_status_lbl.config(text="Exporting...")
            self.update_idletasks()

            self.api_client.export_csv_file(
                output_file_path=dest_file,
                start_date=start_date,
                end_date=end_date,
                category_id=category_id,
                trans_type=trans_type,
            )

            self.export_status_lbl.config(
                text=f"Exported to {os.path.basename(dest_file)}"
            )
            messagebox.showinfo(
                "Export Successful",
                f"Transactions exported successfully to:\n{dest_file}",
            )
        except ApiClientError as e:
            self.export_status_lbl.config(text="Export failed.")
            messagebox.showerror("Export Error", e.message)
