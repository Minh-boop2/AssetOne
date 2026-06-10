import json
import mimetypes
import uuid
from urllib import request as url_request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from flask import session

try:
    from templates.login.login_backend import API_BASE_URL
except Exception:
    API_BASE_URL = "http://127.0.0.1:5001"


DEFAULT_AVATAR_URL = "/static/img/default-avatar.jpg"

ROLE_LABELS = {
    "ADMIN": "QUẢN TRỊ HỆ THỐNG",
    "QUAN_LY": "QUẢN LÝ",
    "NHAN_VIEN": "NHÂN VIÊN",
}

STATUS_LABELS = {
    "HOAT_DONG": "Hoạt động",
    "NGUNG_HOAT_DONG": "Ngưng hoạt động",
}


def get_current_user_id():
    user_id = (
        session.get("current_user_id")
        or session.get("user_id")
        or session.get("id")
    )

    if user_id:
        return str(user_id)

    user = session.get("user") or session.get("current_user")

    if isinstance(user, dict):
        return str(user.get("id") or user.get("_id") or user.get("user_id") or "")

    return ""


def get_session_user():
    user = session.get("user") or session.get("current_user")
    return user if isinstance(user, dict) else None


def call_api_get(path, user_id=None, params=None):
    url = f"{API_BASE_URL}{path}"

    if params:
        url = f"{url}?{urlencode(params)}"

    headers = {
        "Content-Type": "application/json"
    }

    if user_id:
        headers["X-User-Id"] = str(user_id)

    req = url_request.Request(
        url=url,
        headers=headers,
        method="GET"
    )

    try:
        with url_request.urlopen(req, timeout=5) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)

    except HTTPError as error:
        try:
            body = error.read().decode("utf-8")
            return json.loads(body)
        except Exception:
            return {
                "success": False,
                "message": f"API lỗi HTTP {error.code}",
                "data": None
            }

    except URLError as error:
        return {
            "success": False,
            "message": "Không thể kết nối backend API",
            "error": str(error),
            "data": None
        }

    except Exception as error:
        return {
            "success": False,
            "message": "Có lỗi khi gọi backend API",
            "error": str(error),
            "data": None
        }


def call_api_upload_avatar(path, file, user_id=None):
    url = f"{API_BASE_URL}{path}"

    if not file or not file.filename:
        return {
            "success": False,
            "message": "Vui lòng chọn ảnh đại diện",
            "data": None
        }

    boundary = f"----AssetOneBoundary{uuid.uuid4().hex}"
    filename = file.filename
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    file_bytes = file.read()

    body = b""
    body += f"--{boundary}\r\n".encode("utf-8")
    body += (
        f'Content-Disposition: form-data; name="avatar"; filename="{filename}"\r\n'
    ).encode("utf-8")
    body += f"Content-Type: {content_type}\r\n\r\n".encode("utf-8")
    body += file_bytes
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")

    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body))
    }

    if user_id:
        headers["X-User-Id"] = str(user_id)

    req = url_request.Request(
        url=url,
        data=body,
        headers=headers,
        method="POST"
    )

    try:
        with url_request.urlopen(req, timeout=10) as response:
            response_body = response.read().decode("utf-8")
            return json.loads(response_body)

    except HTTPError as error:
        try:
            response_body = error.read().decode("utf-8")
            return json.loads(response_body)
        except Exception:
            return {
                "success": False,
                "message": f"API lỗi HTTP {error.code}",
                "data": None
            }

    except URLError as error:
        return {
            "success": False,
            "message": "Không thể kết nối backend API",
            "error": str(error),
            "data": None
        }

    except Exception as error:
        return {
            "success": False,
            "message": "Có lỗi khi tải avatar lên backend API",
            "error": str(error),
            "data": None
        }


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def normalize_avatar_url(avatar_url):
    if not avatar_url:
        return DEFAULT_AVATAR_URL

    avatar_url = str(avatar_url).strip()

    if not avatar_url:
        return DEFAULT_AVATAR_URL

    default_urls = [
        "/static/imgages/default-avatar.jpg",
        "/static/images/default-avatar.jpg",
        "/static/img/default-avatar.jpg",
    ]

    if avatar_url in default_urls:
        return DEFAULT_AVATAR_URL

    if avatar_url == DEFAULT_AVATAR_URL:
        return DEFAULT_AVATAR_URL

    if avatar_url.startswith("http://") or avatar_url.startswith("https://"):
        return avatar_url

    if avatar_url.startswith("/static/uploads/avatars/"):
        return f"{API_BASE_URL.rstrip('/')}{avatar_url}"

    return avatar_url


def normalize_status_label(profile):
    status = profile.get("status")

    if profile.get("status_label"):
        return profile.get("status_label")

    if status in STATUS_LABELS:
        return STATUS_LABELS.get(status)

    return "Không xác định"


def normalize_role_label(profile):
    role = profile.get("role")

    if profile.get("role_label"):
        return profile.get("role_label").upper()

    if role in ROLE_LABELS:
        return ROLE_LABELS.get(role)

    return "NGƯỜI DÙNG"


def get_asset_count_from_profile(profile):
    return safe_int(
        profile.get("asset_count")
        or profile.get("held_assets_count")
        or profile.get("total_assets")
        or 0
    )


def get_asset_count_from_assets_api(user_id):
    if not user_id:
        return None

    response = call_api_get(
        "/api/assets",
        user_id=user_id,
        params={
            "page": 1,
            "per_page": 1
        }
    )

    pagination = response.get("pagination") or {}

    if "total_items" in pagination:
        return safe_int(pagination.get("total_items"), 0)

    if "total" in pagination:
        return safe_int(pagination.get("total"), 0)

    if isinstance(response.get("items"), list):
        return len(response.get("items"))

    return None


def normalize_admin(profile, asset_count=None):
    if not profile:
        return {
            "id": "N/A",
            "user_id": None,
            "employee_code": "N/A",
            "name": "Chưa đăng nhập",
            "full_name": "Chưa đăng nhập",
            "email": "N/A",
            "phone": "N/A",
            "dept": "N/A",
            "department": "N/A",
            "floor": None,
            "role": "N/A",
            "role_label": "NGƯỜI DÙNG",
            "status": "N/A",
            "status_label": "Không xác định",
            "avatar_url": DEFAULT_AVATAR_URL,
            "asset_count": safe_int(asset_count, 0),
            "asset_scope": "none",
            "created_at": None,
            "updated_at": None,
        }

    name = profile.get("name") or profile.get("full_name") or "Người dùng"

    return {
        "id": profile.get("employee_code") or profile.get("id") or "N/A",
        "user_id": profile.get("id") or profile.get("_id") or profile.get("user_id"),
        "employee_code": profile.get("employee_code") or "N/A",
        "name": name,
        "full_name": profile.get("full_name") or name,
        "email": profile.get("email") or "N/A",
        "phone": profile.get("phone") or "N/A",
        "dept": profile.get("dept") or profile.get("department") or "N/A",
        "department": profile.get("department") or profile.get("dept") or "N/A",
        "floor": profile.get("floor"),
        "role": profile.get("role"),
        "role_label": normalize_role_label(profile),
        "status": profile.get("status"),
        "status_label": normalize_status_label(profile),
        "avatar_url": normalize_avatar_url(profile.get("avatar_url")),
        "asset_count": safe_int(asset_count, get_asset_count_from_profile(profile)),
        "asset_scope": profile.get("asset_scope") or "own",
        "created_at": profile.get("created_at"),
        "updated_at": profile.get("updated_at"),
    }


def normalize_logs_from_list(logs):
    result = []

    if not isinstance(logs, list):
        return result

    for log in logs[:5]:
        if not isinstance(log, dict):
            continue

        result.append({
            "time": log.get("time") or log.get("created_at") or "",
            "action": log.get("action") or "Hoạt động",
            "asset": (
                log.get("asset")
                or log.get("target_name")
                or log.get("name")
                or log.get("path")
                or "Không xác định"
            ),
        })

    return result


def get_logs_from_profile(profile):
    if not profile:
        return []

    logs = (
        profile.get("recent_activities")
        or profile.get("activities")
        or profile.get("logs")
        or []
    )

    return normalize_logs_from_list(logs)


def get_logs_from_activity_api(user_id):
    if not user_id:
        return []

    response = call_api_get(
        "/api/activities",
        user_id=user_id,
        params={
            "user_id": user_id,
            "page": 1,
            "limit": 5
        }
    )

    if not response.get("success"):
        return []

    return normalize_logs_from_list(response.get("data") or [])


def normalize_assets_from_profile(profile):
    if not profile:
        return []

    assets = (
        profile.get("held_assets")
        or profile.get("assets")
        or profile.get("assign_data")
        or []
    )

    return assets[:5] if isinstance(assets, list) else []


def sync_session_user(profile):
    if not isinstance(profile, dict):
        return

    session_user = get_session_user()

    if not isinstance(session_user, dict):
        session_user = {}

    avatar_url = normalize_avatar_url(profile.get("avatar_url"))

    session_user["id"] = (
        profile.get("id")
        or profile.get("_id")
        or profile.get("user_id")
        or session_user.get("id")
    )
    session_user["employee_code"] = profile.get("employee_code") or session_user.get("employee_code")
    session_user["full_name"] = profile.get("full_name") or profile.get("name") or session_user.get("full_name")
    session_user["name"] = profile.get("name") or profile.get("full_name") or session_user.get("name")
    session_user["email"] = profile.get("email") or session_user.get("email")
    session_user["phone"] = profile.get("phone") or session_user.get("phone")
    session_user["department"] = profile.get("department") or profile.get("dept") or session_user.get("department")
    session_user["floor"] = profile.get("floor") or session_user.get("floor")
    session_user["role"] = profile.get("role") or session_user.get("role")
    session_user["role_label"] = profile.get("role_label") or session_user.get("role_label")
    session_user["status"] = profile.get("status") or session_user.get("status")
    session_user["avatar_url"] = avatar_url

    session["user"] = session_user
    session["current_user"] = session_user
    session.modified = True


def get_admin_profile_data():
    user_id = get_current_user_id()
    profile_response = call_api_get("/api/profile/me", user_id)

    if profile_response.get("success"):
        profile = profile_response.get("data") or {}
        sync_session_user(profile)
    else:
        profile = get_session_user() or {}

    profile_asset_count = get_asset_count_from_profile(profile)
    api_asset_count = get_asset_count_from_assets_api(user_id)

    asset_count = api_asset_count if api_asset_count is not None else profile_asset_count

    admin = normalize_admin(profile, asset_count=asset_count)
    logs = get_logs_from_profile(profile)

    if not logs:
        logs = get_logs_from_activity_api(user_id)

    return {
        "success": profile_response.get("success", False),
        "message": profile_response.get("message"),
        "admin": admin,
        "logs": logs,
        "assign_data": normalize_assets_from_profile(profile),
    }


def upload_admin_avatar(file):
    user_id = get_current_user_id()
    response = call_api_upload_avatar("/api/profile/avatar", file, user_id)

    if response.get("success") and isinstance(response.get("data"), dict):
        data = response.get("data") or {}
        sync_session_user(data)

    return response