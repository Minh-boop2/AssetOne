from flask import render_template, redirect, url_for, session, request, flash

from templates.admin_profile.admin_profile_backend import (
    get_admin_profile_data,
    upload_admin_avatar,
)


def register_admin_profile_routes(app):

    @app.route("/admin-profile")
    def profile_page():
        if not session.get("user"):
            return redirect(url_for("login_page"))

        data = get_admin_profile_data()

        return render_template(
            "admin_profile/admin_profile.html",
            admin=data.get("admin"),
            logs=data.get("logs", []),
            assign_data=data.get("assign_data", []),
            profile_message=data.get("message"),
        )

    @app.route("/admin-profile/avatar", methods=["POST"])
    def upload_profile_avatar():
        if not session.get("user"):
            return redirect(url_for("login_page"))

        file = request.files.get("avatar")
        response = upload_admin_avatar(file)

        if response.get("success"):
            flash(response.get("message") or "Cập nhật ảnh đại diện thành công", "success")
        else:
            flash(response.get("message") or "Không thể cập nhật ảnh đại diện", "error")

        return redirect(url_for("profile_page"))