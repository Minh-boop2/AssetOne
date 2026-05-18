import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode, quote

from flask import session


BACKEND_ASSETS_API = "http://127.0.0.1:5001/api/assets"
BACKEND_ASSET_TYPES_API = "http://127.0.0.1:5001/api/assets/types"


DEFAULT_FILTER_COUNTS = {
    "type": {
        "all": 0,
        "laptop": 0,
        "pc": 0,
        "printer": 0,
        "monitor": 0,
        "phone": 0,
        "projector": 0,
        "other": 0,
    },
    "status": {
        "all": 0,
        "using": 0,
        "available": 0,
        "maintenance": 0,
        "broken": 0,
        "pending": 0,
    },
    "department": {
        "all": 0,
    },
    "location": {
        "all": 0,
    },
}


def get_current_user():
    return session.get("user") or session.get("current_user") or {}


def get_current_user_id():
    user_id = session.get("current_user_id")

    if user_id:
        return str(user_id)

    user = get_current_user()

    if user.get("id"):
        return str(user.get("id"))

    if user.get("_id"):
        return str(user.get("_id"))

    return ""


def build_headers(has_json_body=False):
    headers = {
        "Accept": "application/json",
    }

    current_user_id = get_current_user_id()

    # Backend API sẽ dựa vào X-User-Id để biết user hiện tại là ai.
    # ADMIN / QUAN_LY: thấy full tài sản.
    # NHAN_VIEN: chỉ thấy tài sản có user_id hoặc employee_code của chính họ.
    if current_user_id:
        headers["X-User-Id"] = current_user_id

    if has_json_body:
        headers["Content-Type"] = "application/json"

    return headers


def parse_json_response(response):
    raw = response.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def parse_http_error_payload(error):
    try:
        raw = error.read().decode("utf-8")
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


def empty_assets_payload(per_page=10, message=None, status_code=None):
    return {
        "items": [],
        "pagination": {
            "page": 1,
            "per_page": per_page,
            "total_items": 0,
            "total_pages": 1,
        },
        "filter_counts": DEFAULT_FILTER_COUNTS,
        "scope": {},
        "message": message,
        "status_code": status_code,
    }


def make_error_result(default_message, status_code=500, payload=None):
    payload = payload or {}

    return {
        "message": payload.get("message", default_message),
        "errors": payload.get("errors"),
        "status_code": payload.get("status_code", status_code),
    }


def fetch_assets_from_backend(
    page=1,
    per_page=10,
    search="",
    asset_type="Tất cả",
    department="Tất cả",
    status="Tất cả",
):
    params = {
        "page": page,
        "per_page": per_page,
        "search": search,
        "type": asset_type,
        "department": department,
        "status": status,
    }

    api_url = f"{BACKEND_ASSETS_API}?{urlencode(params)}"

    req = Request(
        api_url,
        method="GET",
        headers=build_headers(),
    )

    try:
        with urlopen(req, timeout=5) as response:
            return parse_json_response(response)

    except HTTPError as e:
        payload = parse_http_error_payload(e)

        return empty_assets_payload(
            per_page=per_page,
            message=payload.get(
                "message",
                f"Lấy danh sách tài sản thất bại. HTTP {e.code}",
            ),
            status_code=e.code,
        )

    except (URLError, TimeoutError, json.JSONDecodeError):
        return empty_assets_payload(
            per_page=per_page,
            message="Không thể kết nối đến backend để lấy danh sách tài sản.",
            status_code=500,
        )


def fetch_asset_detail_from_backend(asset_id):
    api_url = f"{BACKEND_ASSETS_API}/{quote(str(asset_id))}"

    req = Request(
        api_url,
        method="GET",
        headers=build_headers(),
    )

    try:
        with urlopen(req, timeout=5) as response:
            return parse_json_response(response)

    except HTTPError:
        return None

    except (URLError, TimeoutError, json.JSONDecodeError):
        return None


def fetch_asset_types_from_backend():
    req = Request(
        BACKEND_ASSET_TYPES_API,
        method="GET",
        headers=build_headers(),
    )

    try:
        with urlopen(req, timeout=5) as response:
            payload = parse_json_response(response)

        return payload.get("items", [])

    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
        return []


def create_asset_to_backend(data):
    payload = json.dumps(data).encode("utf-8")

    req = Request(
        BACKEND_ASSETS_API,
        data=payload,
        method="POST",
        headers=build_headers(has_json_body=True),
    )

    try:
        with urlopen(req, timeout=5) as response:
            result = parse_json_response(response)

        return True, result

    except HTTPError as e:
        payload = parse_http_error_payload(e)

        return False, make_error_result(
            default_message=f"Tạo tài sản thất bại. HTTP {e.code}",
            status_code=e.code,
            payload=payload,
        )

    except (URLError, TimeoutError, json.JSONDecodeError):
        return False, {
            "message": "Không thể kết nối đến backend để tạo tài sản.",
            "status_code": 500,
        }


def update_asset_to_backend(asset_id, data):
    """
    Gọi API cập nhật tài sản.
    Backend server cần có route:
        PUT /api/assets/<asset_id>
    hoặc nếu server của bạn dùng PATCH thì đổi method="PUT" thành method="PATCH".
    """
    api_url = f"{BACKEND_ASSETS_API}/{quote(str(asset_id))}"
    payload = json.dumps(data).encode("utf-8")

    req = Request(
        api_url,
        data=payload,
        method="PUT",
        headers=build_headers(has_json_body=True),
    )

    try:
        with urlopen(req, timeout=5) as response:
            result = parse_json_response(response)

        return True, result

    except HTTPError as e:
        payload = parse_http_error_payload(e)

        return False, make_error_result(
            default_message=f"Cập nhật tài sản thất bại. HTTP {e.code}",
            status_code=e.code,
            payload=payload,
        )

    except (URLError, TimeoutError, json.JSONDecodeError):
        return False, {
            "message": "Không thể kết nối đến backend để cập nhật tài sản.",
            "status_code": 500,
        }


def delete_asset_from_backend(asset_id):
    api_url = f"{BACKEND_ASSETS_API}/{quote(str(asset_id))}"

    req = Request(
        api_url,
        method="DELETE",
        headers=build_headers(),
    )

    try:
        with urlopen(req, timeout=5) as response:
            payload = parse_json_response(response)

        return True, payload

    except HTTPError as e:
        payload = parse_http_error_payload(e)

        return False, make_error_result(
            default_message=f"Xóa tài sản thất bại. HTTP {e.code}",
            status_code=e.code,
            payload=payload,
        )

    except (URLError, TimeoutError, json.JSONDecodeError):
        return False, {
            "message": "Không thể kết nối đến backend để xóa tài sản.",
            "status_code": 500,
        }