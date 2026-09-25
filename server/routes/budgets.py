"""
Budget Routes
Module Owner: Hamza (Backend Module)

REST API Endpoints:
GET    /api/budgets
POST   /api/budgets
GET    /api/budgets/<id>
PUT    /api/budgets/<id>
DELETE /api/budgets/<id>
"""

from flask import Blueprint, request, jsonify, current_app
from server.services.budget_service import BudgetService

budgets_bp = Blueprint("budgets", __name__, url_prefix="/api/budgets")


def _get_budget_service() -> BudgetService:
    db_path = current_app.config.get("DB_PATH")
    return BudgetService(db_path=db_path)


@budgets_bp.route("", methods=["GET"])
def get_budgets():
    """Retrieve monthly category budgets with calculated spending progress."""
    try:
        service = _get_budget_service()
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        category_id = request.args.get("category_id", type=int)

        budgets = service.get_budgets(year=year, month=month, category_id=category_id)
        return jsonify({"success": True, "data": budgets}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@budgets_bp.route("/<int:budget_id>", methods=["GET"])
def get_budget(budget_id: int):
    """Retrieve a single budget by ID."""
    try:
        service = _get_budget_service()
        budget = service.get_budget_by_id(budget_id)
        return jsonify({"success": True, "data": budget}), 200
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@budgets_bp.route("", methods=["POST"])
def set_budget():
    """Create or update (upsert) a monthly budget for a category."""
    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify({"success": False, "error": "Request body must be valid JSON."}),
            400,
        )

    try:
        service = _get_budget_service()
        budget = service.set_budget(
            category_id=data.get("category_id"),
            month=data.get("month"),
            year=data.get("year"),
            amount=data.get("amount"),
        )
        return jsonify({"success": True, "data": budget}), 201
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@budgets_bp.route("/<int:budget_id>", methods=["PUT"])
def update_budget(budget_id: int):
    """Update the budget amount by ID."""
    data = request.get_json(silent=True)
    if not data or "amount" not in data:
        return (
            jsonify(
                {"success": False, "error": "Request body must contain 'amount' field."}
            ),
            400,
        )

    try:
        service = _get_budget_service()
        updated = service.update_budget(budget_id, data["amount"])
        return jsonify({"success": True, "data": updated}), 200
    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return jsonify({"success": False, "error": str(e)}), status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@budgets_bp.route("/<int:budget_id>", methods=["DELETE"])
def delete_budget(budget_id: int):
    """Delete a budget by ID."""
    try:
        service = _get_budget_service()
        service.delete_budget(budget_id)
        return (
            jsonify(
                {"success": True, "data": {"message": "Budget deleted successfully."}}
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
