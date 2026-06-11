<<<<<<< HEAD
=======
# File: templates/statistical/statistical_app.py
# Nhiệm vụ:
# - Đăng ký route frontend cho module thống kê.
# - /statistical/assets lấy dữ liệu thật từ trang tài sản.
# - Bảng bảo trì lấy lỗi từ nội dung / ghi chú báo cáo.

>>>>>>> 619993c3769599db132f4ea465a37b35f7832fb3
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
    return render_template(
        "statistical/statistical_employees.html",
        **get_statistical_employees_context(request.args, get_current_user())
    )


def render_asset_statistics():
    return render_template(
        "statistical/statistical_assets.html",
        **get_statistical_assets_context(request.args, get_current_user())
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