# File: templates/statistical/statistical_app.py

from flask import render_template, request, session, redirect, url_for

from templates.statistical.statistical_backend import (
    get_statistical_assets_context,
    get_statistical_employees_context,
)


def get_current_user():
    return (
        session.get("user")
        or session.get("current_user")
        or session.get("auth_user")
        or {}
    )


def render_employee_statistics():
    context = get_statistical_employees_context(
        args=request.args,
        current_user=get_current_user(),
    )

    return render_template(
        "statistical/statistical_employees.html",
        **context
    )


def render_asset_statistics():
    context = get_statistical_assets_context(
        args=request.args,
        current_user=get_current_user(),
    )

    return render_template(
        "statistical/statistical_assets.html",
        **context
    )


def register_statistical_routes(app):

    @app.route("/statistical")
    def statistics_page():
        return redirect(url_for("statistical_employees"))

    @app.route("/statistical/overview")
    def statistical_overview():
        return redirect(url_for("statistical_employees"))

    @app.route("/statistical/employees")
    def statistical_employees():
        return render_employee_statistics()

    @app.route("/statistical/assets")
    def statistical_assets():
        return render_asset_statistics()

    @app.route("/statistical/assign")
    def statistical_assign():
        return redirect(url_for("statistical_employees"))

    @app.route("/statistical/report")
    def statistical_report():
        return redirect(url_for("statistical_employees"))