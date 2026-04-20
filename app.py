from flask import Flask, render_template, request, redirect, url_for, flash
from data import (
    ASSIGN_DATA, INVENTORY_LIST, DATABASE_LOGS, DEPARTMENTS, 
    ASSET_TYPES, STATUS_OPTIONS, USER_LIST_DATA, ROLES, USER_STATUS_OPTIONS
)
from datetime import datetime
import math

app = Flask(__name__)
app.secret_key = "hsu_assetone_2026"

# --- 1. TRANG CHỦ (DASHBOARD) ---
@app.route('/')
def dashboard_overview():
    using_count = len([i for i in ASSIGN_DATA if i.get('status') == 'Hoàn thành'])
    total_real = len(ASSIGN_DATA)
    stats = {
        "total": total_real,
        "using": using_count,
        "available": max(0, total_real - using_count - 10),
        "maintenance": 10
    }
    recent_activities = ASSIGN_DATA[:4]
    return render_template('dashboard/overview.html', stats=stats, activities=recent_activities)

# --- 2. QUẢN LÝ KHO TÀI SẢN (ASSETS) ---
@app.route('/assets')
def assets_page(): 
    search_q = request.args.get('search', '').strip().lower()
    sel_type = request.args.get('type', 'Tất cả')
    sel_dept = request.args.get('department', 'Tất cả')
    sel_status = request.args.get('status', 'Tất cả')
    
    filtered = ASSIGN_DATA
    if search_q:
        filtered = [
            i for i in filtered if 
            search_q in i.get('asset', '').lower() or 
            search_q in i.get('asset_code', '').lower() or
            search_q in i.get('id', '').lower()
        ]
    if sel_type != 'Tất cả':
        filtered = [i for i in filtered if i.get('type') == sel_type]
    if sel_dept != 'Tất cả':
        filtered = [i for i in filtered if i.get('department') == sel_dept]
    if sel_status != 'Tất cả':
        if sel_status == 'using':
            filtered = [i for i in filtered if i.get('status') in ['using', 'Hoàn thành']]
        else:
            filtered = [i for i in filtered if i.get('status') == sel_status]

    page = request.args.get('page', 1, type=int) 
    per_page = 10 
    total_assets = len(filtered)
    total_pages = math.ceil(total_assets / per_page) if total_assets > 0 else 1
    page = max(1, min(page, total_pages))
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_assets = filtered[start:end]
        
    return render_template(
        'assets/assets.html', 
        assets=paginated_assets, 
        current_page=page, 
        total_pages=total_pages,
        search_q=search_q,
        total_count=total_assets,
        selected_type=sel_type,
        selected_dept=sel_dept,
        selected_status=sel_status
    )

@app.route('/assets/create', methods=['GET', 'POST'])
def asset_create():
    if request.method == 'POST':
        asset_name = request.form.get('asset_name')
        new_id = f"ASG-{str(len(ASSIGN_DATA) + 1).zfill(3)}"
        new_asset = {
            "id": new_id,
            "asset_code": request.form.get('asset_code'),
            "asset": asset_name, 
            "type": request.form.get('type'),
            "receiver": request.form.get('receiver'),
            "department": request.form.get('department'),
            "location": request.form.get('location'),
            "date": datetime.now().strftime("%d/%m/%Y"),
            "warranty": request.form.get('warranty'),
            "status": request.form.get('status')
        }
        ASSIGN_DATA.insert(0, new_asset)
        INVENTORY_LIST.append({
            "name": asset_name,
            "spec": request.form.get('spec') or "Thông số đang cập nhật",
            "warranty": request.form.get('warranty')
        })
        return redirect(url_for('assets_page'))
    return render_template('assets/asset_create.html')

@app.route('/assets/detail/<string:asset_id>')
def asset_detail_view(asset_id):
    info = next((item for item in ASSIGN_DATA if item["id"] == asset_id), None)
    if not info:
        return redirect(url_for('assets_page'))
    
    specs = next((item for item in INVENTORY_LIST if item["name"] == info.get('asset')), {
        "spec": "Thông số kỹ thuật đang được cập nhật",
        "warranty": "N/A"
    })
    return render_template('assets/asset_detail.html', info=info, specs=specs)

# --- 3. QUẢN LÝ CẤP PHÁT (ASSIGN) ---
@app.route('/assign')
def assign_page():
    search_q = request.args.get('search', '').strip().lower()
    selected_dept = request.args.get('department', '')
    selected_cat = request.args.get('category', '')
    selected_status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    filtered = ASSIGN_DATA
    if search_q:
        filtered = [i for i in filtered if search_q in i.get('asset', '').lower() or search_q in i.get('id', '').lower()]
    
    if selected_dept: filtered = [i for i in filtered if i.get('department') == selected_dept]
    if selected_cat: filtered = [i for i in filtered if i.get('type') == selected_cat]
    if selected_status: filtered = [i for i in filtered if i.get('status') == selected_status]

    stats = {
        "total": len(ASSIGN_DATA),
        "pending": len([i for i in ASSIGN_DATA if i.get('status') == 'Chờ duyệt']),
        "overdue": 0
    }

    total_items = len(filtered)
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
    page = max(1, min(page, total_pages))
    
    start = (page - 1) * per_page
    assigns_paginated = filtered[start:start+per_page]

    return render_template(
        'assign/assign_overview.html',
        assigns=assigns_paginated,
        stats=stats,
        departments=DEPARTMENTS,
        categories=ASSET_TYPES,
        status_options=STATUS_OPTIONS,
        current_page=page,
        total_pages=total_pages,
        search_q=search_q,
        selected_dept=selected_dept,
        selected_cat=selected_cat,
        selected_status=selected_status
    )

@app.route('/assign/detail/<string:assign_id>')
def assign_detail_view(assign_id):
    info = next((item for item in ASSIGN_DATA if item["id"] == assign_id), None)
    if not info: return redirect(url_for('assign_page'))
    
    specs = next((item for item in INVENTORY_LIST if item["name"] == info.get('asset')), {
        "spec": "Dữ liệu cấu hình chưa có cho yêu cầu này.",
        "warranty": "N/A"
    })
    return render_template('assign/assign_detail.html', info=info, specs=specs)

@app.route('/assign/create', methods=['GET','POST'])
def assign_create():
    if request.method == 'POST':
        asset_name = request.form.get('asset_name')
        new_entry = {
            "id": f"ASG-{str(len(ASSIGN_DATA) + 1).zfill(3)}",
            "asset": asset_name,
            "receiver": request.form.get('receiver'),
            "department": request.form.get('department'),
            "type": request.form.get('type', 'Thiết bị'),
            "location": request.form.get('location', 'Văn phòng'),
            "date": datetime.now().strftime("%d/%m/%Y"),
            "status": "Hoàn thành",
            "condition": "Mới"
        }
        ASSIGN_DATA.insert(0, new_entry)
        return redirect(url_for('assign_page'))
    return render_template('assign/assign_create.html', inventory=INVENTORY_LIST, departments=DEPARTMENTS)

@app.route('/assign/edit/<string:assign_id>', methods=['GET', 'POST'])
def assign_edit(assign_id):
    info = next((item for item in ASSIGN_DATA if item["id"] == assign_id), None)
    if not info: return redirect(url_for('assign_page'))
    if request.method == 'POST':
        info.update({
            "receiver": request.form.get('receiver'),
            "department": request.form.get('department'),
            "status": request.form.get('status'),
            "location": request.form.get('location')
        })
        return redirect(url_for('assign_detail_view', assign_id=assign_id))
    return render_template('assign/assign_edit.html', info=info)

# --- 4. QUẢN TRỊ NHÂN SỰ (MANAGE) ---
@app.route('/manage')
def manage(): 
    search_q = request.args.get('search', '').strip().lower()
    selected_dept = request.args.get('department', '')
    selected_role = request.args.get('role', '')
    selected_status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10 

    filtered_users = USER_LIST_DATA
    if search_q:
        filtered_users = [i for i in filtered_users if 
                          search_q in i.get('name', '').lower() or 
                          search_q in i.get('id', '').lower() or
                          search_q in i.get('email', '').lower()]
    
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
        "total": len(USER_LIST_DATA),
        "admin_count": len([i for i in USER_LIST_DATA if i.get('role').lower() == 'admin']),
        "manager_count": len([i for i in USER_LIST_DATA if i.get('role').lower() == 'manager']),
        "staff_count": len([i for i in USER_LIST_DATA if i.get('role').lower() == 'staff'])
    }

    return render_template('manage/manage_overview.html', 
                           employees=paginated_users,
                           stats=stats,
                           departments=DEPARTMENTS,
                           roles=ROLES,
                           user_status=USER_STATUS_OPTIONS,
                           search_q=search_q,
                           selected_dept=selected_dept,
                           selected_role=selected_role,
                           selected_status=selected_status,
                           current_page=page,
                           total_pages=total_pages)

# --- PHẦN UPDATE MỚI: 3 ROUTE QUẢN LÝ NHÂN SỰ ---

@app.route('/manage/detail/<string:id>')
def user_detail(id):
    user = next((u for u in USER_LIST_DATA if u['id'] == id), None)
    if not user: return redirect(url_for('manage'))
    return render_template('manage/manage_detail.html', employee=user)

@app.route('/manage/edit/<string:id>', methods=['GET', 'POST'])
def user_edit(id):
    user = next((u for u in USER_LIST_DATA if u['id'] == id), None)
    if not user: return redirect(url_for('manage'))
    
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
    global USER_LIST_DATA
    user = next((u for u in USER_LIST_DATA if u['id'] == id), None)
    if not user: return redirect(url_for('manage'))

    if request.method == 'POST':
        # Xóa hoàn toàn khỏi danh sách
        USER_LIST_DATA = [u for u in USER_LIST_DATA if u['id'] != id]
        flash(f"Đã xóa vĩnh viễn nhân sự {id}", "danger")
        return redirect(url_for('manage'))
    
    # Hiển thị trang xác nhận xóa
    return render_template('manage/manage_delete.html', employee=user)

# --- 5. ROUTE HỖ TRỢ KHÁC ---
@app.route('/assign/request', methods=['GET','POST'])
def request_create():
    if request.method == 'POST':
        new = {
            "id": f"REQ-{str(len(ASSIGN_DATA)+1).zfill(3)}",
            "asset": request.form.get('asset_name'),
            "receiver": request.form.get('requester'),
            "department": request.form.get('department', 'Chưa rõ'),
            "date": datetime.now().strftime("%d/%m/%Y"),
            "status": "Chờ duyệt"
        }
        ASSIGN_DATA.insert(0, new)
        return redirect(url_for('assign_page'))
    return render_template('assign/request_create.html', inventory=INVENTORY_LIST)

@app.route('/assign/approve/<string:id>')
def approve_request(id):
    for item in ASSIGN_DATA:
        if item['id'] == id:
            item['status'] = 'Hoàn thành'
            item['date'] = datetime.now().strftime("%d/%m/%Y")
            break
    return redirect(url_for('assign_page'))

@app.route('/assign/reject/<string:id>')
def reject_request(id):
    for i, item in enumerate(ASSIGN_DATA):
        if item['id'] == id:
            ASSIGN_DATA.pop(i)
            break
    return redirect(url_for('assign_page'))

@app.route('/welcome')
def welcome_page(): return render_template('login/login_overview.html')

@app.route('/login', methods=['GET','POST'])
def login_page():
    if request.method == 'POST':
        if request.form.get('username') == "admin" and request.form.get('password') == "123":
            return redirect(url_for('dashboard_overview'))
    return render_template('login/login.html')

@app.route('/report')
def report_page(): 
    search_query = request.args.get('search', '').strip().lower()
    selected_dept = request.args.get('department', 'Tất cả')
    page = request.args.get('page', 1, type=int)
    per_page = 12

    filtered = DATABASE_LOGS
    if search_query:
        filtered = [l for l in filtered if search_query in l.get('asset', '').lower() or search_query in l.get('user', '').lower()]
    if selected_dept != 'Tất cả':
        filtered = [l for l in filtered if l.get('dept') == selected_dept]

    total_logs = len(filtered)
    total_pages = math.ceil(total_logs / per_page) if total_logs > 0 else 1
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    logs_to_display = filtered[start : start + per_page]

    return render_template('report/report.html', 
                            logs=logs_to_display, 
                            search_query=search_query,
                            selected_dept=selected_dept,
                            current_page=page,
                            total_pages=total_pages)

if __name__ == "__main__":
    app.run(debug=True)