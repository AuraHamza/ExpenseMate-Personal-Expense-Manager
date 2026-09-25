"""
Analytics Routes
Module Owner: Hamza (Backend Module)

REST API Endpoints:
GET /api/analytics?year=YYYY&month=M
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from server.services.analytics_service import AnalyticsService

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


def _get_analytics_service() -> AnalyticsService:
    db_path = current_app.config.get("DB_PATH")
    return AnalyticsService(db_path=db_path)


@analytics_bp.route("", methods=["GET"])
def get_analytics():
    """Retrieve financial summary, category breakdowns, and monthly trends."""
    now = datetime.now()
    year = request.args.get("year", default=now.year, type=int)
    month = request.args.get("month", default=None, type=int)

    if month is not None and (month < 1 or month > 12):
        return (
            jsonify(
                {"success": False, "error": "Month parameter must be between 1 and 12."}
            ),
            400,
        )

    try:
        service = _get_analytics_service()
        report = service.get_financial_summary(year=year, month=month)
        return jsonify({"success": True, "data": report}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
