# app.py
from flask import Flask, render_template, request, redirect, url_for
from data import ASSIGN_DATA, INVENTORY_LIST, DATABASE_LOGS
from datetime import datetime

app = Flask(__name__)
app.secret_key = "hsu_assetone_2026"

@app.route('/')
def dashboard_overview():
    return redirect(url_for('assign_page'))

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
        "overdue": 0 # Có thể cập nhật logic sau
    }
    return render_template('assign/assign_overview.html', assigns=filtered, stats=stats, pending_requests=pending_requests)

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

@app.route('/assign/detail/<asset_name>')
def assign_detail(asset_name):
    info = next((item for item in INVENTORY_LIST if item["name"] == asset_name), None)
    # Tìm người đang sử dụng máy này
    holder = next((item for item in ASSIGN_DATA if item['asset'] == asset_name and item['status'] == 'Hoàn thành'), None)
    return render_template('assign/assign_detail.html', info=info, holder=holder)

@app.route('/assign/create', methods=['GET', 'POST'])
def assign_create():
    if request.method == 'POST':
        new = {"id": f"ASG-00{len(ASSIGN_DATA)+1}", "asset": request.form.get('asset_name'), 
               "receiver": request.form.get('receiver'), "date": datetime.now().strftime("%d/%m/%Y"), "status": "Hoàn thành"}
        ASSIGN_DATA.insert(0, new)
        return redirect(url_for('assign_page'))
    return render_template('assign/assign_create.html', inventory=INVENTORY_LIST)

@app.route('/assign/request', methods=['GET', 'POST'])
def request_create():
    if request.method == 'POST':
        new = {"id": f"REQ-0{len(ASSIGN_DATA)+1}", "asset": request.form.get('asset_name'), 
               "receiver": request.form.get('requester'), "date": datetime.now().strftime("%d/%m/%Y"), "status": "Chờ duyệt"}
        ASSIGN_DATA.insert(0, new)
        return redirect(url_for('assign_page'))
    return render_template('assign/request_create.html', inventory=INVENTORY_LIST)

@app.route('/assets')
def assets_page(): return render_template('assets/assets.html')
@app.route('/return')
def return_page(): return render_template('return/return.html')
@app.route('/report')
def report_page(): return render_template('report/report.html', logs=DATABASE_LOGS)

if __name__ == "__main__":
    app.run(debug=True)