"""
Main Desktop Application Window
Module Owner: Rafay (Frontend / Desktop Client Module)

Integrates all GUI views into a tabbed desktop application:
1. Add Transaction
2. Transaction History
3. Monthly Budgets
4. Analytics & Charts
5. CSV Import & Export
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from client.api_client import ApiClient
from client.ui.transaction_form import TransactionForm
from client.ui.history_view import HistoryView
from client.ui.budget_view import BudgetView
from client.ui.charts_view import ChartsView
from client.ui.csv_dialog import CsvView


class MainWindow(tk.Tk):
    """Primary application window for ExpenseMate."""

    def __init__(self, api_client: Optional[ApiClient] = None):
        super().__init__()

        self.api_client = api_client or ApiClient()

        self.title("ExpenseMate — Personal Expense Manager")
        self.geometry("1020x680")
        self.minsize(850, 550)

        self._setup_styles()
        self._create_header()
        self._create_tabs()
        self._create_status_bar()

        # Check server connectivity on startup
        self.after(500, self.check_connection)

    def _setup_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#1a237e"
        )
        style.configure("SubHeader.TLabel", font=("Segoe UI", 9), foreground="#555555")
        style.configure("Status.TLabel", font=("Segoe UI", 8), foreground="#444444")
        style.configure("TNotebook.Tab", padding=[12, 6], font=("Segoe UI", 10, "bold"))

    def _create_header(self):
        header_frame = ttk.Frame(self, padding=(15, 10, 15, 5))
        header_frame.pack(fill="x")

        title_lbl = ttk.Label(header_frame, text="ExpenseMate", style="Header.TLabel")
        title_lbl.pack(anchor="w")

        sub_text = (
            "Personal Expense Manager | Client Module: Rafay | Server Module: Hamza"
        )
        sub_lbl = ttk.Label(header_frame, text=sub_text, style="SubHeader.TLabel")
        sub_lbl.pack(anchor="w")

        sep = ttk.Separator(self, orient="horizontal")
        sep.pack(fill="x", padx=10, pady=(5, 5))

    def _create_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        # Tab 1: Add Transaction
        add_trans_tab = ttk.Frame(self.notebook, padding=15)
        self.trans_form = TransactionForm(
            add_trans_tab,
            api_client=self.api_client,
            on_success=self.on_data_modified,
        )
        self.trans_form.pack(fill="x", expand=False)
        self.notebook.add(add_trans_tab, text="  Add Transaction  ")

        # Tab 2: Transaction History
        self.history_view = HistoryView(
            self.notebook,
            api_client=self.api_client,
            on_data_changed=self.on_data_modified,
        )
        self.notebook.add(self.history_view, text="  Transaction History  ")

        # Tab 3: Monthly Budgets
        self.budget_view = BudgetView(
            self.notebook,
            api_client=self.api_client,
            on_data_changed=self.on_data_modified,
        )
        self.notebook.add(self.budget_view, text="  Monthly Budgets  ")

        # Tab 4: Analytics & Charts
        self.charts_view = ChartsView(
            self.notebook,
            api_client=self.api_client,
        )
        self.notebook.add(self.charts_view, text="  Analytics & Charts  ")

        # Tab 5: CSV Import / Export
        self.csv_view = CsvView(
            self.notebook,
            api_client=self.api_client,
            on_data_changed=self.on_data_modified,
        )
        self.notebook.add(self.csv_view, text="  CSV Import / Export  ")

        # Bind tab change event to refresh active tab
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_switched)

    def _create_status_bar(self):
        status_frame = ttk.Frame(self, relief="sunken", padding=(10, 4))
        status_frame.pack(fill="x", side="bottom")

        self.server_status_lbl = ttk.Label(
            status_frame,
            text="Checking server status...",
            style="Status.TLabel",
        )
        self.server_status_lbl.pack(side="left")

        retry_btn = ttk.Button(
            status_frame, text="Ping Server", command=self.check_connection, width=12
        )
        retry_btn.pack(side="right")

    def check_connection(self):
        """Check if Flask backend is alive."""
        ok, msg = self.api_client.check_health()
        if ok:
            self.server_status_lbl.config(
                text=f"● Server Online: {self.api_client.base_url} (Health: OK)",
                foreground="#2e7d32",
            )
        else:
            self.server_status_lbl.config(
                text=f"○ Server Offline: Cannot reach {self.api_client.base_url}",
                foreground="#c62828",
            )

    def on_data_modified(self):
        """Called whenever data is added, edited, deleted, or imported."""
        # Refresh current active view
        self._refresh_current_tab()

    def _on_tab_switched(self, event):
        """Auto-refresh the selected tab's data."""
        self._refresh_current_tab()

    def _refresh_current_tab(self):
        selected_idx = self.notebook.index(self.notebook.select())
        if selected_idx == 0:
            self.trans_form.refresh_categories()
        elif selected_idx == 1:
            self.history_view.load_categories()
            self.history_view.load_transactions()
        elif selected_idx == 2:
            self.budget_view.load_categories()
            self.budget_view.load_budgets()
        elif selected_idx == 3:
            self.charts_view.load_categories()
            self.charts_view.load_analytics()
        elif selected_idx == 4:
            self.csv_view.load_categories()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
