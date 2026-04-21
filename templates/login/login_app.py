from flask import render_template, request, redirect, url_for


def register_login_routes(app):
    @app.route('/welcome')
    def welcome_page():
        return render_template('login/login_overview.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login_page():
        if request.method == 'POST':
            if request.form.get('username') == "admin" and request.form.get('password') == "123":
                return redirect(url_for('dashboard_overview'))
        return render_template('login/login.html')
    

    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        return render_template('login/forgot_password.html')
    
    