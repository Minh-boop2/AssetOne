from flask import Flask, render_template, request, redirect, url_for, flash
from data import ASSIGN_DATA, INVENTORY_LIST, DATABASE_LOGS
from datetime import datetime

app = Flask(__name__)
app.secret_key = "hsu_assetone_2026"

# --- DANH SÁCH TÀI KHOẢN (SỬ DỤNG TẠM THỜI) ---
USERS = {
    "admin": "123",
    "chau": "2004"
}

# --- 1. ĐIỀU HƯỚNG MẶC ĐỊNH ---
@app.route('/')
def index():
    return redirect(url_for('login_page'))

# --- 2. XỬ LÝ ĐĂNG NHẬP & ĐĂNG KÝ ---
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        
        if user in USERS and USERS[user] == pw:
            return redirect(url_for('dashboard_overview'))
        else:
            flash("Tên đăng nhập hoặc mật khẩu không đúng!", "danger")
            
    return render_template('login/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        new_user = request.form.get('username')
        new_pw = request.form.get('password')
        
        if new_user in USERS:
            flash("Tên đăng nhập đã tồn tại!", "warning")
        else:
            USERS[new_user] = new_pw
            flash("Tạo tài khoản thành công! Mời Châu đăng nhập.", "success")
            return redirect(url_for('login_page'))
            
    return render_template('login/register.html')

@app.route('/login/overview')
def login_overview():
    return render_template('login/login_overview.html')

# --- 3. TỔNG QUAN HỆ THỐNG (DASHBOARD) ---
@app.route('/dashboard')
def dashboard_overview():
    using_count = len([i for i in ASSIGN_DATA if i['status'] == 'Hoàn thành'])
    pending_count = len([i for i in ASSIGN_DATA if i['status'] == 'Chờ duyệt'])
    
    stats = {
        "total": 128,
        "using": using_count,
        "available": 128 - using_count - 10,
        "maintenance": 10
    }
    recent_activities = ASSIGN_DATA[:4] 
    return render_template('dashboard/overview.html', stats=stats, activities=recent_activities)

# --- 4. QUẢN LÝ CẤP PHÁT ---
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

# --- 5. PHÊ DUYỆT / TỪ CHỐI ---
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

# --- 6. CHI TIẾT TÀI SẢN ---
@app.route('/assign/detail/<asset_name>')
def assign_detail(asset_name):
    info = next((item for item in INVENTORY_LIST if item["name"] == asset_name), None)
    holder = next((item for item in ASSIGN_DATA if item['asset'] == asset_name and item['status'] == 'Hoàn thành'), None)
    return render_template('assign/assign_detail.html', info=info, holder=holder)

# --- 7. TẠO CẤP PHÁT & GỬI YÊU CẦU ---
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
@app.route('/assets')
def assets_page(): 
    return render_template('assets/assets.html')

@app.route('/manage')
def manage():
    return render_template('manage/manage.html')

@app.route('/report')
def report_page(): 
    return render_template('report/report.html', logs=DATABASE_LOGS)

# ===========================================================
# PHẦN BỔ SUNG MỚI (QUÊN MẬT KHẨU & TÙY CHỈNH THEO YÊU CẦU)
# ===========================================================

@app.route('/forgot-password')
def forgot_password():
    """Route trả về trang quên mật khẩu riêng biệt"""
    return render_template('login/forgot_password.html')

if __name__ == "__main__":
    app.run(debug=True)