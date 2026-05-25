from flask import Flask, request, session, redirect, url_for

from templates.dashboard.dashboard_app import register_dashboard_routes
from templates.assets.asset_app import register_assets_routes
from templates.assign.assign_app import register_assign_routes
from templates.manage.manage_app import register_manage_routes
from templates.login.login_app import register_login_routes
from templates.report.report_app import register_report_routes
from templates.admin_profile.admin_profile_app import register_admin_profile_routes
from templates.statistical.statistical_app import register_statistical_routes
from templates.activity.activity_app import register_activity_routes

app = Flask(__name__)
app.secret_key = "hsu_assetone_2026"


@app.before_request
def require_login():
    public_endpoints = {
        "login_page",
        "welcome_page",
        "forgot_password",
        "reset_password_page",
        "logout",
        "static",
    }

    if request.endpoint in public_endpoints:
        return None

    if request.path.startswith("/static/"):
        return None

    if request.endpoint is None:
        return None

    if not session.get("user"):
        return redirect(url_for("login_page"))

    return None


register_dashboard_routes(app)
register_assets_routes(app)
register_assign_routes(app)
register_manage_routes(app)
register_login_routes(app)
register_report_routes(app)
register_admin_profile_routes(app)
register_statistical_routes(app)
register_activity_routes(app)

if __name__ == "__main__":
    app.run(debug=True)