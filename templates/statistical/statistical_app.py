# File: statistical_app.py
# File này chỉ đăng ký route frontend cho module statistical
# Logic gọi API backend nằm trong statistical_backend.py

from flask import render_template, request, session

from templates.statistical.statistical_backend import (
    get_statistical_overview_context,
    get_statistical_employees_context,
    get_statistical_assets_context,
    get_statistical_assign_context,
    get_statistical_report_context,
)


def get_current_user():
    return (
        session.get("user")
        or session.get("current_user")
        or session.get("auth_user")
        or {}
    )


def register_statistical_routes(app):

    @app.route("/statistical")
    def statistics_page():
        context = get_statistical_overview_context(
            args=request.args,
            current_user=get_current_user(),
        )

        return render_template(
            "statistical/statistical.html",
            statistical_template="statistical/statistical_overview.html",
            **context
        )

    @app.route("/statistical/overview")
    def statistical_overview():
        context = get_statistical_overview_context(
            args=request.args,
            current_user=get_current_user(),
        )

        return render_template(
            "statistical/statistical.html",
            statistical_template="statistical/statistical_overview.html",
            **context
        )

    @app.route("/statistical/employees")
    def statistical_employees():
        context = get_statistical_employees_context(
            args=request.args,
            current_user=get_current_user(),
        )

        return render_template(
            "statistical/statistical_employees.html",
            **context
        )

    @app.route("/statistical/assets")
    def statistical_assets():
        context = get_statistical_assets_context(
            args=request.args,
            current_user=get_current_user(),
        )

        return render_template(
            "statistical/statistical_assets.html",
            **context
        )

    @app.route("/statistical/assign")
    def statistical_assign():
        context = get_statistical_assign_context(
            args=request.args,
            current_user=get_current_user(),
        )

        return render_template(
            "statistical/statistical_assign.html",
            **context
        )

    @app.route("/statistical/report")
    def statistical_report():
        context = get_statistical_report_context(
            args=request.args,
            current_user=get_current_user(),
        )

        return render_template(
            "statistical/statistical_report.html",
            **context
        )