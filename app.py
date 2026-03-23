from flask import Flask, render_template

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
    return render_template('report/report.html')

if __name__ == "__main__":
    app.run(debug=True)