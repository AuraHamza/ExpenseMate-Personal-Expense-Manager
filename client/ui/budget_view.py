"""
Budget View
Module Owner: Rafay (Frontend / Desktop Client Module)

Allows setting and updating monthly category budgets, and visualizes
spending thresholds against budgets with color-coded status indicators.
"""

from datetime import datetime
import calendar
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any, List
from client.api_client import ApiClient, ApiClientError


class BudgetView(ttk.Frame):
    """View component for managing monthly category budgets."""

    def __init__(
        self,
        parent: tk.Widget,
        api_client: ApiClient,
        on_data_changed: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, padding=10, **kwargs)
        self.api_client = api_client
        self.on_data_changed = on_data_changed

        self.categories_map: Dict[str, int] = {}
        self.budgets_cache: List[Dict[str, Any]] = []

        now = datetime.now()
        self.current_year = now.year
        self.current_month = now.month

        self._create_widgets()
        self.load_categories()
        self.load_budgets()

    def _create_widgets(self):
        # 1. Budget Entry / Upsert Form
        form_frame = ttk.LabelFrame(
            self, text="Set Monthly Category Budget", padding=10
        )
        form_frame.pack(fill="x", padx=5, pady=(0, 10))

        # Category
        ttk.Label(form_frame, text="Category:").grid(
            row=0, column=0, padx=5, pady=4, sticky="w"
        )
        self.cat_var = tk.StringVar()
        self.cat_combo = ttk.Combobox(
            form_frame, textvariable=self.cat_var, state="readonly", width=20
        )
        self.cat_combo.grid(row=0, column=1, padx=5, pady=4)

        # Month
        ttk.Label(form_frame, text="Month:").grid(
            row=0, column=2, padx=5, pady=4, sticky="w"
        )
        self.month_var = tk.StringVar(
            value=f"{self.current_month:02d} - {calendar.month_name[self.current_month]}"
        )
        months_list = [f"{m:02d} - {calendar.month_name[m]}" for m in range(1, 13)]
        self.month_combo = ttk.Combobox(
            form_frame,
            textvariable=self.month_var,
            values=months_list,
            state="readonly",
            width=16,
        )
        self.month_combo.grid(row=0, column=3, padx=5, pady=4)

        # Year
        ttk.Label(form_frame, text="Year:").grid(
            row=0, column=4, padx=5, pady=4, sticky="w"
        )
        self.year_var = tk.StringVar(value=str(self.current_year))
        self.year_spin = ttk.Spinbox(
            form_frame, from_=2000, to=2099, textvariable=self.year_var, width=8
        )
        self.year_spin.grid(row=0, column=5, padx=5, pady=4)

        # Amount
        ttk.Label(form_frame, text="Budget ($):").grid(
            row=0, column=6, padx=5, pady=4, sticky="w"
        )
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(
            form_frame, textvariable=self.amount_var, width=12
        )
        self.amount_entry.grid(row=0, column=7, padx=5, pady=4)

        # Save Button
        ttk.Button(form_frame, text="Save Budget", command=self._save_budget).grid(
            row=0, column=8, padx=10, pady=4
        )

        # 2. Filter & Budgets Table
        table_container = ttk.LabelFrame(
            self, text="Monthly Budgets & Spending Progress", padding=10
        )
        table_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Table filter sub-bar
        sub_bar = ttk.Frame(table_container)
        sub_bar.pack(fill="x", pady=(0, 6))

        ttk.Label(sub_bar, text="Filter Year:").pack(side="left", padx=(0, 4))
        self.filter_year_var = tk.StringVar(value=str(self.current_year))
        ttk.Spinbox(
            sub_bar, from_=2000, to=2099, textvariable=self.filter_year_var, width=7
        ).pack(side="left", padx=(0, 10))

        ttk.Label(sub_bar, text="Filter Month:").pack(side="left", padx=(0, 4))
        self.filter_month_var = tk.StringVar(value="All Months")
        filter_months = ["All Months"] + [
            f"{m:02d} - {calendar.month_name[m]}" for m in range(1, 13)
        ]
        ttk.Combobox(
            sub_bar,
            textvariable=self.filter_month_var,
            values=filter_months,
            state="readonly",
            width=14,
        ).pack(side="left", padx=(0, 10))

        ttk.Button(sub_bar, text="Filter", command=self.load_budgets).pack(
            side="left", padx=4
        )

        # Treeview table
        columns = (
            "category",
            "period",
            "budget",
            "spent",
            "remaining",
            "percentage",
            "status",
        )
        self.tree = ttk.Treeview(
            table_container, columns=columns, show="headings", selectmode="browse"
        )

        self.tree.heading("category", text="Category")
        self.tree.heading("period", text="Period")
        self.tree.heading("budget", text="Budget ($)")
        self.tree.heading("spent", text="Spent ($)")
        self.tree.heading("remaining", text="Remaining ($)")
        self.tree.heading("percentage", text="Used (%)")
        self.tree.heading("status", text="Alert Status")

        self.tree.column("category", width=180, anchor="w")
        self.tree.column("period", width=120, anchor="center")
        self.tree.column("budget", width=110, anchor="e")
        self.tree.column("spent", width=110, anchor="e")
        self.tree.column("remaining", width=110, anchor="e")
        self.tree.column("percentage", width=90, anchor="center")
        self.tree.column("status", width=120, anchor="center")

        # Color tags
        self.tree.tag_configure("normal", foreground="#2e7d32")
        self.tree.tag_configure("warning", foreground="#e65100")
        self.tree.tag_configure("exceeded", foreground="#b71c1c")

        scroll = ttk.Scrollbar(
            table_container, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # 3. Bottom controls
        bottom_bar = ttk.Frame(self)
        bottom_bar.pack(fill="x", padx=5, pady=(5, 0))

        self.info_label = ttk.Label(bottom_bar, text="0 budgets loaded")
        self.info_label.pack(side="left")

        ttk.Button(bottom_bar, text="Refresh", command=self.load_budgets).pack(
            side="right", padx=(5, 0)
        )
        ttk.Button(
            bottom_bar, text="Delete Selected", command=self._delete_selected
        ).pack(side="right")

    def load_categories(self):
        """Fetch categories to populate selection combo."""
        try:
            cats = self.api_client.get_categories()
            self.categories_map = {c["name"]: c["id"] for c in cats}
            names = list(self.categories_map.keys())
            self.cat_combo["values"] = names
            if names and not self.cat_var.get():
                self.cat_combo.current(0)
        except ApiClientError:
            pass

    def load_budgets(self):
        """Query budgets from API with filters."""
        try:
            year_val = int(self.filter_year_var.get())
        except ValueError:
            year_val = self.current_year

        month_str = self.filter_month_var.get()
        month_val = None
        if month_str != "All Months":
            try:
                month_val = int(month_str.split(" - ")[0])
            except (ValueError, IndexError):
                month_val = None

        try:
            budgets = self.api_client.get_budgets(year=year_val, month=month_val)
            self.budgets_cache = budgets
            self._populate_table(budgets)
        except ApiClientError as e:
            messagebox.showerror("Error", f"Failed to load budgets: {e.message}")

    def _populate_table(self, budgets: List[Dict[str, Any]]):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for b in budgets:
            m = b["month"]
            y = b["year"]
            m_name = calendar.month_abbr[m]
            period_str = f"{m_name} {y}"

            budget_amt = float(b.get("amount", 0.0))
            spent_amt = float(b.get("spent", 0.0))
            remaining_amt = float(b.get("remaining", 0.0))
            pct = float(b.get("percentage", 0.0))
            status = b.get("status", "normal")

            status_display = "Normal"
            tag = "normal"
            if status == "exceeded" or pct >= 100.0:
                status_display = "Exceeded (>=100%)"
                tag = "exceeded"
            elif status == "warning" or pct >= 80.0:
                status_display = "Warning (>=80%)"
                tag = "warning"

            self.tree.insert(
                "",
                "end",
                iid=str(b["id"]),
                values=(
                    b.get("category_name", ""),
                    period_str,
                    f"${budget_amt:,.2f}",
                    f"${spent_amt:,.2f}",
                    f"${remaining_amt:,.2f}",
                    f"{pct:.1f}%",
                    status_display,
                ),
                tags=(tag,),
            )

        self.info_label.config(text=f"{len(budgets)} budgets tracked")

    def _save_budget(self):
        cat_name = self.cat_var.get()
        cat_id = self.categories_map.get(cat_name)
        if not cat_id:
            messagebox.showwarning("Validation Error", "Please select a category.")
            return

        try:
            month = int(self.month_var.get().split(" - ")[0])
        except (ValueError, IndexError):
            messagebox.showwarning("Validation Error", "Please select a valid month.")
            return

        try:
            year = int(self.year_var.get().strip())
        except ValueError:
            messagebox.showwarning("Validation Error", "Please enter a valid year.")
            return

        try:
            amount = float(self.amount_var.get().strip())
            if amount < 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning(
                "Validation Error", "Budget amount must be a positive number."
            )
            return

        try:
            budget = self.api_client.set_budget(
                category_id=cat_id,
                month=month,
                year=year,
                amount=amount,
            )
            pct = budget.get("percentage", 0.0)
            if pct >= 100.0:
                msg = (
                    f"Budget saved! Notice: Spending in {cat_name} is already at "
                    f"{pct:.1f}% (${budget['spent']:.2f}/${amount:.2f})."
                )
                messagebox.showerror("Budget Alert!", msg)
            elif pct >= 80.0:
                msg = (
                    f"Budget saved! Warning: Spending in {cat_name} is already at "
                    f"{pct:.1f}% (${budget['spent']:.2f}/${amount:.2f})."
                )
                messagebox.showwarning("Budget Warning", msg)
            else:
                msg = (
                    f"Budget for {cat_name} ({calendar.month_abbr[month]} {year}) "
                    f"set to ${amount:,.2f}."
                )
                messagebox.showinfo("Success", msg)

            self.amount_var.set("")
            self.load_budgets()
            if self.on_data_changed:
                self.on_data_changed()
        except ApiClientError as e:
            messagebox.showerror("Error", e.message)

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Notice", "Please select a budget to delete.")
            return

        budget_id = int(selected[0])
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete budget #{budget_id}?",
            icon="warning",
        )
        if not confirm:
            return

        try:
            self.api_client.delete_budget(budget_id)
            messagebox.showinfo("Success", "Budget deleted successfully.")
            self.load_budgets()
            if self.on_data_changed:
                self.on_data_changed()
        except ApiClientError as e:
            messagebox.showerror("Error", e.message)
