"""
Transaction History View
Module Owner: Rafay (Frontend / Desktop Client Module)

Displays transaction history in a sortable, filterable table.
Supports filtering by date range, category, and transaction type,
with options to edit and delete individual transactions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any, List
from client.api_client import ApiClient, ApiClientError
from client.ui.transaction_form import TransactionEditDialog


class HistoryView(ttk.Frame):
    """View component for viewing, filtering, editing, and deleting transactions."""

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
        self.transactions_cache: List[Dict[str, Any]] = []

        self._create_widgets()
        self.load_categories()
        self.load_transactions()

    def _create_widgets(self):
        # 1. Filter Bar
        filter_frame = ttk.LabelFrame(self, text="Filter Transactions", padding=10)
        filter_frame.pack(fill="x", padx=5, pady=(0, 10))

        # Date filters
        ttk.Label(filter_frame, text="From:").grid(
            row=0, column=0, padx=5, pady=2, sticky="w"
        )
        self.start_date_var = tk.StringVar()
        self.start_date_entry = ttk.Entry(
            filter_frame, textvariable=self.start_date_var, width=12
        )
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(filter_frame, text="To:").grid(
            row=0, column=2, padx=5, pady=2, sticky="w"
        )
        self.end_date_var = tk.StringVar()
        self.end_date_entry = ttk.Entry(
            filter_frame, textvariable=self.end_date_var, width=12
        )
        self.end_date_entry.grid(row=0, column=3, padx=5, pady=2)

        # Category filter
        ttk.Label(filter_frame, text="Category:").grid(
            row=0, column=4, padx=5, pady=2, sticky="w"
        )
        self.cat_filter_var = tk.StringVar(value="All Categories")
        self.cat_filter_combo = ttk.Combobox(
            filter_frame, textvariable=self.cat_filter_var, state="readonly", width=18
        )
        self.cat_filter_combo.grid(row=0, column=5, padx=5, pady=2)

        # Type filter
        ttk.Label(filter_frame, text="Type:").grid(
            row=0, column=6, padx=5, pady=2, sticky="w"
        )
        self.type_filter_var = tk.StringVar(value="All")
        self.type_filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.type_filter_var,
            values=["All", "expense", "income"],
            state="readonly",
            width=10,
        )
        self.type_filter_combo.grid(row=0, column=7, padx=5, pady=2)

        # Action buttons
        ttk.Button(filter_frame, text="Filter", command=self.load_transactions).grid(
            row=0, column=8, padx=6, pady=2
        )
        ttk.Button(filter_frame, text="Reset", command=self._reset_filters).grid(
            row=0, column=9, padx=4, pady=2
        )

        # 2. Table with scrollbars
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("id", "type", "amount", "date", "category", "description")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="browse"
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Type")
        self.tree.heading("amount", text="Amount ($)")
        self.tree.heading("date", text="Date")
        self.tree.heading("category", text="Category")
        self.tree.heading("description", text="Description")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("type", width=80, anchor="center")
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("date", width=100, anchor="center")
        self.tree.column("category", width=150, anchor="w")
        self.tree.column("description", width=250, anchor="w")

        # Color tags
        self.tree.tag_configure("income", foreground="#2e7d32")
        self.tree.tag_configure("expense", foreground="#c62828")

        y_scroll = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        x_scroll = ttk.Scrollbar(
            table_frame, orient="horizontal", command=self.tree.xview
        )
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        # 3. Action Toolbar at bottom
        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", padx=5, pady=(5, 0))

        self.count_label = ttk.Label(action_frame, text="0 transactions found")
        self.count_label.pack(side="left")

        ttk.Button(action_frame, text="Refresh", command=self.load_transactions).pack(
            side="right", padx=(5, 0)
        )
        ttk.Button(action_frame, text="Delete", command=self._delete_selected).pack(
            side="right", padx=(5, 0)
        )
        ttk.Button(action_frame, text="Edit", command=self._edit_selected).pack(
            side="right"
        )

    def load_categories(self):
        """Fetch categories to populate filter combo."""
        try:
            cats = self.api_client.get_categories()
            self.categories_map = {c["name"]: c["id"] for c in cats}
            options = ["All Categories"] + sorted(list(self.categories_map.keys()))
            self.cat_filter_combo["values"] = options
        except ApiClientError:
            pass

    def load_transactions(self):
        """Query transactions with current filter values."""
        start_date = self.start_date_var.get().strip() or None
        end_date = self.end_date_var.get().strip() or None

        cat_name = self.cat_filter_var.get()
        cat_id = (
            self.categories_map.get(cat_name) if cat_name != "All Categories" else None
        )

        t_type = self.type_filter_var.get()
        trans_type = None if t_type == "All" else t_type

        try:
            items = self.api_client.get_transactions(
                start_date=start_date,
                end_date=end_date,
                category_id=cat_id,
                trans_type=trans_type,
            )
            self.transactions_cache = items
            self._populate_table(items)
        except ApiClientError as e:
            messagebox.showerror("Error", f"Could not load transactions: {e.message}")

    def _populate_table(self, items: List[Dict[str, Any]]):
        """Populate treeview with transaction records."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        for t in items:
            t_type = t.get("type", "").lower()
            amt_val = float(t.get("amount", 0.0))
            amt_display = (
                f"+${amt_val:,.2f}" if t_type == "income" else f"-${amt_val:,.2f}"
            )

            self.tree.insert(
                "",
                "end",
                iid=str(t["id"]),
                values=(
                    t["id"],
                    t_type.capitalize(),
                    amt_display,
                    t.get("date", ""),
                    t.get("category_name", ""),
                    t.get("description", ""),
                ),
                tags=(t_type,),
            )

        self.count_label.config(text=f"{len(items)} transactions loaded")

    def _reset_filters(self):
        self.start_date_var.set("")
        self.end_date_var.set("")
        self.cat_filter_var.set("All Categories")
        self.type_filter_var.set("All")
        self.load_transactions()

    def _get_selected_transaction(self) -> Optional[Dict[str, Any]]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Notice", "Please select a transaction first.")
            return None
        trans_id = int(selected[0])
        for t in self.transactions_cache:
            if t["id"] == trans_id:
                return t
        return None

    def _edit_selected(self):
        t = self._get_selected_transaction()
        if not t:
            return

        def on_edited():
            self.load_transactions()
            if self.on_data_changed:
                self.on_data_changed()

        TransactionEditDialog(self, self.api_client, t, on_success=on_edited)

    def _delete_selected(self):
        t = self._get_selected_transaction()
        if not t:
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            (
                f"Are you sure you want to delete transaction #{t['id']} "
                f"(${float(t['amount']):.2f} - {t['category_name']})?"
            ),
            icon="warning",
        )
        if not confirm:
            return

        try:
            self.api_client.delete_transaction(t["id"])
            messagebox.showinfo("Success", "Transaction deleted successfully.")
            self.load_transactions()
            if self.on_data_changed:
                self.on_data_changed()
        except ApiClientError as e:
            messagebox.showerror("Error", e.message)
