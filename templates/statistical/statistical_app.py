from flask import render_template

def register_statistical_routes(app):
    @app.route('/statistical')
    def statistics_page():
        return render_template('statistical/statistical.html')

    @app.route('/statistical/overview')
    def statistical_overview():
        return render_template('statistical/statistical_overview.html')