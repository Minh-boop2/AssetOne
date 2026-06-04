# File: statistical_backend.py
# Nhiệm vụ:
# - Gọi API backend thật để lấy dữ liệu thống kê nhân viên.
# - Chỉ giữ dữ liệu liên quan đến nhân viên.
# - Không còn dữ liệu doanh thu, tiền tệ, tài sản, cấp phát, báo cáo.

import os
import requests


# URL backend API thật.
# Nếu không cấu hình BACKEND_API_URL trong .env thì mặc định gọi port 5001.
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:5001")


# Context mặc định cho trang thống kê nhân viên.
# Dùng để frontend không bị lỗi nếu backend API lỗi hoặc chưa chạy.
def get_default_employees_context():
    return {
        "total_users": 0,
        "active_users": 0,
        "inactive_users": 0,
        "employee_segments": [],
        "role_items": [],
        "dept_items": [],
        "recent_users": [],
        "statistical_error": None,
        "current_user": {},
    }


# Hàm gọi API GET chung.
# Trả về payload JSON và status code.
def get_json(url, headers=None, params=None):
    try:
        response = requests.get(
            url,
            headers=headers or {},
            params=params or {},
            timeout=8,
        )

        try:
            payload = response.json()
        except Exception:
            payload = {}

        return payload, response.status_code

    except requests.RequestException as error:
        return {
            "success": False,
            "message": str(error),
        }, 500


# Lấy dữ liệu thống kê nhân viên từ backend.
# API backend đang dùng:
# GET /api/statistical/employees
def get_statistical_employees_context(args, current_user):
    payload, status_code = get_json(
        f"{BACKEND_API_URL}/api/statistical/employees",
        params=args,
    )

    context = get_default_employees_context()
    context["current_user"] = current_user or {}

    if status_code != 200 or not payload.get("success"):
        context["statistical_error"] = (
            payload.get("message")
            or "Không thể tải dữ liệu thống kê nhân viên"
        )

        return context

    data = payload.get("data") or {}

    context.update(data)
    context["statistical_error"] = None

    return context


# Giữ alias này để tránh lỗi nếu file khác trong frontend cũ còn gọi overview.
# Nhưng dữ liệu trả về vẫn là thống kê nhân viên.
def get_statistical_overview_context(args, current_user):
    return get_statistical_employees_context(args, current_user)