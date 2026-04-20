from flask import render_template, request
import math
import data


def register_report_routes(app):
    @app.route('/report')
    def report_page():
        search_query = request.args.get('search', '').strip().lower()
        selected_dept = request.args.get('department', 'Tất cả')
        page = request.args.get('page', 1, type=int)
        per_page = 12

        filtered = data.DATABASE_LOGS
        if search_query:
            filtered = [
                l for l in filtered
                if search_query in l.get('asset', '').lower() or search_query in l.get('user', '').lower()
            ]
        if selected_dept != 'Tất cả':
            filtered = [l for l in filtered if l.get('dept') == selected_dept]

        total_logs = len(filtered)
        total_pages = math.ceil(total_logs / per_page) if total_logs > 0 else 1
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        logs_to_display = filtered[start:start + per_page]

        return render_template(
            'report/report.html',
            logs=logs_to_display,
            search_query=search_query,
            selected_dept=selected_dept,
            current_page=page,
            total_pages=total_pages
        )