from flask import render_template, request, session, redirect, url_for

from templates.activity.activity_backend import get_activity_page_context


def register_activity_routes(app):

    @app.route("/activity")
    def activity_page():
        current_user = session.get("user") or {}

        if not current_user:
            return redirect(url_for("login_page"))

        context = get_activity_page_context(
            args=request.args,
            current_user=current_user,
        )

        return render_template("activity/activity.html", **context)