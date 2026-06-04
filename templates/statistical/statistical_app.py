# File: statistical_app.py
# Nhiệm vụ:
# - Đăng ký route frontend cho module thống kê.
# - Hiện tại module statistical chỉ làm thống kê nhân viên.
# - Các route cũ như /overview, /assets, /assign, /report sẽ redirect về /statistical/employees
#   để tránh lỗi nếu frontend/sidebar cũ vẫn còn link.

from flask import render_template, request, session, redirect, url_for

from templates.statistical.statistical_backend import (
    get_statistical_employees_context,
)


# Lấy user hiện tại từ session.
# Viết nhiều key để phù hợp với các cách lưu session khác nhau trong project.
def get_current_user():
    return (
        session.get("user")
        or session.get("current_user")
        or session.get("auth_user")
        or {}
    )


# Đăng ký route frontend cho trang thống kê nhân viên
def register_statistical_routes(app):

    # Trang gốc /statistical sẽ tự chuyển về trang thống kê nhân viên
    @app.route("/statistical")
    def statistics_page():
        return redirect(url_for("statistical_employees"))

    # Giữ route /statistical/overview để tránh lỗi link cũ
    # Nhưng hiện tại không còn thống kê doanh thu/tài chính nữa
    @app.route("/statistical/overview")
    def statistical_overview():
        return redirect(url_for("statistical_employees"))

    # Route chính của module thống kê nhân viên
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

    # Các route dưới đây tạm redirect về nhân viên
    # vì hiện tại bạn chưa làm thống kê tài sản/cấp phát/báo cáo
    @app.route("/statistical/assets")
    def statistical_assets():
        return redirect(url_for("statistical_employees"))

    @app.route("/statistical/assign")
    def statistical_assign():
        return redirect(url_for("statistical_employees"))

    @app.route("/statistical/report")
    def statistical_report():
        return redirect(url_for("statistical_employees"))