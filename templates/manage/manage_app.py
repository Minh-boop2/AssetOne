from flask import render_template, request, redirect, url_for, flash
import requests
import random
import string
from datetime import datetime, timezone, timedelta


API_BASE_URL = "http://127.0.0.1:5001/api"
PER_PAGE = 10

VN_TZ = timezone(timedelta(hours=7))


ROLE_OPTIONS = [
    {"value": "ADMIN", "label": "Admin"},
    {"value": "QUAN_LY", "label": "Quản lý"},
    {"value": "NHAN_VIEN", "label": "Nhân viên"},
]

STATUS_OPTIONS = [
    {"value": "HOAT_DONG", "label": "Hoạt động"},
    {"value": "NGUNG_HOAT_DONG", "label": "Ngưng hoạt động"},
]


DEFAULT_DEPARTMENTS = [
    "Phòng Kỹ Thuật",
    "Phòng Hành Chính",
    "Phòng IT",
    "Phòng Thiết Kế",
    "Phòng Nhân Sự",
    "Phòng Kế Toán",
]

DEFAULT_FLOORS = [f"Tầng {i}" for i in range(1, 11)]


ROLE_LABELS = {item["value"]: item["label"] for item in ROLE_OPTIONS}
STATUS_LABELS = {item["value"]: item["label"] for item in STATUS_OPTIONS}


def now_vietnam():
    return datetime.now(VN_TZ)


def format_datetime_vietnam(value):
    """
    Chuẩn hóa ngày giờ để hiển thị theo giờ Việt Nam.

    Backend tốt nhất nên trả created_at dạng:
    05/05/2026 10:30

    Nhưng nếu backend trả ISO dạng:
    2026-05-05T03:30:00Z
    hoặc:
    2026-05-05T03:30:00+00:00

    thì frontend vẫn tự convert sang giờ Việt Nam.
    """
    if not value:
        return ""

    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        value = value.strip()

        if not value:
            return ""

        # Nếu backend đã format sẵn dd/mm/yyyy thì giữ nguyên
        if "/" in value:
            return value

        try:
            iso_value = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso_value)
        except ValueError:
            return value
    else:
        return str(value)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    dt_vn = dt.astimezone(VN_TZ)

    return dt_vn.strftime("%d/%m/%Y %H:%M")


def call_api(method, path, **kwargs):
    try:
        response = requests.request(
            method,
            f"{API_BASE_URL}{path}",
            timeout=8,
            **kwargs
        )

        try:
            payload = response.json()
        except ValueError:
            payload = {
                "success": False,
                "message": response.text
            }

        return payload, response.status_code

    except requests.RequestException as e:
        return {
            "success": False,
            "message": f"Không kết nối được backend API: {e}"
        }, 503


def clean_api_params(params):
    return {
        key: value
        for key, value in params.items()
        if value is not None and value != "" and value != "Tất cả"
    }


def normalize_role(value):
    if not value:
        return "NHAN_VIEN"

    value = value.strip().upper()

    mapping = {
        "ADMIN": "ADMIN",
        "QUẢN LÝ": "QUAN_LY",
        "QUAN_LY": "QUAN_LY",
        "MANAGER": "QUAN_LY",
        "NHÂN VIÊN": "NHAN_VIEN",
        "NHAN_VIEN": "NHAN_VIEN",
        "USER": "NHAN_VIEN",
        "STAFF": "NHAN_VIEN",
    }

    return mapping.get(value, value)


def normalize_status(value):
    if not value:
        return "HOAT_DONG"

    value = value.strip().upper()

    mapping = {
        "HOẠT ĐỘNG": "HOAT_DONG",
        "ĐANG HOẠT ĐỘNG": "HOAT_DONG",
        "HOAT_DONG": "HOAT_DONG",
        "KHÓA": "NGUNG_HOAT_DONG",
        "NGƯNG HOẠT ĐỘNG": "NGUNG_HOAT_DONG",
        "NGUNG_HOAT_DONG": "NGUNG_HOAT_DONG",
    }

    return mapping.get(value, value)


def get_option_label(options, value, default_label):
    if not value or value == "Tất cả":
        return default_label

    for item in options:
        if item["value"] == value:
            return item["label"]

    return default_label


def map_user_for_template(user):
    role_code = normalize_role(user.get("role"))
    status_code = normalize_status(user.get("status"))

    created_at_vn = format_datetime_vietnam(user.get("created_at"))
    updated_at_vn = format_datetime_vietnam(user.get("updated_at"))

    return {
        # MongoDB _id, dùng cho detail / edit / delete
        "db_id": user.get("id"),

        # Mã nhân viên, dùng để hiển thị ngoài bảng
        "id": user.get("employee_code") or user.get("id"),

        "name": user.get("full_name") or "",
        "email": user.get("email") or "",
        "phone": user.get("phone") or "",
        "dept": user.get("department") or "",
        "position": user.get("floor") or "",

        "role_code": role_code,
        "role": ROLE_LABELS.get(role_code, role_code),

        "status_code": status_code,
        "status": STATUS_LABELS.get(status_code, status_code),

        # created_at dùng làm ngày tham gia
        "join_date": created_at_vn,
        "created_at": created_at_vn,
        "updated_at": updated_at_vn,
    }


def fetch_users_from_api(params=None):
    params = params or {}

    payload, status_code = call_api("GET", "/users", params=params)

    if status_code >= 400 or not payload.get("success"):
        return [], {
            "page": 1,
            "limit": PER_PAGE,
            "total": 0,
            "total_pages": 1
        }, payload.get("message", "Không lấy được danh sách user")

    return (
        payload.get("data", []),
        payload.get("pagination", {}),
        None
    )


def fetch_user_stats_from_api():
    payload, status_code = call_api("GET", "/users/stats")

    if status_code >= 400 or not payload.get("success"):
        return {}, payload.get("message", "Không lấy được thống kê user")

    return payload.get("data", {}), None


def fetch_user_detail(user_db_id):
    payload, status_code = call_api("GET", f"/users/{user_db_id}")

    if status_code >= 400 or not payload.get("success"):
        return None, payload.get("message", "Không tìm thấy nhân sự")

    return payload.get("data"), None


def generate_unique_id():
    """
    Tạo mã nhân viên tạm để fill form.
    Backend vẫn là nơi kiểm tra trùng employee_code thật sự.
    Dùng giờ Việt Nam để mã dễ đọc và đúng timezone.
    """
    today = now_vietnam().strftime("%Y%m%d%H%M%S")
    random_part = ''.join(random.choices(string.digits, k=3))

    return f"HSU-{today}-{random_part}"


def build_departments_from_stats(stats_payload):
    stats_payload = stats_payload or {}

    dept_counts = stats_payload.get("dept_counts", {})
    departments_from_db = stats_payload.get("departments", sorted(dept_counts.keys()))

    departments = sorted(set(DEFAULT_DEPARTMENTS + departments_from_db))

    return departments


def build_floors_from_stats(stats_payload):
    stats_payload = stats_payload or {}

    floor_counts = stats_payload.get("floor_counts", {})
    floors_from_db = stats_payload.get("floors", sorted(floor_counts.keys()))

    floors = sorted(set(DEFAULT_FLOORS + floors_from_db))

    return floors


def register_manage_routes(app):

    @app.route('/manage')
    def manage():
        search_q = request.args.get('search', '').strip()
        selected_dept = request.args.get('department', 'Tất cả')
        selected_role = request.args.get('role', 'Tất cả')
        selected_status = request.args.get('status', 'Tất cả')
        selected_floor = request.args.get('floor', 'Tất cả')
        page = request.args.get('page', 1, type=int)

        if selected_role and selected_role != "Tất cả":
            selected_role = normalize_role(selected_role)

        if selected_status and selected_status != "Tất cả":
            selected_status = normalize_status(selected_status)

        api_params = clean_api_params({
            "page": page,
            "limit": PER_PAGE,
            "keyword": search_q,
            "department": selected_dept,
            "role": selected_role,
            "status": selected_status,
            "floor": selected_floor,
        })

        users_raw, pagination, users_error = fetch_users_from_api(api_params)

        if users_error:
            flash(users_error, "danger")

        employees = [map_user_for_template(user) for user in users_raw]

        stats_payload, stats_error = fetch_user_stats_from_api()

        if stats_error:
            flash(stats_error, "danger")
            stats_payload = {}

        stats = stats_payload.get("stats", {
            "total": 0,
            "admin_count": 0,
            "manager_count": 0,
            "staff_count": 0
        })

        dept_counts = stats_payload.get("dept_counts", {})
        role_counts = stats_payload.get("role_counts", {})
        status_counts = stats_payload.get("status_counts", {})
        floor_counts = stats_payload.get("floor_counts", {})

        departments = build_departments_from_stats(stats_payload)
        floors = build_floors_from_stats(stats_payload)

        current_page = pagination.get("page", page)
        total_pages = pagination.get("total_pages", 1)
        total_records = pagination.get("total", 0)

        selected_role_label = get_option_label(
            ROLE_OPTIONS,
            selected_role,
            "Tất cả chức vụ"
        )

        selected_status_label = get_option_label(
            STATUS_OPTIONS,
            selected_status,
            "Tất cả trạng thái"
        )

        return render_template(
            'manage/manage_overview.html',
            employees=employees,
            stats=stats,
            dept_counts=dept_counts,
            role_counts=role_counts,
            status_counts=status_counts,
            floor_counts=floor_counts,
            floors=floors,
            departments=departments,
            roles=ROLE_OPTIONS,
            user_status=STATUS_OPTIONS,
            search_q=search_q,
            selected_dept=selected_dept,
            selected_role=selected_role,
            selected_role_label=selected_role_label,
            selected_status=selected_status,
            selected_status_label=selected_status_label,
            selected_floor=selected_floor,
            current_page=current_page,
            total_pages=total_pages,
            total_records=total_records
        )

    @app.route('/manage/create', methods=['GET', 'POST'])
    def manage_create():
        stats_payload, _ = fetch_user_stats_from_api()
        departments = build_departments_from_stats(stats_payload)
        floors = build_floors_from_stats(stats_payload)

        if request.method == 'POST':
            emp_id = request.form.get('emp_id')
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            dept = request.form.get('department')
            role = normalize_role(request.form.get('role'))
            floor = request.form.get('floor')
            password = request.form.get('password') or "123"

            new_user = {
                "employee_code": emp_id,
                "full_name": name,
                "email": email,
                "phone": phone,
                "department": dept,
                "floor": floor,
                "role": role,
                "status": "HOAT_DONG",
                "password": password
            }

            payload, status_code = call_api("POST", "/users", json=new_user)

            if status_code >= 400 or not payload.get("success"):
                flash(payload.get("message", "Thêm nhân sự thất bại"), "danger")
                return redirect(url_for('manage_create'))

            flash(f"Đã thêm nhân sự {name} thành công!", "success")
            return redirect(url_for('manage'))

        auto_id = generate_unique_id()

        return render_template(
            'manage/manage_create.html',
            auto_id=auto_id,
            floors=floors,
            departments=departments,
            roles=ROLE_OPTIONS
        )

    @app.route('/manage/detail/<string:id>')
    def user_detail(id):
        user_raw, error = fetch_user_detail(id)

        if error:
            flash(error, "warning")
            return redirect(url_for('manage'))

        user = map_user_for_template(user_raw)

        return render_template(
            'manage/manage_detail.html',
            user=user
        )

    @app.route('/manage/edit/<string:id>', methods=['GET', 'POST'])
    def user_edit(id):
        user_raw, error = fetch_user_detail(id)

        if error:
            flash(error, "warning")
            return redirect(url_for('manage'))

        stats_payload, _ = fetch_user_stats_from_api()
        departments = build_departments_from_stats(stats_payload)
        floors = build_floors_from_stats(stats_payload)

        if request.method == 'POST':
            update_data = {
                "full_name": request.form.get('name'),
                "email": request.form.get('email'),
                "phone": request.form.get('phone'),
                "role": normalize_role(request.form.get('role')),
                "status": normalize_status(request.form.get('status')),
                "department": request.form.get('dept') or request.form.get('department'),
                "floor": request.form.get('position') or request.form.get('floor'),
            }

            password = request.form.get('password')

            if password:
                update_data["password"] = password

            payload, status_code = call_api(
                "PUT",
                f"/users/{id}",
                json=update_data
            )

            if status_code >= 400 or not payload.get("success"):
                flash(payload.get("message", "Cập nhật nhân sự thất bại"), "danger")
                return redirect(url_for('user_edit', id=id))

            updated_user = map_user_for_template(payload.get("data"))
            flash(f"Đã cập nhật thông tin cho {updated_user['name']} thành công!", "success")
            return redirect(url_for('user_detail', id=id))

        user = map_user_for_template(user_raw)

        return render_template(
            'manage/manage_edit.html',
            user=user,
            roles=ROLE_OPTIONS,
            departments=departments,
            floors=floors,
            user_status=STATUS_OPTIONS
        )

    @app.route('/manage/toggle-status/<string:id>')
    def user_toggle_status(id):
        user_raw, error = fetch_user_detail(id)

        if error:
            flash(error, "warning")
            return redirect(url_for('manage'))

        user = map_user_for_template(user_raw)

        if user["status_code"] == "HOAT_DONG":
            new_status = "NGUNG_HOAT_DONG"
            message = f"Đã ngưng hoạt động tài khoản của {user['name']}"
            category = "warning"
        else:
            new_status = "HOAT_DONG"
            message = f"Đã mở hoạt động tài khoản cho {user['name']}"
            category = "success"

        payload, status_code = call_api(
            "PUT",
            f"/users/{id}",
            json={"status": new_status}
        )

        if status_code >= 400 or not payload.get("success"):
            flash(payload.get("message", "Cập nhật trạng thái thất bại"), "danger")
            return redirect(url_for('user_detail', id=id))

        flash(message, category)
        return redirect(url_for('user_detail', id=id))

    @app.route('/manage/delete/<string:id>', methods=['GET', 'POST'])
    def user_delete(id):
        user_raw, error = fetch_user_detail(id)

        if error:
            flash("Nhân sự không tồn tại hoặc đã bị xóa trước đó!", "warning")
            return redirect(url_for('manage'))

        user = map_user_for_template(user_raw)

        payload, status_code = call_api("DELETE", f"/users/{id}")

        if status_code >= 400 or not payload.get("success"):
            flash(payload.get("message", "Xóa nhân sự thất bại"), "danger")
            return redirect(url_for('manage'))

        flash(
            f"Đã xóa vĩnh viễn nhân sự {user['name']} ({user['id']}) khỏi hệ thống",
            "danger"
        )
        return redirect(url_for('manage'))