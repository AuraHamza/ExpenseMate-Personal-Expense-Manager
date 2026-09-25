"""
Transaction Routes
Module Owner: Hamza (Backend Module)

REST API Endpoints:
GET    /api/transactions
POST   /api/transactions
GET    /api/transactions/<id>
PUT    /api/transactions/<id>
DELETE /api/transactions/<id>
"""

from flask import Blueprint, request, jsonify, current_app
from server.services.transaction_service import TransactionService

transactions_bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")


def _get_transaction_service() -> TransactionService:
    db_path = current_app.config.get("DB_PATH")
    return TransactionService(db_path=db_path)


@transactions_bp.route("", methods=["GET"])
def get_transactions():
    """Retrieve transactions with optional query filters."""
    try:
        service = _get_transaction_service()
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        category_id = request.args.get("category_id", type=int)
        trans_type = request.args.get("type")

        results = service.get_transactions(
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            trans_type=trans_type,
        )
        return jsonify({"success": True, "data": results}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@transactions_bp.route("/<int:trans_id>", methods=["GET"])
def get_transaction(trans_id: int):
    """Retrieve a single transaction by ID."""
    try:
        service = _get_transaction_service()
        transaction = service.get_transaction(trans_id)
        return jsonify({"success": True, "data": transaction}), 200
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@transactions_bp.route("", methods=["POST"])
def create_transaction():
    """Create a new income or expense transaction."""
    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify({"success": False, "error": "Request body must be valid JSON."}),
            400,
        )

    try:
        service = _get_transaction_service()
        transaction, alert = service.create_transaction(
            trans_type=data.get("type"),
            amount=data.get("amount"),
            date_str=data.get("date"),
            category_id=data.get("category_id"),
            description=data.get("description", ""),
        )
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "transaction": transaction,
                        "alert": alert,
                    },
                }
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@transactions_bp.route("/<int:trans_id>", methods=["PUT"])
def update_transaction(trans_id: int):
    """Update an existing transaction."""
    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify({"success": False, "error": "Request body must be valid JSON."}),
            400,
        )

    try:
        service = _get_transaction_service()
        updated, alert = service.update_transaction(
            transaction_id=trans_id,
            trans_type=data.get("type"),
            amount=data.get("amount"),
            date_str=data.get("date"),
            category_id=data.get("category_id"),
            description=data.get("description", ""),
        )
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "transaction": updated,
                        "alert": alert,
                    },
                }
            ),
            200,
        )
    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return jsonify({"success": False, "error": str(e)}), status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@transactions_bp.route("/<int:trans_id>", methods=["DELETE"])
def delete_transaction(trans_id: int):
    """Delete a transaction by ID."""
    try:
        service = _get_transaction_service()
        service.delete_transaction(trans_id)
        return (
            jsonify(
                {
                    "success": True,
                    "data": {"message": "Transaction deleted successfully."},
                }
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
