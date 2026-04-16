from flask import Flask, render_template, request, redirect, url_for
from data import ASSIGN_DATA, INVENTORY_LIST, DATABASE_LOGS
from datetime import datetime
import math # Thư viện tính toán số trang

app = Flask(__name__)
app.secret_key = "hsu_assetone_2026"

# --- 1. TRANG CHỦ: TỔNG QUAN HỆ THỐNG ---
@app.route('/')
def dashboard_overview():
    # Tính toán thống kê dựa trên dữ liệu thực tế từ ASSIGN_DATA
    using_count = len([i for i in ASSIGN_DATA if i['status'] == 'Hoàn thành'])
    
    # Cập nhật stats dựa trên độ dài thực tế của danh sách 128+ tài sản
    total_real = len(ASSIGN_DATA)
    stats = {
        "total": total_real,
        "using": using_count,
        "available": total_real - using_count - 10,
        "maintenance": 10
    }
    
    # Lấy 4 hoạt động mới nhất để hiển thị
    recent_activities = ASSIGN_DATA[:4] 
    
    return render_template('dashboard/overview.html', stats=stats, activities=recent_activities)


# --- 2. TRANG QUẢN LÝ TÀI SẢN (Cập nhật tìm kiếm Tên & Mã tài sản) ---
@app.route('/assets')
def assets_page(): 
    # Lấy các tham số lọc từ URL
    search_q = request.args.get('search', '').strip().lower()
    sel_type = request.args.get('type', 'Tất cả')
    sel_dept = request.args.get('department', 'Tất cả')
    sel_status = request.args.get('status', 'Tất cả')
    
    # Logic lọc dữ liệu
    filtered = ASSIGN_DATA
    
    # CẬP NHẬT: Tìm kiếm theo cả Tên tài sản (asset) và Mã tài sản (asset_code)
    if search_q:
        filtered = [
            i for i in filtered if 
            search_q in i.get('asset', '').lower() or 
            search_q in i.get('asset_code', '').lower() or
            search_q in i.get('id', '').lower() # Tìm theo ID hệ thống nếu cần
        ]
    
    # Giữ nguyên các bộ lọc cũ
    if sel_type != 'Tất cả':
        filtered = [i for i in filtered if i.get('type') == sel_type]
        
    if sel_dept != 'Tất cả':
        filtered = [i for i in filtered if i.get('department') == sel_dept]
        
    if sel_status != 'Tất cả':
        if sel_status == 'using':
            filtered = [i for i in filtered if i['status'] in ['using', 'Hoàn thành']]
        else:
            filtered = [i for i in filtered if i['status'] == sel_status]

    # --- LOGIC PHÂN TRANG ---
    page = request.args.get('page', 1, type=int) 
    per_page = 10 
    total_assets = len(filtered)
    total_pages = math.ceil(total_assets / per_page) 

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


# --- 3. CHỨC NĂNG: THÊM THIẾT BỊ MỚI (Giữ nguyên) ---
@app.route('/assets/create', methods=['GET', 'POST'])
def asset_create():
    if request.method == 'POST':
        asset_code = request.form.get('asset_code')
        asset_name = request.form.get('asset_name')
        asset_type = request.form.get('type')
        status = request.form.get('status')
        receiver = request.form.get('receiver')
        department = request.form.get('department')
        location = request.form.get('location')
        warranty = request.form.get('warranty')
        spec = request.form.get('spec')

        new_id = f"ASG-{str(len(ASSIGN_DATA) + 1).zfill(3)}"

        new_asset = {
            "id": new_id,
            "asset_code": asset_code,
            "asset": asset_name, 
            "type": asset_type,
            "receiver": receiver,
            "department": department,
            "location": location,
            "date": datetime.now().strftime("%d/%m/%Y"),
            "warranty": warranty,
            "status": status
        }
        
        ASSIGN_DATA.insert(0, new_asset)

        INVENTORY_LIST.append({
            "name": asset_name,
            "spec": spec if spec else "Thông số đang cập nhật",
            "warranty": warranty
        })

        return redirect(url_for('assets_page'))

    return render_template('assets/asset_create.html')


# --- 4. CHỨC NĂNG: XEM CHI TIẾT TÀI SẢN (Giữ nguyên) ---
@app.route('/assets/detail/<string:asset_id>')
def asset_detail_view(asset_id):
    info = next((item for item in ASSIGN_DATA if item["id"] == asset_id), None)
    
    if not info:
        return redirect(url_for('assets_page'))
    
    specs = next((item for item in INVENTORY_LIST if item["name"] == info['asset']), {
        "spec": "Thông số kỹ thuật đang được cập nhật",
        "warranty": "N/A"
    })
    
    return render_template('assets/asset_detail.html', info=info, specs=specs)


# --- 5. TRANG QUẢN LÝ CẤP PHÁT (Giữ nguyên) ---
@app.route('/assign')
def assign_page():
    search_q = request.args.get('search', '').strip().lower()
    
    if search_q:
        filtered = [i for i in ASSIGN_DATA if search_q in i['receiver'].lower() or search_q in i['asset'].lower()]
    else:
        filtered = ASSIGN_DATA

    pending_requests = [i for i in ASSIGN_DATA if i['status'] == 'Chờ duyệt']
    
    stats = {
        "total": len(ASSIGN_DATA),
        "pending": len(pending_requests),
        "overdue": 0
    }
    return render_template('assign/assign_overview.html', assigns=filtered, stats=stats, pending_requests=pending_requests)


# --- 6. XỬ LÝ PHÊ DUYỆT / TỪ CHỐI YÊU CẦU (Giữ nguyên) ---
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


# --- 7. TẠO MỚI CẤP PHÁT & GỬI YÊU CẦU MƯỢN (Giữ nguyên) ---
@app.route('/assign/create', methods=['GET', 'POST'])
def assign_create():
    if request.method == 'POST':
        new = {
            "id": f"ASG-00{len(ASSIGN_DATA)+1}", 
            "asset": request.form.get('asset_name'), 
            "receiver": request.form.get('receiver'), 
            "date": datetime.now().strftime("%d/%m/%Y"), 
            "status": "Hoàn thành"
        }
        ASSIGN_DATA.insert(0, new) 
        return redirect(url_for('assign_page'))
    return render_template('assign/assign_create.html', inventory=INVENTORY_LIST)

@app.route('/assign/request', methods=['GET', 'POST'])
def request_create():
    if request.method == 'POST':
        new = {
            "id": f"REQ-0{len(ASSIGN_DATA)+1}", 
            "asset": request.form.get('asset_name'), 
            "receiver": request.form.get('requester'), 
            "date": datetime.now().strftime("%d/%m/%Y"), 
            "status": "Chờ duyệt"
        }
        ASSIGN_DATA.insert(0, new)
        return redirect(url_for('assign_page'))
    return render_template('assign/request_create.html', inventory=INVENTORY_LIST)


# --- 8. CÁC TRANG PHỤ KHÁC (Giữ nguyên) ---
@app.route('/login')
def login(): 
    return render_template('login/login.html')

@app.route('/manage')
def manage(): 
    return render_template('manage/manage.html')

@app.route('/report')
def report_page(): 
    return render_template('report/report.html', logs=DATABASE_LOGS)


if __name__ == "__main__":
    app.run(debug=True)