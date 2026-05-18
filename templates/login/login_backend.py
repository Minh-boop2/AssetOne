import requests


API_BASE_URL = "http://127.0.0.1:5001"


ROLE_LABELS = {
    "ADMIN": "Quản trị hệ thống",
    "QUAN_LY": "Quản lý",
    "NHAN_VIEN": "Nhân viên",
}

DEFAULT_AVATAR_URL = "/static/imgages/default-avatar.jpg"


def parse_response(response):
    try:
        result = response.json()
    except ValueError:
        return False, "Backend trả về dữ liệu không hợp lệ", None

    if not response.ok:
        return False, result.get("message", "Thao tác thất bại"), None

    if not result.get("success"):
        return False, result.get("message", "Thao tác thất bại"), None

    return True, result.get("message", "Thành công"), result.get("data")


def build_user_session(user):
    if not user:
        return None

    role = user.get("role")
    user_id = str(user.get("id") or user.get("_id") or "")

    permissions = user.get("permissions")
    can = user.get("can")
    is_admin = user.get("is_admin")

    if permissions is None:
        permissions = {}

    if can is None:
        can = {}

    if is_admin is None:
        is_admin = role == "ADMIN"

    return {
        "id": user_id,
        "employee_code": user.get("employee_code"),
        "email": user.get("email"),
        "full_name": user.get("full_name") or "Người dùng",
        "phone": user.get("phone"),
        "department": user.get("department"),
        "floor": user.get("floor"),
        "role": role,
        "role_label": ROLE_LABELS.get(role, role),
        "status": user.get("status"),
        "avatar_url": user.get("avatar_url") or DEFAULT_AVATAR_URL,

        # Dữ liệu phân quyền cho frontend ẩn/hiện menu, nút, action
        "is_admin": is_admin,
        "permissions": permissions,
        "can": can,
    }


def login_user_from_form(form):
    email = form.get("email")
    password = form.get("password")

    if not email or not password:
        return False, "Vui lòng nhập Gmail và mật khẩu", None

    payload = {
        "email": email,
        "password": password
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/users/login",
            json=payload,
            timeout=5
        )

        success, message, user = parse_response(response)

        if not success:
            return success, message, None

        if not user:
            return False, "Backend không trả về thông tin user", None

        role = user.get("role")

        if role not in ROLE_LABELS:
            return False, "Tài khoản chưa được phân quyền hợp lệ", None

        user_session = build_user_session(user)

        if not user_session or not user_session.get("id"):
            return False, "Tài khoản thiếu ID user", None

        return True, message, user_session

    except requests.exceptions.ConnectionError:
        return False, "Không kết nối được backend API. Hãy chạy app database port 5001", None

    except requests.exceptions.Timeout:
        return False, "Backend API phản hồi quá lâu", None

    except requests.exceptions.RequestException:
        return False, "Có lỗi khi gọi backend API", None


def forgot_password_from_form(form):
    email = form.get("email")

    if not email:
        return False, "Vui lòng nhập Gmail", None

    payload = {
        "email": email
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/mail/forgot-password",
            json=payload,
            timeout=10
        )

        return parse_response(response)

    except requests.exceptions.ConnectionError:
        return False, "Không kết nối được backend API. Hãy chạy app database port 5001", None

    except requests.exceptions.Timeout:
        return False, "Backend API phản hồi quá lâu", None

    except requests.exceptions.RequestException:
        return False, "Có lỗi khi gửi yêu cầu quên mật khẩu", None


def verify_reset_token(token):
    if not token:
        return False, "Link đặt lại mật khẩu không hợp lệ", None

    try:
        response = requests.get(
            f"{API_BASE_URL}/api/mail/reset-password/verify/{token}",
            timeout=5
        )

        return parse_response(response)

    except requests.exceptions.ConnectionError:
        return False, "Không kết nối được backend API. Hãy chạy app database port 5001", None

    except requests.exceptions.Timeout:
        return False, "Backend API phản hồi quá lâu", None

    except requests.exceptions.RequestException:
        return False, "Có lỗi khi kiểm tra link đặt lại mật khẩu", None


def reset_password_from_form(token, form):
    password = form.get("password")
    confirm_password = form.get("confirm_password")

    if not password:
        return False, "Vui lòng nhập mật khẩu mới", None

    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự", None

    if not confirm_password:
        return False, "Vui lòng nhập xác nhận mật khẩu", None

    if password != confirm_password:
        return False, "Mật khẩu xác nhận không khớp", None

    payload = {
        "token": token,
        "password": password,
        "confirm_password": confirm_password
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/mail/reset-password",
            json=payload,
            timeout=10
        )

        return parse_response(response)

    except requests.exceptions.ConnectionError:
        return False, "Không kết nối được backend API. Hãy chạy app database port 5001", None

    except requests.exceptions.Timeout:
        return False, "Backend API phản hồi quá lâu", None

    except requests.exceptions.RequestException:
        return False, "Có lỗi khi đặt lại mật khẩu", None