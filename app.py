from flask import Flask, render_template, request, redirect, url_for
from data import ASSIGN_DATA, INVENTORY_LIST, DATABASE_LOGS
from datetime import datetime

app = Flask(__name__)
app.secret_key = "hsu_assetone_2026"

# --- 1. TRANG CHỦ: TỔNG QUAN HỆ THỐNG ---
@app.route('/')
def dashboard_overview():
    # Tính toán thống kê dựa trên dữ liệu thực tế từ ASSIGN_DATA
    using_count = len([i for i in ASSIGN_DATA if i['status'] == 'Hoàn thành'])
    
    # Giả lập các chỉ số thống kê
    stats = {
        "total": 128 + len(ASSIGN_DATA),
        "using": using_count,
        "available": 128 - using_count - 10,
        "maintenance": 10
    }
    
    # Lấy 4 hoạt động mới nhất để hiển thị
    recent_activities = ASSIGN_DATA[:4] 
    
    return render_template('dashboard/overview.html', stats=stats, activities=recent_activities)


# --- 2. TRANG QUẢN LÝ TÀI SẢN (Danh sách tổng) ---
@app.route('/assets')
def assets_page(): 
    # Logic lọc tìm kiếm theo tên tài sản hoặc mã tài sản (ID)
    search_q = request.args.get('search', '').strip().lower()
    if search_q:
        filtered = [i for i in ASSIGN_DATA if search_q in i['asset'].lower() or search_q in i['id'].lower()]
    else:
        filtered = ASSIGN_DATA
        
    return render_template('assets/assets.html', assets=filtered)


# --- 3. CHỨC NĂNG: THÊM THIẾT BỊ MỚI (UPDATE MỚI) ---
@app.route('/assets/create', methods=['GET', 'POST'])
def asset_create():
    if request.method == 'POST':
        # Lấy dữ liệu từ form người dùng nhập
        asset_code = request.form.get('asset_code')
        asset_name = request.form.get('asset_name')
        asset_type = request.form.get('type')
        status = request.form.get('status')
        receiver = request.form.get('receiver')
        department = request.form.get('department')
        location = request.form.get('location')
        warranty = request.form.get('warranty')
        spec = request.form.get('spec')

        # Tạo ID hệ thống tự động dựa trên độ dài danh sách
        new_id = f"ASG-{str(len(ASSIGN_DATA) + 1).zfill(3)}"

        # Tạo bản ghi mới cho danh sách hiển thị
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
        
        # Thêm vào đầu danh sách dữ liệu
        ASSIGN_DATA.insert(0, new_asset)

        # Thêm vào kho thông số kỹ thuật (để xem chi tiết không bị lỗi)
        INVENTORY_LIST.append({
            "name": asset_name,
            "spec": spec if spec else "Thông số đang cập nhật",
            "warranty": warranty
        })

        return redirect(url_for('assets_page'))

    return render_template('assets/asset_create.html')


# --- 4. CHỨC NĂNG: XEM CHI TIẾT TÀI SẢN ---
@app.route('/assets/detail/<string:asset_id>')
def asset_detail_view(asset_id):
    # Tìm thông tin cấp phát trong ASSIGN_DATA bằng ID
    info = next((item for item in ASSIGN_DATA if item["id"] == asset_id), None)
    
    if not info:
        return redirect(url_for('assets_page'))
    
    # Tìm cấu hình kỹ thuật trong INVENTORY_LIST dựa trên tên tài sản
    specs = next((item for item in INVENTORY_LIST if item["name"] == info['asset']), {
        "spec": "Thông số kỹ thuật đang được cập nhật",
        "warranty": "N/A"
    })
    
    return render_template('assets/asset_detail.html', info=info, specs=specs)


# --- 5. TRANG QUẢN LÝ CẤP PHÁT (Phòng IT Duyệt/Cấp) ---
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


# --- 6. XỬ LÝ PHÊ DUYỆT / TỪ CHỐI YÊU CẦU ---
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


# --- 7. TẠO MỚI CẤP PHÁT & GỬI YÊU CẦU MƯỢN ---
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


# --- 8. CÁC TRANG PHỤ KHÁC ---
@app.route('/login')
def login(): 
    return render_template('login/login.html')

@app.route('/manage')
def manage(): 
    return render_template('manage/manage.html')

@app.route('/report')
def report_page(): 
    return render_template('report/report.html', logs=DATABASE_LOGS)


# --- CHẠY ỨNG DỤNG ---
if __name__ == "__main__":
    app.run(debug=True)