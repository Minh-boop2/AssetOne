from flask import render_template, request, session, redirect, url_for, Response

from templates.activity.activity_backend import (
    get_activity_page_context,
    export_activities_excel,
)


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

    @app.route("/activity/export")
    def activity_export_page():
        current_user = session.get("user") or {}

        if not current_user:
            return redirect(url_for("login_page"))

        result = export_activities_excel(
            args=request.args,
            current_user=current_user,
        )

        if not result.get("success"):
            return Response(
                result.get("content") or b"Export failed",
                status=result.get("status_code", 500),
                mimetype=result.get("content_type", "text/plain")
            )

        response = Response(
            result["content"],
            mimetype=result["content_type"],
        )

        response.headers["Content-Disposition"] = (
            f'attachment; filename="{result["filename"]}"'
        )

        return response