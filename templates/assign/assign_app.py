from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import math
import random
import string
import data  # Đảm bảo file data.py nằm cùng thư mục

app = Flask(__name__)
app.secret_key = 'hsu_secret_key_2026'

# --- HÀM HỖ TRỢ: SINH MÃ NGẪU NHIÊN KHÔNG TRÙNG LẶP ---
def generate_unique_asset_code(existing_data):
    """Tạo mã HSU-XXXXXX ngẫu nhiên và kiểm tra trùng lặp trong ASSIGN_DATA"""
    existing_codes = {item.get('asset_code') for item in existing_data}
    
    while True:
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        new_code = f"HSU-{random_str}"
        if new_code not in existing_codes:
            return new_code

def register_assign_routes(app):
    # --- 1. TRANG DANH SÁCH (OVERVIEW) ---
    @app.route('/assign')
    def assign_page():
        search_q = request.args.get('search', '').strip().lower()
        selected_dept = request.args.get('department', 'Tất cả')
        selected_cat = request.args.get('category', 'Tất cả')
        selected_loc = request.args.get('location', 'Tất cả')
        selected_status = request.args.get('status', 'Tất cả')
        
        page = request.args.get('page', 1, type=int)
        per_page = 10

        filtered_data = data.ASSIGN_DATA

        if search_q:
            filtered_data = [
                i for i in filtered_data
                if search_q in i.get('asset', '').lower() or 
                   search_q in i.get('asset_code', '').lower() or
                   search_q in i.get('id', '').lower() or
                   search_q in i.get('receiver', '').lower()
            ]
        
        if selected_dept and selected_dept != 'Tất cả':
            filtered_data = [i for i in filtered_data if i.get('department') == selected_dept]
            
        if selected_cat and selected_cat != 'Tất cả':
            filtered_data = [i for i in filtered_data if i.get('type') == selected_cat]

        if selected_loc and selected_loc != 'Tất cả':
            filtered_data = [i for i in filtered_data if i.get('location') == selected_loc]
            
        if selected_status and selected_status != 'Tất cả':
            filtered_data = [i for i in filtered_data if i.get('status') == selected_status]

        counts = data.get_filter_counts()

        total_items = len(filtered_data)
        total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        assigns_paginated = filtered_data[start : start + per_page]

        return render_template(
            'assign/assign_overview.html',
            assigns=assigns_paginated,
            counts=counts,
            departments=data.DEPARTMENTS,
            categories=data.ASSET_TYPES,
            locations=data.LOCATIONS,
            status_options=data.STATUS_OPTIONS,
            current_page=page,
            total_pages=total_pages,
            total_items=total_items,
            search_q=search_q,
            selected_dept=selected_dept,
            selected_cat=selected_cat,
            selected_loc=selected_loc,
            selected_status=selected_status
        )

    # --- 2. TẠO MỚI CẤP PHÁT (CREATE) ---
    @app.route('/assign/create', methods=['GET', 'POST'])
    def assign_create():
        if request.method == 'POST':
            asset_name = request.form.get('asset_name')
            receiver = request.form.get('receiver')
            dept = request.form.get('department')
            asset_type = request.form.get('type') 
            location = request.form.get('location')
            spec_content = request.form.get('spec')
            asset_code = request.form.get('asset_code')
            
            inventory_item = next((item for item in data.INVENTORY_LIST if item["name"] == asset_name), None)
            
            if inventory_item:
                final_type = inventory_item.get('type', asset_type)
            else:
                final_type = asset_type
                data.INVENTORY_LIST.append({
                    "name": asset_name, 
                    "spec": spec_content, 
                    "type": asset_type
                })

            new_id_num = len(data.ASSIGN_DATA) + 1
            new_id = f"ASG-{str(new_id_num).zfill(3)}"
            
            new_entry = {
                "id": new_id,
                "asset_code": asset_code,
                "asset": asset_name,
                "type": final_type,
                "receiver": receiver,
                "department": dept,
                "location": location or "Văn phòng HSU",
                "date": datetime.now().strftime("%d/%m/%Y"),
                "status": "Chờ duyệt", # Mặc định tạo mới là Chờ duyệt
                "notes": spec_content
            }
            
            data.ASSIGN_DATA.insert(0, new_entry)
            
            flash(f'Đã cấp phát thành công {asset_name} cho {receiver}!', 'success')
            return redirect(url_for('assign_page'))
            
        suggested_code = generate_unique_asset_code(data.ASSIGN_DATA)
        unique_types = sorted(list(set(item.get('type') for item in data.INVENTORY_LIST if item.get('type'))))

        return render_template('assign/assign_create.html', 
                               inventory=data.INVENTORY_LIST, 
                               departments=data.DEPARTMENTS,
                               locations=data.LOCATIONS,
                               suggested_code=suggested_code,
                               inventory_types=unique_types)

    # --- 3. XEM CHI TIẾT (DETAIL) ---
    @app.route('/assign/detail/<string:id>')
    def assign_detail(id):
        info = next((item for item in data.ASSIGN_DATA if item["id"] == id), None)
        if not info:
            flash("Không tìm thấy thông tin.", "danger")
            return redirect(url_for('assign_page'))
        
        specs = next((item for item in data.INVENTORY_LIST if item["name"] == info['asset']), 
                     {"spec": info.get('notes', "Chưa có thông tin cấu hình.")})
        
        return render_template('assign/assign_detail.html', info=info, specs=specs)

    # --- 4. CHỈNH SỬA (EDIT) ---
    @app.route('/assign/edit/<string:id>', methods=['GET', 'POST'])
    def assign_edit(id):
        # Lấy thông tin cấp phát
        info = next((item for item in data.ASSIGN_DATA if item["id"] == id), None)
        if not info:
            flash("Bản ghi không tồn tại.", "danger")
            return redirect(url_for('assign_page'))

        # Lấy thông số kỹ thuật từ kho dựa trên tên tài sản
        specs_item = next((item for item in data.INVENTORY_LIST if item["name"] == info['asset']), None)

        if request.method == 'POST':
            # Cập nhật thông tin từ form HTML (Khớp name="...")
            info['asset'] = request.form.get('asset_name')
            info['receiver'] = request.form.get('receiver')
            info['department'] = request.form.get('department')
            info['type'] = request.form.get('category') # Trong form HTML đặt name="category"
            info['location'] = request.form.get('location')
            info['status'] = request.form.get('status')
            
            new_spec = request.form.get('notes') # Trong form HTML đặt name="notes" cho textarea
            info['notes'] = new_spec

            # Đồng bộ ngược lại kho hàng (Inventory)
            if specs_item:
                specs_item['name'] = info['asset'] # Cập nhật tên nếu có đổi
                specs_item['spec'] = new_spec
                specs_item['type'] = info['type']
            else:
                data.INVENTORY_LIST.append({
                    "name": info['asset'], 
                    "spec": new_spec, 
                    "type": info['type']
                })

            flash(f'Đã cập nhật thay đổi cho phiếu #{id}', 'success')
            return redirect(url_for('assign_detail', id=id))

        # Trả về dữ liệu cho Form GET
        return render_template('assign/assign_edit.html', 
                               assign=info, # Đổi tên biến sang 'assign' để khớp file HTML trước
                               departments=data.DEPARTMENTS,
                               categories=data.ASSET_TYPES,
                               locations=data.LOCATIONS,
                               status_options=data.STATUS_OPTIONS)

    # --- 5. ACTION PHÊ DUYỆT ---
    @app.route('/assign/approve/<string:id>')
    def approve_request(id):
        for item in data.ASSIGN_DATA:
            if item['id'] == id:
                item['status'] = 'Hoàn thành'
                flash(f'Đã phê duyệt phiếu #{id}', 'success')
                break
        return redirect(url_for('assign_page'))

    # --- 6. ACTION TỪ CHỐI ---
    @app.route('/assign/reject/<string:id>')
    def reject_request(id):
        for item in data.ASSIGN_DATA:
            if item['id'] == id:
                item['status'] = 'Đã từ chối' 
                flash(f'Đã từ chối yêu cầu phiếu #{id}', 'warning')
                break
        return redirect(url_for('assign_page'))

    # --- 7. XÓA BẢN GHI ---
    @app.route('/assign/delete/<string:id>')
    def delete_assign(id):
        data.ASSIGN_DATA = [i for i in data.ASSIGN_DATA if i['id'] != id]
        flash(f'Đã xóa bản ghi #{id}', 'warning')
        return redirect(url_for('assign_page'))

# Đăng ký routes vào app
register_assign_routes(app)

if __name__ == '__main__':
    app.run(debug=True)