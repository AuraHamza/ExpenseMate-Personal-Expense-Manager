"""
Flask Application Factory
Module Owner: Hamza (Backend Module)

Initializes the Flask REST API application, registers blueprints,
configures SQLite database connection, and defines common error handlers.
"""

from typing import Optional, Dict, Any
from flask import Flask, jsonify
from server.database import DEFAULT_DB_PATH, init_db
from server.routes.transactions import transactions_bp
from server.routes.categories import categories_bp
from server.routes.budgets import budgets_bp
from server.routes.analytics import analytics_bp
from server.routes.csv_io import csv_bp


def create_app(
    test_config: Optional[Dict[str, Any]] = None, db_path: Optional[str] = None
) -> Flask:
    """
    Application factory for ExpenseMate backend server.
    """
    app = Flask(__name__)

    # Default configuration
    app.config.from_mapping(
        SECRET_KEY="expensemate-dev-secret-key",
        DB_PATH=db_path or DEFAULT_DB_PATH,
        JSON_SORT_KEYS=False,
    )

    # Override with test configuration if provided
    if test_config:
        app.config.update(test_config)

    # Initialize the database schema and default categories
    active_db_path = app.config.get("DB_PATH")
    init_db(active_db_path)

    # Register Blueprints
    app.register_blueprint(transactions_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(csv_bp)

    # Health check endpoint for client readiness polling
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "status": "ok",
                    },
                }
            ),
            200,
        )

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "Resource not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Method not allowed for requested endpoint.",
                }
            ),
            405,
        )

    @app.errorhandler(500)
    def internal_error(error):
        return (
            jsonify({"success": False, "error": "Internal server error occurred."}),
            500,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    print("Starting ExpenseMate Server on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
