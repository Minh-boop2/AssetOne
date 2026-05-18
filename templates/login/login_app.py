from datetime import timedelta
from flask import render_template, request, redirect, url_for, session

from .login_backend import (
    login_user_from_form,
    forgot_password_from_form,
    verify_reset_token,
    reset_password_from_form,
)


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
                session["login_error"] = message or "Sai tài khoản hoặc mật khẩu"
                session["login_email"] = request.form.get("email", "")
                session["login_remember"] = True if request.form.get("remember") else False

                return redirect(url_for('login_page'))

            session.pop("login_error", None)
            session.pop("login_email", None)
            session.pop("login_remember", None)

            # user lúc này đã được login_backend chuẩn hóa sẵn:
            # có id, role, permissions, can, is_admin
            session["user"] = user
            session["current_user"] = user
            session["current_user_id"] = user["id"]

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