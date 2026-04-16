from flask import Flask, render_template, request, redirect, url_for
from data import ASSIGN_DATA, INVENTORY_LIST, DATABASE_LOGS
from datetime import datetime

app = Flask(__name__)
app.secret_key = "hsu_assetone_2026"


# --- 1. TRANG CHỦ ---
@app.route('/')
def dashboard_overview():
    using_count = len([i for i in ASSIGN_DATA if i.get('status') in ['Hoàn thành', 'Đang sử dụng']])

    stats = {
        "total": 128 + len(ASSIGN_DATA),
        "using": using_count,
        "available": max(0, 128 - using_count - 10),
        "maintenance": 10
    }

    recent_activities = ASSIGN_DATA[:4]
    return render_template('dashboard/overview.html', stats=stats, activities=recent_activities)


# --- 2. TRANG TÀI SẢN ---
@app.route('/assets')
def assets_page():
    search_q = request.args.get('search', '').strip().lower()

    if search_q:
        filtered = [
            i for i in ASSIGN_DATA
            if search_q in i.get('asset', '').lower()
            or search_q in i.get('id', '').lower()
        ]
    else:
        filtered = ASSIGN_DATA

    return render_template('assets/assets.html', assets=filtered)


# --- 3. THÊM TÀI SẢN ---
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


# --- 4. CHI TIẾT TÀI SẢN ---
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


# --- 5. TRANG CẤP PHÁT ---
@app.route('/assign')
def assign_page():
    search_q = request.args.get('search', '').strip().lower()

    if search_q:
        filtered = [
            i for i in ASSIGN_DATA
            if search_q in i.get('receiver', '').lower()
            or search_q in i.get('asset', '').lower()
            or search_q in i.get('status', '').lower()
            or search_q in i.get('id', '').lower()
        ]
    else:
        filtered = ASSIGN_DATA

    pending_requests = [i for i in ASSIGN_DATA if i.get('status') == 'Chờ duyệt']

    stats = {
        "total": len(ASSIGN_DATA),
        "pending": len(pending_requests),
        "overdue": 0
    }

    return render_template(
        'assign/assign_overview.html',
        assigns=filtered,
        stats=stats
    )


# --- 6. CHI TIẾT CẤP PHÁT ---
@app.route('/assign/detail/<string:id>')
def assign_detail(id):
    holder = next((item for item in ASSIGN_DATA if item["id"] == id), None)

    if not holder:
        return redirect(url_for('assign_page'))

    info = next((item for item in INVENTORY_LIST if item["name"] == holder["asset"]), None)

    return render_template('assign/assign_detail.html', info=info, holder=holder)


# --- 7. DUYỆT / TỪ CHỐI ---
@app.route('/assign/approve/<string:id>')
def approve_request(id):
    for item in ASSIGN_DATA:
        if item['id'] == id:
            item['status'] = 'Hoàn thành'
            item['date'] = datetime.now().strftime("%d/%m/%Y")
            item['updated_at'] = datetime.now().strftime("%d/%m/%Y")
            break
    return redirect(url_for('assign_page'))


@app.route('/assign/reject/<string:id>')
def reject_request(id):
    for i, item in enumerate(ASSIGN_DATA):
        if item['id'] == id:
            ASSIGN_DATA.pop(i)
            break
    return redirect(url_for('assign_page'))


# --- 8. CẤP PHÁT MỚI ---
@app.route('/assign/create', methods=['GET', 'POST'])
def assign_create():
    if request.method == 'POST':
        new = {
            "id": f"ASG-{str(len(ASSIGN_DATA) + 1).zfill(3)}",
            "asset": request.form.get('asset_name'),
            "receiver": request.form.get('receiver'),
            "date": datetime.now().strftime("%d/%m/%Y"),
            "status": "Hoàn thành"
        }
        ASSIGN_DATA.insert(0, new)
        return redirect(url_for('assign_page'))

    return render_template('assign/assign_create.html', inventory=INVENTORY_LIST)


# --- 9. GỬI YÊU CẦU ---
@app.route('/assign/request', methods=['GET', 'POST'])
def request_create():
    if request.method == 'POST':
        new = {
            "id": f"REQ-{str(len(ASSIGN_DATA) + 1).zfill(3)}",
            "asset": request.form.get('asset_name'),
            "receiver": request.form.get('requester'),
            "date": datetime.now().strftime("%d/%m/%Y"),
            "status": "Chờ duyệt"
        }
        ASSIGN_DATA.insert(0, new)
        return redirect(url_for('assign_page'))

    return render_template('assign/request_create.html', inventory=INVENTORY_LIST)


# --- 10. SỬA CẤP PHÁT ---
@app.route('/assign/edit/<string:id>', methods=['GET', 'POST'])
def assign_edit(id):
    item = next((x for x in ASSIGN_DATA if x["id"] == id), None)

    if not item:
        return redirect(url_for('assign_page'))

    if request.method == 'POST':
        receiver = request.form.get('receiver', '').strip()
        status = request.form.get('status', '').strip()
        note = request.form.get('note', '').strip()

        valid_status = [
            'Đang sử dụng',
            'Báo hỏng',
            'Mất',
            'Thu hồi',
            'Hoàn thành',
            'Chờ duyệt'
        ]

        if receiver:
            item['receiver'] = receiver

        if status in valid_status:
            item['status'] = status

        item['note'] = note
        item['updated_at'] = datetime.now().strftime("%d/%m/%Y")

        if status == 'Thu hồi':
            item['receiver'] = 'Kho IT'

        return redirect(url_for('assign_page'))

    return render_template('assign/assign_edit.html', item=item)


# --- 11. TRANG PHỤ ---
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