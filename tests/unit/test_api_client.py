"""
Unit Tests for Client ApiClient
Module: tests/unit/test_api_client.py
"""

from unittest.mock import MagicMock, patch
import pytest
import requests
from client.api_client import ApiClient, ApiClientError


def test_api_client_health_success():
    client = ApiClient(base_url="http://127.0.0.1:5000")
    with patch.object(client.session, "request") as mock_req:
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True, "data": {"status": "ok"}}
        mock_req.return_value = mock_resp

        ok, status = client.check_health()
        assert ok is True
        assert status == "ok"


def test_api_client_connection_error():
    client = ApiClient(base_url="http://127.0.0.1:5000")
    with patch.object(
        client.session, "request", side_effect=requests.ConnectionError("Refused")
    ):
        ok, msg = client.check_health()
        assert ok is False
        assert "Could not connect to ExpenseMate server" in msg


def test_api_client_timeout_error():
    client = ApiClient(base_url="http://127.0.0.1:5000")
    with patch.object(
        client.session, "request", side_effect=requests.Timeout("Timed out")
    ):
        with pytest.raises(ApiClientError, match="Server request timed out"):
            client.get_categories()


def test_api_client_http_error_response():
    client = ApiClient(base_url="http://127.0.0.1:5000")
    with patch.object(client.session, "request") as mock_req:
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 400
        mock_resp.json.return_value = {
            "success": False,
            "error": "Amount must be positive",
        }
        mock_req.return_value = mock_resp

        with pytest.raises(ApiClientError, match="Amount must be positive") as exc_info:
            client.create_transaction("expense", -50.0, "2026-09-01", 1)
        assert exc_info.value.status_code == 400


def test_api_client_non_json_response():
    client = ApiClient(base_url="http://127.0.0.1:5000")
    with patch.object(client.session, "request") as mock_req:
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("No JSON")
        mock_req.return_value = mock_resp

        with pytest.raises(ApiClientError, match="non-JSON response"):
            client.get_categories()
