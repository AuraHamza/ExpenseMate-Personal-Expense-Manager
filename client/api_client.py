"""
Client API Module
Module Owner: Rafay (Frontend / Desktop Client Module)

Centralized HTTP client communicating with the Flask backend.
The UI layer calls methods in this module exclusively, avoiding direct
HTTP or database interactions from view components.
"""

from typing import Optional, Dict, Any, List, Tuple
import requests


class ApiClientError(Exception):
    """Custom exception providing user-friendly error messages from API calls."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ApiClient:
    """Central client for ExpenseMate REST API operations."""

    def __init__(self, base_url: str = "http://127.0.0.1:5000", timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Validate and parse JSON response payload."""
        try:
            payload = response.json()
        except ValueError:
            raise ApiClientError(
                f"Server returned non-JSON response (Status {response.status_code}).",
                status_code=response.status_code,
            )

        if not response.ok or not payload.get("success", False):
            error_msg = payload.get(
                "error", f"Request failed with HTTP {response.status_code}."
            )
            raise ApiClientError(error_msg, status_code=response.status_code)

        return payload.get("data", {})

    def _request(self, method: str, path: str, **kwargs) -> Any:
        """Send HTTP request with unified error handling."""
        kwargs.setdefault("timeout", self.timeout)
        try:
            resp = self.session.request(method, self._url(path), **kwargs)
            return self._handle_response(resp)
        except requests.ConnectionError:
            raise ApiClientError(
                f"Could not connect to ExpenseMate server at {self.base_url}. "
                "Please verify that the backend server is running."
            )
        except requests.Timeout:
            raise ApiClientError("Server request timed out. Please try again.")
        except requests.RequestException as e:
            raise ApiClientError(f"Network error: {str(e)}")

    # -------------------------------------------------------------
    # System / Health
    # -------------------------------------------------------------
    def check_health(self) -> Tuple[bool, str]:
        """Check if backend server is responsive."""
        try:
            data = self._request("GET", "/api/health")
            return True, data.get("status", "healthy")
        except ApiClientError as e:
            return False, e.message

    # -------------------------------------------------------------
    # Categories
    # -------------------------------------------------------------
    def get_categories(self) -> List[Dict[str, Any]]:
        """Retrieve list of categories."""
        return self._request("GET", "/api/categories")

    def create_category(self, name: str) -> Dict[str, Any]:
        """Create a new custom category."""
        return self._request("POST", "/api/categories", json={"name": name})

    # -------------------------------------------------------------
    # Transactions
    # -------------------------------------------------------------
    def get_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category_id: Optional[int] = None,
        trans_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve transactions with optional filter criteria."""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if category_id is not None:
            params["category_id"] = category_id
        if trans_type:
            params["type"] = trans_type
        return self._request("GET", "/api/transactions", params=params)

    def get_transaction(self, trans_id: int) -> Dict[str, Any]:
        """Retrieve a single transaction by ID."""
        return self._request("GET", f"/api/transactions/{trans_id}")

    def create_transaction(
        self,
        trans_type: str,
        amount: float,
        date_str: str,
        category_id: int,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Create a new transaction.
        Returns dict containing 'transaction' and optional 'alert'.
        """
        payload = {
            "type": trans_type,
            "amount": amount,
            "date": date_str,
            "category_id": category_id,
            "description": description,
        }
        return self._request("POST", "/api/transactions", json=payload)

    def update_transaction(
        self,
        trans_id: int,
        trans_type: str,
        amount: float,
        date_str: str,
        category_id: int,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Update an existing transaction.
        Returns dict containing 'transaction' and optional 'alert'.
        """
        payload = {
            "type": trans_type,
            "amount": amount,
            "date": date_str,
            "category_id": category_id,
            "description": description,
        }
        return self._request("PUT", f"/api/transactions/{trans_id}", json=payload)

    def delete_transaction(self, trans_id: int) -> bool:
        """Delete a transaction by ID."""
        self._request("DELETE", f"/api/transactions/{trans_id}")
        return True

    # -------------------------------------------------------------
    # Budgets
    # -------------------------------------------------------------
    def get_budgets(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        category_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve budgets with calculated progress."""
        params = {}
        if year is not None:
            params["year"] = year
        if month is not None:
            params["month"] = month
        if category_id is not None:
            params["category_id"] = category_id
        return self._request("GET", "/api/budgets", params=params)

    def set_budget(
        self,
        category_id: int,
        month: int,
        year: int,
        amount: float,
    ) -> Dict[str, Any]:
        """Create or update a monthly category budget."""
        payload = {
            "category_id": category_id,
            "month": month,
            "year": year,
            "amount": amount,
        }
        return self._request("POST", "/api/budgets", json=payload)

    def update_budget(self, budget_id: int, amount: float) -> Dict[str, Any]:
        """Update an existing budget amount."""
        return self._request(
            "PUT", f"/api/budgets/{budget_id}", json={"amount": amount}
        )

    def delete_budget(self, budget_id: int) -> bool:
        """Delete a budget by ID."""
        self._request("DELETE", f"/api/budgets/{budget_id}")
        return True

    # -------------------------------------------------------------
    # Analytics
    # -------------------------------------------------------------
    def get_analytics(self, year: int, month: Optional[int] = None) -> Dict[str, Any]:
        """Retrieve complete financial report and chart data."""
        params = {"year": year}
        if month is not None:
            params["month"] = month
        return self._request("GET", "/api/analytics", params=params)

    # -------------------------------------------------------------
    # CSV Import / Export
    # -------------------------------------------------------------
    def import_csv_file(self, file_path: str) -> Dict[str, Any]:
        """Upload and import transactions from a local CSV file."""
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path, f, "text/csv")}
                resp = self.session.post(
                    self._url("/api/csv/import"),
                    files=files,
                    timeout=self.timeout,
                )
            return self._handle_response(resp)
        except FileNotFoundError:
            raise ApiClientError(f"CSV file not found: {file_path}")
        except requests.ConnectionError:
            raise ApiClientError("Failed to connect to server during CSV upload.")
        except requests.RequestException as e:
            raise ApiClientError(f"CSV upload error: {str(e)}")

    def export_csv_file(
        self,
        output_file_path: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category_id: Optional[int] = None,
        trans_type: Optional[str] = None,
    ) -> str:
        """Download transactions CSV from server and save to local disk."""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if category_id is not None:
            params["category_id"] = category_id
        if trans_type:
            params["type"] = trans_type

        try:
            resp = self.session.get(
                self._url("/api/csv/export"),
                params=params,
                timeout=self.timeout,
            )
            if not resp.ok:
                raise ApiClientError(f"CSV export failed with HTTP {resp.status_code}.")

            with open(output_file_path, "w", encoding="utf-8", newline="") as f:
                f.write(resp.text)
            return output_file_path
        except requests.RequestException as e:
            raise ApiClientError(f"CSV export error: {str(e)}")
