from flask import render_template, redirect, url_for, session

from templates.admin_profile.admin_profile_backend import get_admin_profile_data


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