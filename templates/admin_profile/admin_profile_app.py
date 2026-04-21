from flask import render_template

def register_admin_profile_routes(app):
    @app.route('/admin-profile')
    def profile_page():
        return render_template('admin_profile/admin_profile.html')

    @app.route('/admin-profile/overview')
    def admin_profile_overview():
        return render_template('admin_profile/admin_profile_overview.html')