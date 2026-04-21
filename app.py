from flask import Flask

from templates.dashboard.dashboard_app import register_dashboard_routes
from templates.assets.asset_app import register_assets_routes
from templates.assign.assign_app import register_assign_routes
from templates.manage.manage_app import register_manage_routes
from templates.login.login_app import register_login_routes
from templates.report.report_app import register_report_routes
from templates.admin_profile.admin_profile_app import register_admin_profile_routes
from templates.statistical.statistical_app import register_statistical_routes


app = Flask(__name__)
app.secret_key = "hsu_assetone_2026"

register_dashboard_routes(app)
register_assets_routes(app)
register_assign_routes(app)
register_manage_routes(app)
register_login_routes(app)
register_report_routes(app)
register_admin_profile_routes(app)
register_statistical_routes(app)


if __name__ == "__main__":
    app.run(debug=True)