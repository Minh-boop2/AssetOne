from flask import render_template
from data import USER_LIST_DATA, DATABASE_LOGS, ASSIGN_DATA 

def register_admin_profile_routes(app):
    @app.route('/admin-profile')
    def profile_page():
        # Lấy thông tin Admin đầu tiên
        admin = USER_LIST_DATA[0]
        
        # Lấy tối đa 4 nhật ký hoạt động để đảm bảo chiều cao vừa vặn 1 trang
        logs = [log for log in DATABASE_LOGS if log.get('user') == 'Admin'][:4]
        
        # Lọc danh sách tài sản do admin này nắm giữ
        admin_assets = [a for a in ASSIGN_DATA if a['receiver'] == admin['name']]

        return render_template('admin_profile/admin_profile.html', 
                               admin=admin, 
                               logs=logs, 
                               assign_data=admin_assets)