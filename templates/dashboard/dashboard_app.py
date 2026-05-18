from flask import jsonify, render_template, request, redirect, url_for, flash, session

from .dashboard_backend import get_dashboard_overview_data


def get_current_user():
    return session.get("user") or session.get("current_user") or {}


def is_logged_in():
    return bool(get_current_user())


def user_can(module_key, action):
    user = get_current_user()
    role = user.get("role")

    if user.get("is_admin") or role == "ADMIN":
        return True

    # Dashboard là trang chính sau login.
    # Nếu session can chưa kịp cập nhật thì vẫn cho role hợp lệ vào dashboard.
    if module_key == "dashboard" and action == "view":
        return role in ["ADMIN", "QUAN_LY", "NHAN_VIEN"]

    can = user.get("can") or {}

    return can.get(module_key, {}).get(action) is True


def require_login_page():
    if not is_logged_in():
        return redirect(url_for("login_page"))

    return None


def require_dashboard_permission_page():
    login_redirect = require_login_page()

    if login_redirect:
        return login_redirect

    if not user_can("dashboard", "view"):
        flash("Bạn không có quyền xem dashboard.", "danger")
        return redirect(url_for("login_page"))

    return None


def dashboard_context():
    return {
        "current_user": get_current_user(),
        "can_view_dashboard": user_can("dashboard", "view"),
        "can_view_asset": user_can("assets", "view"),
        "can_view_user": user_can("users", "view"),
        "can_view_assign": user_can("assign", "view"),
        "can_view_report": user_can("reports", "view"),
    }


def register_dashboard_routes(app):
    @app.route("/")
    def dashboard_overview():
        permission_redirect = require_dashboard_permission_page()

        if permission_redirect:
            return permission_redirect

        return render_template(
            "dashboard/overview.html",
            **dashboard_context(),
        )

    @app.route("/api/dashboard/overview", methods=["GET"])
    def dashboard_overview_api():
        if not is_logged_in():
            return jsonify({
                "success": False,
                "message": "Bạn chưa đăng nhập",
                "stats": {},
                "recent_assets": [],
            }), 401

        if not user_can("dashboard", "view"):
            return jsonify({
                "success": False,
                "message": "Bạn không có quyền xem dashboard",
                "stats": {},
                "recent_assets": [],
            }), 403

        limit = request.args.get("limit", 4, type=int)

        data = get_dashboard_overview_data(limit=limit)

        status_code = data.get("status_code")

        if status_code == 401:
            session.clear()

            return jsonify({
                "success": False,
                "message": "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
                "stats": {},
                "recent_assets": [],
            }), 401

        if status_code == 403:
            return jsonify({
                "success": False,
                "message": data.get("message", "Bạn không có quyền xem dữ liệu dashboard"),
                "stats": data.get("stats", {}),
                "recent_assets": data.get("recent_assets", []),
            }), 403

        return jsonify({
            "success": True,
            "message": "Lấy dữ liệu dashboard thành công",
            "stats": data.get("stats", {}),
            "recent_assets": data.get("recent_assets", []),
            "scope": data.get("scope", {}),
        }), 200