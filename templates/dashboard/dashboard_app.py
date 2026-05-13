from flask import jsonify, render_template, request

from .dashboard_backend import get_dashboard_overview_data


def register_dashboard_routes(app):
    @app.route("/")
    def dashboard_overview():
        return render_template("dashboard/overview.html")

    @app.route("/api/dashboard/overview", methods=["GET"])
    def dashboard_overview_api():
        limit = request.args.get("limit", 4, type=int)

        data = get_dashboard_overview_data(limit=limit)

        return jsonify(data), 200