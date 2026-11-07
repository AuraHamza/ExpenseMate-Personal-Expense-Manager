"""
Category Routes
Module Owner: Hamza (Backend Module)

REST API Endpoints:
GET  /api/categories
POST /api/categories
"""

from flask import Blueprint, request, jsonify, current_app
from server.services.category_service import CategoryService

categories_bp = Blueprint("categories", __name__, url_prefix="/api/categories")


def _get_category_service() -> CategoryService:
    db_path = current_app.config.get("DB_PATH")
    return CategoryService(db_path=db_path)


@categories_bp.route("", methods=["GET"])
def get_all_categories():
    """Retrieve all available categories."""
    try:
        service = _get_category_service()
        categories = service.get_all_categories()
        return jsonify({"success": True, "data": categories}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@categories_bp.route("", methods=["POST"])
def create_category():
    """Create a new custom category."""
    data = request.get_json(silent=True)
    if not data or "name" not in data:
        return (
            jsonify(
                {"success": False, "error": "Request body must contain 'name' field."}
            ),
            400,
        )

    try:
        service = _get_category_service()
        new_cat = service.create_category(data.get("name"))
        return jsonify({"success": True, "data": new_cat}), 201
    except ValueError as e:
        err_msg = str(e)
        status_code = 409 if "already exists" in err_msg.lower() else 400
        return jsonify({"success": False, "error": err_msg}), status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
