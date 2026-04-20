from flask import render_template
import data


def register_dashboard_routes(app):
    @app.route('/')
    def dashboard_overview():
        using_count = len([i for i in data.ASSIGN_DATA if i.get('status') == 'Hoàn thành'])
        total_real = len(data.ASSIGN_DATA)
        stats = {
            "total": total_real,
            "using": using_count,
            "available": max(0, total_real - using_count - 10),
            "maintenance": 10
        }
        recent_activities = data.ASSIGN_DATA[:4]
        return render_template('dashboard/overview.html', stats=stats, activities=recent_activities)