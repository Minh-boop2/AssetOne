from flask import Flask, render_template, request
# Import dữ liệu từ file data.py vừa tạo
from data import DATABASE_LOGS 

app = Flask(__name__)

@app.route('/')
def dashboard_overview():
    return render_template('dashboard/overview.html')

@app.route('/assets')
def assets_page():
    return render_template('assets/assets.html')

@app.route('/assign')
def assign_page():
    return render_template('assign/assign.html')

@app.route('/return')
def return_page():
    return render_template('return/return.html')

@app.route('/report')
def report_page():
    f_dept = request.args.get('department', 'Tất cả')
    f_type = request.args.get('type', 'Tất cả')

    # Logic lọc vẫn giữ nguyên, nhưng dùng DATABASE_LOGS lấy từ file data.py
    filtered_logs = DATABASE_LOGS
    if f_dept != 'Tất cả':
        filtered_logs = [log for log in filtered_logs if log['dept'] == f_dept]
    if f_type != 'Tất cả':
        filtered_logs = [log for log in filtered_logs if log['type'] == f_type]

    return render_template('report/report.html', 
                           logs=filtered_logs, 
                           selected_dept=f_dept, 
                           selected_type=f_type)

if __name__ == "__main__":
    app.run(debug=True)