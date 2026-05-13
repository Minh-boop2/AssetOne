from datetime import timedelta
from flask import render_template, request, redirect, url_for, session

from .login_backend import (
    login_user_from_form,
    forgot_password_from_form,
    verify_reset_token,
    reset_password_from_form,
)


ROLE_LABELS = {
    "ADMIN": "Quản trị hệ thống",
    "QUAN_LY": "Quản lý",
    "NHAN_VIEN": "Nhân viên",
}

DEFAULT_AVATAR_URL = "/static/imgages/default-avatar.jpg"


def register_login_routes(app):
    app.permanent_session_lifetime = timedelta(days=7)

    @app.route('/welcome')
    def welcome_page():
        return redirect(url_for('login_page'))

    @app.route('/login', methods=['GET', 'POST'])
    def login_page():
        if session.get("user"):
            return redirect(url_for('dashboard_overview'))

        if request.method == 'POST':
            success, message, user = login_user_from_form(request.form)

            if not success:
                session["login_error"] = "Sai tài khoản hoặc mật khẩu"
                session["login_email"] = request.form.get("email", "")
                session["login_remember"] = True if request.form.get("remember") else False

                return redirect(url_for('login_page'))

            session.pop("login_error", None)
            session.pop("login_email", None)
            session.pop("login_remember", None)

            role = user.get("role")

            if role not in ROLE_LABELS:
                session.clear()
                session["login_error"] = "Tài khoản chưa được phân quyền hợp lệ"
                return redirect(url_for('login_page'))

            session["user"] = {
                "id": str(user.get("id") or user.get("_id") or ""),
                "employee_code": user.get("employee_code"),
                "email": user.get("email"),
                "full_name": user.get("full_name") or "Người dùng",
                "phone": user.get("phone"),
                "department": user.get("department"),
                "floor": user.get("floor"),
                "role": role,
                "role_label": ROLE_LABELS.get(role, role),
                "status": user.get("status"),
                "avatar_url": user.get("avatar_url") or DEFAULT_AVATAR_URL,
            }

            if request.form.get("remember"):
                session.permanent = True
            else:
                session.permanent = False

            return redirect(url_for('dashboard_overview'))

        login_error = session.pop("login_error", None)
        login_email = session.pop("login_email", "")
        login_remember = session.pop("login_remember", False)
        login_success = session.pop("login_success", None)

        return render_template(
            'login/login_overview.html',
            login_error=login_error,
            login_email=login_email,
            login_remember=login_remember,
            login_success=login_success
        )

    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        if request.method == 'POST':
            success, message, data = forgot_password_from_form(request.form)

            session["forgot_email"] = request.form.get("email", "")

            if not success:
                session["forgot_error"] = message
                session.pop("forgot_success", None)
                return redirect(url_for('forgot_password'))

            session["forgot_success"] = "Đã gửi link đặt lại mật khẩu qua Gmail. Vui lòng kiểm tra hộp thư."
            session.pop("forgot_error", None)

            return redirect(url_for('forgot_password'))

        forgot_email = session.pop("forgot_email", "")
        forgot_error = session.pop("forgot_error", None)
        forgot_success = session.pop("forgot_success", None)

        return render_template(
            'login/forgot_password.html',
            reset_mode=False,
            forgot_email=forgot_email,
            forgot_error=forgot_error,
            forgot_success=forgot_success
        )

    @app.route('/reset-password/<string:token>', methods=['GET', 'POST'])
    def reset_password_page(token):
        if request.method == 'POST':
            success, message, data = reset_password_from_form(token, request.form)

            if not success:
                session["reset_error"] = message
                return redirect(url_for('reset_password_page', token=token))

            session.pop("reset_error", None)
            session["login_success"] = "Đặt lại mật khẩu thành công. Vui lòng đăng nhập lại."

            return redirect(url_for('login_page'))

        token_success, token_message, data = verify_reset_token(token)

        if not token_success:
            return render_template(
                'login/forgot_password.html',
                reset_mode=True,
                token=token,
                token_error=token_message,
                reset_error=None
            )

        reset_error = session.pop("reset_error", None)

        return render_template(
            'login/forgot_password.html',
            reset_mode=True,
            token=token,
            token_error=None,
            reset_error=reset_error
        )

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login_page'))