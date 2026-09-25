"""
CSV Import / Export Routes
Module Owner: Hamza (Backend Module)

REST API Endpoints:
POST /api/csv/import
GET  /api/csv/export
"""

from flask import Blueprint, request, jsonify, Response, current_app
from server.services.csv_service import CsvService

csv_bp = Blueprint("csv_io", __name__, url_prefix="/api/csv")


def _get_csv_service() -> CsvService:
    db_path = current_app.config.get("DB_PATH")
    return CsvService(db_path=db_path)


@csv_bp.route("/import", methods=["POST"])
def import_csv():
    """
    Import transactions from CSV.
    Supports multipart/form-data upload or JSON with 'csv_content'.
    """
    csv_text = None

    if "file" in request.files:
        uploaded_file = request.files["file"]
        if uploaded_file.filename == "":
            return jsonify({"success": False, "error": "No file selected."}), 400
        try:
            csv_text = uploaded_file.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Invalid file encoding. UTF-8 required.",
                    }
                ),
                400,
            )
    elif request.is_json:
        data = request.get_json(silent=True) or {}
        csv_text = data.get("csv_content")
    else:
        # Check raw text data
        raw_data = request.get_data(as_text=True)
        if raw_data:
            csv_text = raw_data

    if not csv_text or not csv_text.strip():
        return jsonify({"success": False, "error": "No CSV content provided."}), 400

    try:
        service = _get_csv_service()
        result = service.import_transactions_from_csv(csv_text)
        return jsonify({"success": True, "data": result}), 200
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@csv_bp.route("/export", methods=["GET"])
def export_csv():
    """Export transactions to CSV format."""
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        category_id = request.args.get("category_id", type=int)
        trans_type = request.args.get("type")

        service = _get_csv_service()
        csv_data = service.export_transactions_to_csv(
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            trans_type=trans_type,
        )

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=transactions.csv",
                "Content-Type": "text/csv; charset=utf-8",
            },
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
