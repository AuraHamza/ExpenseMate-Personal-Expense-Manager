"""
Charts and Analytics View
Module Owner: Rafay (Frontend / Desktop Client Module)

Embeds Matplotlib charts directly in the Tkinter desktop GUI:
- Category spending distribution (Pie chart)
- Category totals / Monthly comparison (Bar chart)
- Financial overview KPI metrics (Income, Expenses, Net Savings, Savings Rate)
- Month and year selection controls
"""

from datetime import datetime
import calendar
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from client.api_client import ApiClient, ApiClientError


class ChartsView(ttk.Frame):
    """View component displaying analytics KPIs and interactive Matplotlib charts."""

    def __init__(
        self,
        parent: tk.Widget,
        api_client: ApiClient,
        **kwargs,
    ):
        super().__init__(parent, padding=10, **kwargs)
        self.api_client = api_client

        now = datetime.now()
        self.current_year = now.year
        self.current_month = now.month

        self.categories_map: Dict[str, int] = {}

        self._create_widgets()
        self.load_categories()
        self.load_analytics()

    def _create_widgets(self):
        # 1. Top Controls Bar
        control_frame = ttk.LabelFrame(self, text="Analytics Controls", padding=10)
        control_frame.pack(fill="x", padx=5, pady=(0, 10))

        ttk.Label(control_frame, text="Year:").pack(side="left", padx=(0, 4))
        self.year_var = tk.StringVar(value=str(self.current_year))
        ttk.Spinbox(
            control_frame, from_=2000, to=2099, textvariable=self.year_var, width=8
        ).pack(side="left", padx=(0, 15))

        ttk.Label(control_frame, text="Month:").pack(side="left", padx=(0, 4))
        self.month_var = tk.StringVar(
            value=f"{self.current_month:02d} - {calendar.month_name[self.current_month]}"
        )
        months = ["All Months"] + [
            f"{m:02d} - {calendar.month_name[m]}" for m in range(1, 13)
        ]
        month_combo = ttk.Combobox(
            control_frame,
            textvariable=self.month_var,
            values=months,
            state="readonly",
            width=16,
        )
        month_combo.pack(side="left", padx=(0, 15))
        month_combo.bind("<<ComboboxSelected>>", lambda e: self.load_analytics())

        ttk.Label(control_frame, text="Category:").pack(side="left", padx=(0, 4))
        self.cat_var = tk.StringVar(value="All Categories")
        self.cat_combo = ttk.Combobox(
            control_frame,
            textvariable=self.cat_var,
            values=["All Categories"],
            state="readonly",
            width=18,
        )
        self.cat_combo.pack(side="left", padx=(0, 15))
        self.cat_combo.bind("<<ComboboxSelected>>", lambda e: self.load_analytics())

        ttk.Button(
            control_frame, text="Refresh Charts", command=self.load_analytics
        ).pack(side="left")

        # 2. KPI Summary Cards
        self.kpi_frame = ttk.Frame(self)
        self.kpi_frame.pack(fill="x", padx=5, pady=(0, 10))

        self.income_lbl = self._create_kpi_card(
            self.kpi_frame, "Total Income", "$0.00", "#2e7d32", 0
        )
        self.expense_lbl = self._create_kpi_card(
            self.kpi_frame, "Total Expenses", "$0.00", "#c62828", 1
        )
        self.net_lbl = self._create_kpi_card(
            self.kpi_frame, "Net Savings", "$0.00", "#1565c0", 2
        )
        self.savings_lbl = self._create_kpi_card(
            self.kpi_frame, "Savings Rate", "0.0%", "#6a1b9a", 3
        )

        # 3. Matplotlib Canvas
        chart_container = ttk.Frame(self)
        chart_container.pack(fill="both", expand=True, padx=5, pady=5)

        self.figure = Figure(figsize=(9, 4.5), dpi=100)
        self.figure.patch.set_facecolor("#f8f9fa")

        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_container)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

    def _create_kpi_card(
        self, parent: ttk.Frame, title: str, initial_val: str, color: str, col: int
    ) -> ttk.Label:
        card = ttk.Frame(parent, relief="groove", padding=10)
        card.grid(row=0, column=col, padx=5, sticky="ew")
        parent.columnconfigure(col, weight=1)

        ttk.Label(card, text=title, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        val_lbl = ttk.Label(
            card, text=initial_val, font=("Segoe UI", 14, "bold"), foreground=color
        )
        val_lbl.pack(anchor="w", pady=(3, 0))
        return val_lbl

    def load_categories(self):
        """Fetch categories to populate category filter dropdown."""
        try:
            cats = self.api_client.get_categories()
            self.categories_map = {c["name"]: c["id"] for c in cats}
            options = ["All Categories"] + sorted(list(self.categories_map.keys()))
            self.cat_combo["values"] = options
            if self.cat_var.get() not in options:
                self.cat_var.set("All Categories")
        except ApiClientError:
            pass

    def load_analytics(self):
        """Fetch analytics report from API and re-render charts."""
        try:
            year_val = int(self.year_var.get())
        except ValueError:
            year_val = self.current_year

        month_str = self.month_var.get()
        month_val = None
        if month_str != "All Months":
            try:
                month_val = int(month_str.split(" - ")[0])
            except (ValueError, IndexError):
                month_val = None

        cat_name = self.cat_var.get()
        cat_id = (
            self.categories_map.get(cat_name)
            if cat_name and cat_name != "All Categories"
            else None
        )

        try:
            report = self.api_client.get_analytics(
                year=year_val, month=month_val, category_id=cat_id
            )
            self._update_kpi(report["summary"])
            self._render_charts(report)
        except ApiClientError as e:
            messagebox.showerror("Error", f"Failed to load analytics: {e.message}")

    def _update_kpi(self, summary: Dict[str, Any]):
        inc = summary.get("total_income", 0.0)
        exp = summary.get("total_expense", 0.0)
        net = summary.get("net_savings", 0.0)
        rate = summary.get("savings_rate", 0.0)

        self.income_lbl.config(text=f"${inc:,.2f}")
        self.expense_lbl.config(text=f"${exp:,.2f}")
        self.net_lbl.config(
            text=f"${net:,.2f}", foreground="#2e7d32" if net >= 0 else "#c62828"
        )
        self.savings_lbl.config(text=f"{rate:.1f}%")

    def _render_charts(self, report: Dict[str, Any]):
        """Render Pie and Bar charts onto the Matplotlib canvas."""
        self.figure.clear()

        distribution = report.get("distribution", {})
        labels = distribution.get("labels", [])
        values = distribution.get("values", [])

        # Subplot 1: Pie Chart (Category Spending Distribution)
        ax1 = self.figure.add_subplot(1, 2, 1)
        ax1.set_facecolor("#f8f9fa")

        if values and sum(values) > 0:
            palette = plt.cm.tab20.colors
            wedges, texts, autotexts = ax1.pie(
                values,
                labels=labels,
                autopct="%1.1f%%",
                startangle=140,
                colors=palette[: len(values)],
                textprops={"fontsize": 8},
            )
            for autotext in autotexts:
                autotext.set_fontsize(8)
            ax1.set_title(
                "Spending by Category", fontsize=11, fontweight="bold", pad=10
            )
        else:
            ax1.text(
                0.5,
                0.5,
                "No Expense Data\nfor Selected Period",
                ha="center",
                va="center",
                fontsize=10,
                color="gray",
            )
            ax1.axis("off")
            ax1.set_title(
                "Spending by Category", fontsize=11, fontweight="bold", pad=10
            )

        # Subplot 2: Bar Chart (Category Totals or Monthly Trend)
        ax2 = self.figure.add_subplot(1, 2, 2)
        ax2.set_facecolor("#f8f9fa")

        cat_spending = report.get("category_spending", [])
        active_cats = [c for c in cat_spending if c["total_spent"] > 0]

        if active_cats:
            cat_names = [c["category_name"] for c in active_cats]
            cat_amounts = [c["total_spent"] for c in active_cats]

            bars = ax2.barh(
                cat_names, cat_amounts, color="#1976d2", edgecolor="#0d47a1", height=0.6
            )
            ax2.set_title("Category Totals ($)", fontsize=11, fontweight="bold", pad=10)
            ax2.set_xlabel("Amount ($)", fontsize=9)
            ax2.tick_params(axis="both", which="major", labelsize=8)

            # Add value labels to bars
            for bar in bars:
                width = bar.get_width()
                ax2.text(
                    width + (max(cat_amounts) * 0.02),
                    bar.get_y() + bar.get_height() / 2,
                    f"${width:,.0f}",
                    va="center",
                    ha="left",
                    fontsize=8,
                )
            ax2.invert_yaxis()  # Highest at top
            ax2.grid(axis="x", linestyle="--", alpha=0.5)
        else:
            ax2.text(
                0.5,
                0.5,
                "No Category Expenses\nto Display",
                ha="center",
                va="center",
                fontsize=10,
                color="gray",
            )
            ax2.axis("off")
            ax2.set_title("Category Totals", fontsize=11, fontweight="bold", pad=10)

        self.figure.tight_layout()
        self.canvas.draw()
