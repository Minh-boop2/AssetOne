from flask import render_template, request, redirect, url_for
from datetime import datetime
import math
import data


def register_assign_routes(app):
    @app.route('/assign')
    def assign_page():
        search_q = request.args.get('search', '').strip().lower()
        selected_dept = request.args.get('department', '')
        selected_cat = request.args.get('category', '')
        selected_status = request.args.get('status', '')
        page = request.args.get('page', 1, type=int)
        per_page = 10

        filtered = data.ASSIGN_DATA
        if search_q:
            filtered = [
                i for i in filtered
                if search_q in i.get('asset', '').lower() or search_q in i.get('id', '').lower()
            ]

        if selected_dept:
            filtered = [i for i in filtered if i.get('department') == selected_dept]
        if selected_cat:
            filtered = [i for i in filtered if i.get('type') == selected_cat]
        if selected_status:
            filtered = [i for i in filtered if i.get('status') == selected_status]

        stats = {
            "total": len(data.ASSIGN_DATA),
            "pending": len([i for i in data.ASSIGN_DATA if i.get('status') == 'Chờ duyệt']),
            "overdue": 0
        }

        total_items = len(filtered)
        total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
        page = max(1, min(page, total_pages))

        start = (page - 1) * per_page
        assigns_paginated = filtered[start:start + per_page]

        return render_template(
            'assign/assign_overview.html',
            assigns=assigns_paginated,
            stats=stats,
            departments=data.DEPARTMENTS,
            categories=data.ASSET_TYPES,
            status_options=data.STATUS_OPTIONS,
            current_page=page,
            total_pages=total_pages,
            search_q=search_q,
            selected_dept=selected_dept,
            selected_cat=selected_cat,
            selected_status=selected_status
        )

    @app.route('/assign/detail/<string:assign_id>')
    def assign_detail_view(assign_id):
        info = next((item for item in data.ASSIGN_DATA if item["id"] == assign_id), None)
        if not info:
            return redirect(url_for('assign_page'))

        specs = next((item for item in data.INVENTORY_LIST if item["name"] == info.get('asset')), {
            "spec": "Dữ liệu cấu hình chưa có cho yêu cầu này.",
            "warranty": "N/A"
        })
        return render_template('assign/assign_detail.html', info=info, specs=specs)

    @app.route('/assign/create', methods=['GET', 'POST'])
    def assign_create():
        if request.method == 'POST':
            asset_name = request.form.get('asset_name')
            new_entry = {
                "id": f"ASG-{str(len(data.ASSIGN_DATA) + 1).zfill(3)}",
                "asset": asset_name,
                "receiver": request.form.get('receiver'),
                "department": request.form.get('department'),
                "type": request.form.get('type', 'Thiết bị'),
                "location": request.form.get('location', 'Văn phòng'),
                "date": datetime.now().strftime("%d/%m/%Y"),
                "status": "Hoàn thành",
                "condition": "Mới"
            }
            data.ASSIGN_DATA.insert(0, new_entry)
            return redirect(url_for('assign_page'))
        return render_template('assign/assign_create.html', inventory=data.INVENTORY_LIST, departments=data.DEPARTMENTS)

    @app.route('/assign/edit/<string:assign_id>', methods=['GET', 'POST'])
    def assign_edit(assign_id):
        info = next((item for item in data.ASSIGN_DATA if item["id"] == assign_id), None)
        if not info:
            return redirect(url_for('assign_page'))

        if request.method == 'POST':
            info.update({
                "receiver": request.form.get('receiver'),
                "department": request.form.get('department'),
                "status": request.form.get('status'),
                "location": request.form.get('location')
            })
            return redirect(url_for('assign_detail_view', assign_id=assign_id))
        return render_template('assign/assign_edit.html', info=info)

    @app.route('/assign/request', methods=['GET', 'POST'])
    def request_create():
        if request.method == 'POST':
            new = {
                "id": f"REQ-{str(len(data.ASSIGN_DATA) + 1).zfill(3)}",
                "asset": request.form.get('asset_name'),
                "receiver": request.form.get('requester'),
                "department": request.form.get('department', 'Chưa rõ'),
                "date": datetime.now().strftime("%d/%m/%Y"),
                "status": "Chờ duyệt"
            }
            data.ASSIGN_DATA.insert(0, new)
            return redirect(url_for('assign_page'))
        return render_template('assign/request_create.html', inventory=data.INVENTORY_LIST)

    @app.route('/assign/approve/<string:id>')
    def approve_request(id):
        for item in data.ASSIGN_DATA:
            if item['id'] == id:
                item['status'] = 'Hoàn thành'
                item['date'] = datetime.now().strftime("%d/%m/%Y")
                break
        return redirect(url_for('assign_page'))

    @app.route('/assign/reject/<string:id>')
    def reject_request(id):
        for i, item in enumerate(data.ASSIGN_DATA):
            if item['id'] == id:
                data.ASSIGN_DATA.pop(i)
                break
        return redirect(url_for('assign_page'))