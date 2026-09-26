"""
Transaction Form View
Module Owner: Rafay (Frontend / Desktop Client Module)

Provides interface for adding and editing income and expense transactions.
Supports category selection, quick custom category creation, and displays
automatic budget alert notifications received from the server.
"""

from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Callable, Dict, Any, Tuple
from client.api_client import ApiClient, ApiClientError


class TransactionForm(ttk.LabelFrame):
    """Reusable transaction form component (embeddable in main window or tabs)."""

    def __init__(
        self,
        parent: tk.Widget,
        api_client: ApiClient,
        on_success: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, text="Add New Transaction", padding=15, **kwargs)
        self.api_client = api_client
        self.on_success = on_success

        self.categories_map: Dict[str, int] = {}
        self._create_widgets()
        self.refresh_categories()

    def _create_widgets(self):
        # Configure grid columns
        self.columnconfigure(1, weight=1)

        # 1. Type
        ttk.Label(self, text="Transaction Type:").grid(
            row=0, column=0, sticky="w", pady=6
        )
        self.type_var = tk.StringVar(value="expense")
        type_frame = ttk.Frame(self)
        type_frame.grid(row=0, column=1, sticky="w", pady=6)
        ttk.Radiobutton(
            type_frame, text="Expense", value="expense", variable=self.type_var
        ).pack(side="left", padx=(0, 15))
        ttk.Radiobutton(
            type_frame, text="Income", value="income", variable=self.type_var
        ).pack(side="left")

        # 2. Amount
        ttk.Label(self, text="Amount ($):").grid(row=1, column=0, sticky="w", pady=6)
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(self, textvariable=self.amount_var, width=30)
        self.amount_entry.grid(row=1, column=1, sticky="ew", pady=6)

        # 3. Date
        ttk.Label(self, text="Date (YYYY-MM-DD):").grid(
            row=2, column=0, sticky="w", pady=6
        )
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_entry = ttk.Entry(self, textvariable=self.date_var, width=30)
        self.date_entry.grid(row=2, column=1, sticky="ew", pady=6)

        # 4. Category
        ttk.Label(self, text="Category:").grid(row=3, column=0, sticky="w", pady=6)
        cat_frame = ttk.Frame(self)
        cat_frame.grid(row=3, column=1, sticky="ew", pady=6)
        cat_frame.columnconfigure(0, weight=1)

        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            cat_frame, textvariable=self.category_var, state="readonly"
        )
        self.category_combo.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.add_cat_btn = ttk.Button(
            cat_frame, text="+ New", width=7, command=self._add_new_category
        )
        self.add_cat_btn.grid(row=0, column=1, sticky="e")

        # 5. Description
        ttk.Label(self, text="Description:").grid(row=4, column=0, sticky="w", pady=6)
        self.desc_var = tk.StringVar()
        self.desc_entry = ttk.Entry(self, textvariable=self.desc_var, width=30)
        self.desc_entry.grid(row=4, column=1, sticky="ew", pady=6)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=5, column=0, columnspan=2, sticky="e", pady=(15, 0))

        self.clear_btn = ttk.Button(btn_frame, text="Clear", command=self.clear_form)
        self.clear_btn.pack(side="right", padx=(5, 0))

        self.submit_btn = ttk.Button(
            btn_frame, text="Save Transaction", command=self._submit
        )
        self.submit_btn.pack(side="right")

    def refresh_categories(self):
        """Fetch categories from API and populate dropdown."""
        try:
            cats = self.api_client.get_categories()
            self.categories_map = {c["name"]: c["id"] for c in cats}
            cat_names = list(self.categories_map.keys())
            self.category_combo["values"] = cat_names
            if cat_names and not self.category_var.get():
                self.category_combo.current(0)
        except ApiClientError as e:
            messagebox.showerror(
                "Network Error", f"Failed to load categories: {e.message}"
            )

    def _add_new_category(self):
        """Prompt user for a new category name and register it via API."""
        name = simpledialog.askstring(
            "Add Category", "Enter new category name:", parent=self
        )
        if name is not None:
            clean_name = name.strip()
            if not clean_name:
                messagebox.showerror("Error", "Category name cannot be empty.")
                return
            if any(c.lower() == clean_name.lower() for c in self.categories_map.keys()):
                messagebox.showerror(
                    "Error", f"Category '{clean_name}' already exists."
                )
                return
            try:
                created = self.api_client.create_category(clean_name)
                self.refresh_categories()
                self.category_var.set(created["name"])
                messagebox.showinfo(
                    "Success", f"Category '{created['name']}' created successfully."
                )
            except ApiClientError as e:
                messagebox.showerror("Error", e.message)

    def _validate_form_inputs(self) -> Optional[Tuple[float, str, int]]:
        """Validate form fields; return (amount, date_str, cat_id) or None on failure."""
        amount_str = self.amount_var.get().strip()
        date_str = self.date_var.get().strip()
        cat_name = self.category_var.get()

        if not amount_str:
            messagebox.showwarning("Validation Error", "Please enter an amount.")
            return None

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning(
                "Validation Error", "Amount must be a positive number."
            )
            return None

        if not date_str:
            messagebox.showwarning(
                "Validation Error", "Please enter a valid date (YYYY-MM-DD)."
            )
            return None

        cat_id = self.categories_map.get(cat_name)
        if not cat_id:
            messagebox.showwarning("Validation Error", "Please select a category.")
            return None

        return amount, date_str, cat_id

    def _handle_transaction_alert(self, alert: Optional[Dict[str, Any]]) -> None:
        """Show an appropriate dialog for budget alert or success message."""
        if alert and alert.get("has_alert"):
            level = alert.get("level", "WARNING")
            msg = alert.get("message", "")
            if level == "ALERT":
                messagebox.showerror("Budget Limit Exceeded!", msg)
            else:
                messagebox.showwarning("Budget Warning (80% reached)", msg)
        else:
            messagebox.showinfo("Success", "Transaction recorded successfully.")

    def _submit(self):
        """Validate and dispatch transaction creation to API."""
        validated = self._validate_form_inputs()
        if validated is None:
            return
        amount, date_str, cat_id = validated

        try:
            result = self.api_client.create_transaction(
                trans_type=self.type_var.get(),
                amount=amount,
                date_str=date_str,
                category_id=cat_id,
                description=self.desc_var.get().strip(),
            )
            self._handle_transaction_alert(result.get("alert"))
            self.clear_form()
            if self.on_success:
                self.on_success()
        except ApiClientError as e:
            messagebox.showerror("Error", e.message)

    def clear_form(self):
        """Reset inputs to defaults."""
        self.amount_var.set("")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.desc_var.set("")


class TransactionEditDialog(tk.Toplevel):
    """Modal dialog to edit an existing transaction."""

    def __init__(
        self,
        parent: tk.Widget,
        api_client: ApiClient,
        transaction: Dict[str, Any],
        on_success: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.title(f"Edit Transaction #{transaction['id']}")
        self.geometry("450x320")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.api_client = api_client
        self.transaction = transaction
        self.on_success = on_success
        self.categories_map: Dict[str, int] = {}

        self._create_widgets()
        self._populate_fields()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        # Type
        ttk.Label(frame, text="Type:").grid(row=0, column=0, sticky="w", pady=6)
        self.type_var = tk.StringVar()
        type_f = ttk.Frame(frame)
        type_f.grid(row=0, column=1, sticky="w", pady=6)
        ttk.Radiobutton(
            type_f, text="Expense", value="expense", variable=self.type_var
        ).pack(side="left", padx=(0, 15))
        ttk.Radiobutton(
            type_f, text="Income", value="income", variable=self.type_var
        ).pack(side="left")

        # Amount
        ttk.Label(frame, text="Amount ($):").grid(row=1, column=0, sticky="w", pady=6)
        self.amount_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.amount_var).grid(
            row=1, column=1, sticky="ew", pady=6
        )

        # Date
        ttk.Label(frame, text="Date (YYYY-MM-DD):").grid(
            row=2, column=0, sticky="w", pady=6
        )
        self.date_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.date_var).grid(
            row=2, column=1, sticky="ew", pady=6
        )

        # Category
        ttk.Label(frame, text="Category:").grid(row=3, column=0, sticky="w", pady=6)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            frame, textvariable=self.category_var, state="readonly"
        )
        self.category_combo.grid(row=3, column=1, sticky="ew", pady=6)

        # Description
        ttk.Label(frame, text="Description:").grid(row=4, column=0, sticky="w", pady=6)
        self.desc_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.desc_var).grid(
            row=4, column=1, sticky="ew", pady=6
        )

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, sticky="e", pady=(15, 0))
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(
            side="right", padx=(5, 0)
        )
        ttk.Button(btn_frame, text="Update", command=self._save).pack(side="right")

    def _populate_fields(self):
        try:
            cats = self.api_client.get_categories()
            self.categories_map = {c["name"]: c["id"] for c in cats}
            self.category_combo["values"] = list(self.categories_map.keys())
        except ApiClientError:
            pass

        self.type_var.set(self.transaction.get("type", "expense"))
        self.amount_var.set(str(self.transaction.get("amount", "")))
        self.date_var.set(str(self.transaction.get("date", "")))
        self.category_var.set(str(self.transaction.get("category_name", "")))
        self.desc_var.set(str(self.transaction.get("description", "")))

    def _save(self):
        try:
            amount = float(self.amount_var.get().strip())
        except ValueError:
            messagebox.showwarning(
                "Validation Error", "Amount must be a positive number.", parent=self
            )
            return

        cat_id = self.categories_map.get(self.category_var.get())
        if not cat_id:
            messagebox.showwarning(
                "Validation Error", "Please select a category.", parent=self
            )
            return

        try:
            result = self.api_client.update_transaction(
                trans_id=self.transaction["id"],
                trans_type=self.type_var.get(),
                amount=amount,
                date_str=self.date_var.get().strip(),
                category_id=cat_id,
                description=self.desc_var.get().strip(),
            )

            alert = result.get("alert")
            if alert and alert.get("has_alert"):
                msg = alert.get("message", "")
                if alert.get("level") == "ALERT":
                    messagebox.showerror("Budget Exceeded", msg, parent=self)
                else:
                    messagebox.showwarning("Budget Warning", msg, parent=self)

            messagebox.showinfo(
                "Success", "Transaction updated successfully.", parent=self
            )
            if self.on_success:
                self.on_success()
            self.destroy()
        except ApiClientError as e:
            messagebox.showerror("Error", e.message, parent=self)
