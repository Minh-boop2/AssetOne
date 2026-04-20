from flask import render_template, request, redirect, url_for, flash
import math
import data


def register_manage_routes(app):
    @app.route('/manage')
    def manage():
        search_q = request.args.get('search', '').strip().lower()
        selected_dept = request.args.get('department', '')
        selected_role = request.args.get('role', '')
        selected_status = request.args.get('status', '')
        page = request.args.get('page', 1, type=int)
        per_page = 10

        filtered_users = data.USER_LIST_DATA
        if search_q:
            filtered_users = [
                i for i in filtered_users if
                search_q in i.get('name', '').lower() or
                search_q in i.get('id', '').lower() or
                search_q in i.get('email', '').lower()
            ]

        if selected_dept and "Tất cả" not in selected_dept:
            filtered_users = [i for i in filtered_users if i.get('dept') == selected_dept]
        if selected_role and "Tất cả" not in selected_role:
            filtered_users = [i for i in filtered_users if i.get('role') == selected_role]
        if selected_status and "Tất cả" not in selected_status:
            filtered_users = [i for i in filtered_users if i.get('status') == selected_status]

        total_users = len(filtered_users)
        total_pages = math.ceil(total_users / per_page) if total_users > 0 else 1
        page = max(1, min(page, total_pages))

        start = (page - 1) * per_page
        end = start + per_page
        paginated_users = filtered_users[start:end]

        stats = {
            "total": len(data.USER_LIST_DATA),
            "admin_count": len([i for i in data.USER_LIST_DATA if i.get('role').lower() == 'admin']),
            "manager_count": len([i for i in data.USER_LIST_DATA if i.get('role').lower() == 'manager']),
            "staff_count": len([i for i in data.USER_LIST_DATA if i.get('role').lower() == 'staff'])
        }

        return render_template(
            'manage/manage_overview.html',
            employees=paginated_users,
            stats=stats,
            departments=data.DEPARTMENTS,
            roles=data.ROLES,
            user_status=data.USER_STATUS_OPTIONS,
            search_q=search_q,
            selected_dept=selected_dept,
            selected_role=selected_role,
            selected_status=selected_status,
            current_page=page,
            total_pages=total_pages
        )

    @app.route('/manage/detail/<string:id>')
    def user_detail(id):
        user = next((u for u in data.USER_LIST_DATA if u['id'] == id), None)
        if not user:
            return redirect(url_for('manage'))
        return render_template('manage/manage_detail.html', employee=user)

    @app.route('/manage/edit/<string:id>', methods=['GET', 'POST'])
    def user_edit(id):
        user = next((u for u in data.USER_LIST_DATA if u['id'] == id), None)
        if not user:
            return redirect(url_for('manage'))

        if request.method == 'POST':
            user.update({
                "role": request.form.get('role'),
                "status": request.form.get('status')
            })
            flash(f"Đã cập nhật quyền cho {user['name']}", "success")
            return redirect(url_for('manage'))

        return render_template('manage/manage_edit.html', employee=user)

    @app.route('/manage/delete/<string:id>', methods=['GET', 'POST'])
    def user_delete(id):
        user = next((u for u in data.USER_LIST_DATA if u['id'] == id), None)
        if not user:
            return redirect(url_for('manage'))

        if request.method == 'POST':
            data.USER_LIST_DATA = [u for u in data.USER_LIST_DATA if u['id'] != id]
            flash(f"Đã xóa vĩnh viễn nhân sự {id}", "danger")
            return redirect(url_for('manage'))

        return render_template('manage/manage_delete.html', employee=user)