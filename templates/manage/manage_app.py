from flask import render_template, request, redirect, url_for, flash
import math
import data
import random
import string
from datetime import datetime

def generate_unique_id():
    """Tạo mã nhân viên ngẫu nhiên định dạng HSU-XXX và kiểm tra trùng lặp"""
    while True:
        # Tạo 3 số ngẫu nhiên
        random_num = ''.join(random.choices(string.digits, k=3))
        new_id = f"HSU-{random_num}"
        
        # Kiểm tra xem mã đã tồn tại trong hệ thống chưa (data.USER_LIST_DATA)
        exists = any(user.get('id') == new_id for user in data.USER_LIST_DATA)
        if not exists:
            return new_id

def register_manage_routes(app):
    @app.route('/manage')
    def manage():
        # 1. Lấy tham số từ URL
        search_q = request.args.get('search', '').strip().lower()
        selected_dept = request.args.get('department', 'Tất cả')
        selected_role = request.args.get('role', 'Tất cả')
        selected_status = request.args.get('status', 'Tất cả')
        selected_floor = request.args.get('floor', 'Tất cả') 
        page = request.args.get('page', 1, type=int)
        per_page = 10

        # 2. Khởi tạo danh sách tầng cố định
        floors_list = [f"Tầng {i}" for i in range(1, 11)]

        # 3. Khởi tạo biến counts để hiển thị số lượng thực tế cạnh label
        dept_counts = {}
        role_counts = {}
        status_counts = {}
        floor_counts = {} 

        # 4. Tính toán số lượng thực tế từ USER_LIST_DATA toàn bộ
        for u in data.USER_LIST_DATA:
            d = u.get('dept')
            r = u.get('role')
            s = u.get('status')
            f = u.get('position') 
            
            if d: dept_counts[d] = dept_counts.get(d, 0) + 1
            if r: role_counts[r] = role_counts.get(r, 0) + 1
            if s: status_counts[s] = status_counts.get(s, 0) + 1
            if f: floor_counts[f] = floor_counts.get(f, 0) + 1

        # 5. Lọc dữ liệu (Filtering)
        filtered_users = data.USER_LIST_DATA

        # Tìm kiếm đa năng
        if search_q:
            filtered_users = [
                i for i in filtered_users if
                search_q in i.get('name', '').lower() or
                search_q in i.get('id', '').lower() or
                search_q in i.get('email', '').lower() or
                search_q in i.get('phone', '').lower() or
                search_q in i.get('dept', '').lower() or
                search_q in i.get('role', '').lower() or
                search_q in str(i.get('position', '')).lower()
            ]

        # Lọc theo Phòng ban
        if selected_dept and selected_dept != "Tất cả":
            filtered_users = [i for i in filtered_users if i.get('dept') == selected_dept]
        
        # Lọc theo Quyền hạn
        if selected_role and selected_role != "Tất cả":
            filtered_users = [i for i in filtered_users if i.get('role') == selected_role]
            
        # Lọc theo Trạng thái
        if selected_status and selected_status != "Tất cả":
            filtered_users = [i for i in filtered_users if i.get('status') == selected_status]

        # Lọc theo Vị trí (Tầng)
        if selected_floor and selected_floor != "Tất cả":
            filtered_users = [i for i in filtered_users if i.get('position') == selected_floor]

        # 6. Phân trang (Pagination)
        total_filtered = len(filtered_users)
        total_pages = math.ceil(total_filtered / per_page) if total_filtered > 0 else 1
        page = max(1, min(page, total_pages))

        start = (page - 1) * per_page
        end = start + per_page
        paginated_users = filtered_users[start:end]

        # 7. Thống kê cho các Stat Cards
        stats = {
            "total": len(data.USER_LIST_DATA),
            "admin_count": len([i for i in data.USER_LIST_DATA if i.get('role', '').upper() == 'ADMIN']),
            "manager_count": len([i for i in data.USER_LIST_DATA if i.get('role', '').upper() == 'MANAGER']),
            "staff_count": len([i for i in data.USER_LIST_DATA if i.get('role', '').upper() == 'USER'])
        }

        return render_template(
            'manage/manage_overview.html',
            employees=paginated_users,
            stats=stats,
            dept_counts=dept_counts,
            role_counts=role_counts,
            status_counts=status_counts,
            floor_counts=floor_counts,
            floors=floors_list,
            departments=data.DEPARTMENTS,
            roles=data.ROLES,
            user_status=data.USER_STATUS_OPTIONS,
            search_q=search_q,
            selected_dept=selected_dept,
            selected_role=selected_role,
            selected_status=selected_status,
            selected_floor=selected_floor,
            current_page=page,
            total_pages=total_pages,
            total_records=total_filtered
        )

    @app.route('/manage/create', methods=['GET', 'POST'])
    def manage_create():
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            dept = request.form.get('department')
            role = request.form.get('role')
            position = request.form.get('floor') 
            emp_id = request.form.get('emp_id')
            start_date_str = request.form.get('start_date')
            
            try:
                dt_obj = datetime.strptime(start_date_str, '%Y-%m-%d')
                formatted_date = dt_obj.strftime("%d/%m/%Y")
            except:
                formatted_date = datetime.now().strftime("%d/%m/%Y")

            new_user = {
                "id": emp_id,
                "name": name,
                "email": email,
                "phone": phone,
                "dept": dept,
                "role": role,
                "position": position, 
                "status": "Hoạt động",
                "created_at": formatted_date
            }

            data.USER_LIST_DATA.insert(0, new_user)
            flash(f"Đã thêm nhân sự {name} thành công!", "success")
            return redirect(url_for('manage'))

        auto_id = generate_unique_id()
        floors = [f"Tầng {i}" for i in range(1, 11)]
        
        return render_template('manage/manage_create.html', 
                               auto_id=auto_id,
                               floors=floors,
                               departments=data.DEPARTMENTS, 
                               roles=data.ROLES)

    @app.route('/manage/detail/<string:id>')
    def user_detail(id):
        user = next((u for u in data.USER_LIST_DATA if u['id'] == id), None)
        if not user:
            flash("Không tìm thấy nhân sự này!", "warning")
            return redirect(url_for('manage'))
        return render_template('manage/manage_detail.html', user=user)

    @app.route('/manage/edit/<string:id>', methods=['GET', 'POST'])
    def user_edit(id):
        user = next((u for u in data.USER_LIST_DATA if u['id'] == id), None)
        if not user:
            flash("Không tìm thấy nhân sự để chỉnh sửa!", "warning")
            return redirect(url_for('manage'))

        if request.method == 'POST':
            # Cập nhật thông tin từ form manage_edit.html
            user['name'] = request.form.get('name')
            user['email'] = request.form.get('email')
            user['phone'] = request.form.get('phone')
            user['role'] = request.form.get('role')
            user['status'] = request.form.get('status')
            user['dept'] = request.form.get('dept')
            user['position'] = request.form.get('position')
            
            flash(f"Đã cập nhật thông tin cho {user['name']} thành công!", "success")
            return redirect(url_for('user_detail', id=id)) # Quay về trang chi tiết sau khi sửa

        floors = [f"Tầng {i}" for i in range(1, 11)]
        return render_template('manage/manage_edit.html', 
                               user=user, 
                               roles=data.ROLES, 
                               departments=data.DEPARTMENTS, 
                               floors=floors,
                               user_status=data.USER_STATUS_OPTIONS)

    @app.route('/manage/toggle-status/<string:id>')
    def user_toggle_status(id):
        """Hàm xử lý cho nút KHÓA TÀI KHOẢN"""
        user = next((u for u in data.USER_LIST_DATA if u['id'] == id), None)
        if user:
            old_status = user.get('status')
            # Nếu đang hoạt động thì khóa, nếu đang khóa thì mở lại
            if old_status in ["Hoạt động", "Đang hoạt động"]:
                user['status'] = "Khóa"
                flash(f"Đã khóa tài khoản của {user['name']}", "warning")
            else:
                user['status'] = "Hoạt động"
                flash(f"Đã mở khóa tài khoản cho {user['name']}", "success")
        return redirect(url_for('user_detail', id=id))

    @app.route('/manage/delete/<string:id>', methods=['GET', 'POST'])
    def user_delete(id):
        """Xử lý xóa nhân sự trực tiếp hoặc qua trang xác nhận"""
        user = next((u for u in data.USER_LIST_DATA if u['id'] == id), None)
        if not user:
            flash("Nhân sự không tồn tại hoặc đã bị xóa trước đó!", "warning")
            return redirect(url_for('manage'))

        # Xóa vĩnh viễn khỏi danh sách
        data.USER_LIST_DATA = [u for u in data.USER_LIST_DATA if u['id'] != id]
        flash(f"Đã xóa vĩnh viễn nhân sự {user['name']} ({id}) khỏi hệ thống", "danger")
        return redirect(url_for('manage'))