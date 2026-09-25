"""
Category Routes
Module Owner: Hamza (Backend Module)

REST API Endpoints:
GET  /api/categories
POST /api/categories
"""

from flask import Blueprint, request, jsonify, current_app
from server.repositories.category_repository import CategoryRepository

categories_bp = Blueprint("categories", __name__, url_prefix="/api/categories")


def _get_category_repo() -> CategoryRepository:
    db_path = current_app.config.get("DB_PATH")
    return CategoryRepository(db_path=db_path)


@categories_bp.route("", methods=["GET"])
def get_all_categories():
    """Retrieve all available categories."""
    try:
        repo = _get_category_repo()
        categories = repo.get_all()
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

    name = str(data["name"]).strip()
    if not name:
        return (
            jsonify({"success": False, "error": "Category name cannot be empty."}),
            400,
        )

    repo = _get_category_repo()
    existing = repo.get_by_name(name)
    if existing:
        return (
            jsonify({"success": False, "error": f"Category '{name}' already exists."}),
            409,
        )

    try:
        cat_id = repo.create(name)
        new_cat = repo.get_by_id(cat_id)
        return jsonify({"success": True, "data": new_cat}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
