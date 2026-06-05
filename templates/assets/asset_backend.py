import json
import unicodedata
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode, quote

from flask import session, flash, redirect, url_for


BACKEND_ASSETS_API = "http://127.0.0.1:5001/api/assets"
BACKEND_ASSET_TYPES_API = "http://127.0.0.1:5001/api/assets/types"

# THÊM: API hoạt động dùng để lấy lịch sử hoạt động của 1 tài sản ở trang detail
BACKEND_ACTIVITIES_API = "http://127.0.0.1:5001/api/activities"


DEFAULT_FILTER_COUNTS = {
    "type": {
        "all": 0,
        "laptop": 0,
        "pc": 0,
        "printer": 0,
        "monitor": 0,
        "phone": 0,
        "projector": 0,
        "scanner": 0,
        "network": 0,
        "ups": 0,
        "camera": 0,
        "speaker": 0,
        "microphone": 0,
        "keyboard": 0,
        "mouse": 0,
        "tablet": 0,
        "server": 0,
        "router": 0,
        "switch": 0,
        "storage": 0,
        "accessory": 0,
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


STATUS_LABELS = {
    "using": "Đang sử dụng",
    "available": "Chưa sử dụng",
    "maintenance": "Bảo trì",
    "broken": "Hỏng",
    "pending": "Chờ duyệt",
}


STATUS_ALIASES = {
    "using": ["using", "Đang sử dụng", "Dang su dung", "Hoàn thành"],
    "available": ["available", "Chưa sử dụng", "Chua su dung", "Chưa dùng", "Chua dung"],
    "maintenance": ["maintenance", "Bảo trì", "Bao tri"],
    "broken": ["broken", "Hỏng", "Hong"],
    "pending": ["pending", "Chờ duyệt", "Cho duyet"],
}


ASSET_STATUS_ACTIONS = {
    "send_maintenance": {
        "allowed_from": ["broken"],
        "label": "Đang bảo trì",
    },
    "maintenance_done": {
        "allowed_from": ["maintenance"],
        "label": "Hoàn thành",
    },
    "maintenance_failed": {
        "allowed_from": ["maintenance"],
        "label": "Không hoàn thành",
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


def is_logged_in():
    return bool(get_current_user())


def user_can(module_key, action):
    user = get_current_user()

    if user.get("is_admin") or user.get("role") == "ADMIN":
        return True

    can = user.get("can") or {}

    return can.get(module_key, {}).get(action) is True


def is_staff_user():
    user = get_current_user()
    return user.get("role") == "NHAN_VIEN"


def require_login():
    if not is_logged_in():
        return redirect(url_for("login_page"))

    return None


def require_asset_permission(action):
    login_redirect = require_login()

    if login_redirect:
        return login_redirect

    if not user_can("assets", action):
        flash("Bạn không có quyền thực hiện chức năng này.", "danger")
        return redirect(url_for("dashboard_overview"))

    return None


def asset_permission_context():
    user = get_current_user()

    return {
        "current_user": user,
        "can_view_asset": user_can("assets", "view"),
        "can_create_asset": user_can("assets", "create"),
        "can_update_asset": user_can("assets", "update"),
        "can_delete_asset": user_can("assets", "delete"),
        "is_staff_asset_scope": is_staff_user(),
    }


def build_headers(has_json_body=False):
    headers = {
        "Accept": "application/json",
    }

    current_user_id = get_current_user_id()

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


def handle_api_auth_error(status_code, default_message=None):
    if status_code == 401:
        session.clear()
        flash("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.", "warning")
        return redirect(url_for("login_page"))

    if status_code == 403:
        flash(default_message or "Bạn không có quyền thực hiện chức năng này.", "danger")
        return redirect(url_for("dashboard_overview"))

    return None


def normalize_status_code(value):
    value = (value or "").strip()

    for code, aliases in STATUS_ALIASES.items():
        if value in aliases:
            return code

    return value or "pending"


def get_status_label(status):
    status = normalize_status_code(status)
    return STATUS_LABELS.get(status, status)


def normalize_asset_for_template(info):
    info = dict(info or {})

    info["id"] = str(info.get("id") or info.get("_id") or info.get("asset_code") or "")
    info["asset"] = info.get("asset") or info.get("asset_name") or ""
    info["asset_name"] = info.get("asset_name") or info.get("asset") or ""

    info["type"] = info.get("type") or info.get("category") or ""
    info["category"] = info.get("category") or info.get("type") or ""

    info["user"] = info.get("user") or info.get("receiver") or ""
    info["receiver"] = info.get("receiver") or info.get("user") or ""

    info["asset_code"] = info.get("asset_code") or ""
    info["status"] = normalize_status_code(info.get("status") or "available")
    info["department"] = info.get("department") or ""
    info["location"] = info.get("location") or ""
    info["warranty"] = info.get("warranty") or ""

    info["spec"] = info.get("spec") or info.get("notes") or ""
    info["notes"] = info.get("notes") or info.get("spec") or ""

    info["user_id"] = info.get("user_id") or ""
    info["employee_code"] = info.get("employee_code") or ""

    return info


def asset_has_user(asset):
    return bool(
        asset.get("user_id")
        or asset.get("employee_code")
        or asset.get("user")
        or asset.get("receiver")
    )


def build_create_asset_payload(form_data):
    asset_type = form_data.get("type", "").strip()
    asset_name = form_data.get("asset_name", "").strip()
    spec = form_data.get("spec", "").strip()

    return {
        "asset_code": form_data.get("asset_code", "").strip(),
        "asset_name": asset_name,
        "asset": asset_name,
        "type": asset_type,
        "category": asset_type,
        "warranty": form_data.get("warranty", "").strip(),
        "spec": spec,
        "notes": spec,
        "status": "available",
        "user": "",
        "receiver": "",
        "user_id": "",
        "employee_code": "",
        "department": "",
        "location": "",
    }


def build_update_asset_payload(form_data, current_asset):
    asset_name = form_data.get("asset_name", "").strip()
    asset_type = form_data.get("type", "").strip()
    spec = form_data.get("spec", "").strip()

    return {
        "asset_code": form_data.get("asset_code", "").strip() or current_asset.get("asset_code", ""),
        "asset_name": asset_name,
        "asset": asset_name,
        "type": asset_type,
        "category": asset_type,
        "warranty": form_data.get("warranty", "").strip(),
        "spec": spec,
        "notes": spec,
    }


def merge_asset_form_data(current_asset, form_data):
    asset_name = form_data.get("asset_name", "").strip()
    asset_type = form_data.get("type", "").strip()
    spec = form_data.get("spec", "").strip()

    return normalize_asset_for_template({
        **current_asset,
        **form_data,
        "asset": asset_name,
        "asset_name": asset_name,
        "category": asset_type,
        "type": asset_type,
        "notes": spec,
        "spec": spec,
    })


def normalize_asset_types_filter(asset_types=None):
    # THÊM: chuẩn hóa danh sách loại tài sản khi filter chọn nhiều
    # nhận được cả list ["laptop", "pc"] hoặc chuỗi "laptop,pc"
    if not asset_types:
        return ""

    if isinstance(asset_types, (list, tuple, set)):
        values = asset_types
    else:
        values = str(asset_types).split(",")

    clean_values = []

    for value in values:
        value = str(value or "").strip()

        if value and value != "Tất cả" and value not in clean_values:
            clean_values.append(value)

    return ",".join(clean_values)


def fetch_assets_from_backend(
    page=1,
    per_page=10,
    search="",
    asset_type="Tất cả",
    asset_types=None,
    department="Tất cả",
    status="Tất cả",
):
    selected_types = normalize_asset_types_filter(asset_types)

    params = {
        "page": page,
        "per_page": per_page,
        "search": search,
        "type": "Tất cả" if selected_types else asset_type,
        "department": department,
        "status": status,
    }

    # THÊM: gửi thêm types cho backend API để lọc nhiều loại tài sản cùng lúc
    if selected_types:
        params["types"] = selected_types

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


# THÊM: bỏ dấu và viết thường để so khớp hoạt động với tài sản ổn định hơn
def normalize_match_text(value):
    if value is None:
        return ""

    text = str(value).strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")

    return text


# THÊM: lấy mã hoạt động giống trang Hoạt động
def build_asset_activity_code(activity, index=0):
    raw_id = (
        activity.get("id")
        or activity.get("_id")
        or activity.get("activity_id")
        or activity.get("log_id")
        or ""
    )

    raw_id = str(raw_id)

    if raw_id:
        return "ACT-" + raw_id[-6:].upper()

    return "ACT-" + str(index + 1).zfill(6)


# THÊM: format thời gian giống bảng Hoạt động
def format_asset_activity_time(value):
    if not value:
        return "—"

    text = str(value).strip()

    if not text:
        return "—"

    formats = [
        "%d/%m/%Y %H:%M",
        "%H:%M %d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]

    clean_text = text.replace("Z", "").replace("+00:00", "")

    for fmt in formats:
        try:
            parsed = datetime.strptime(clean_text[:26], fmt)
            return parsed.strftime("%H:%M %d/%m/%Y")
        except Exception:
            pass

    return text


# THÊM: đổi status_code thành chữ hiển thị
def get_asset_activity_status_text(activity):
    status_code = activity.get("status_code")

    if status_code is None or status_code == "":
        return activity.get("status") or activity.get("display_status") or "Thành công"

    try:
        code = int(status_code)
    except Exception:
        return str(status_code)

    if 200 <= code < 300:
        return "Thành công"

    if 300 <= code < 400:
        return "Chuyển hướng"

    if 400 <= code < 500:
        return "Thất bại"

    if code >= 500:
        return "Lỗi hệ thống"

    return "Không xác định"


# THÊM: class màu cho trạng thái hoạt động
def get_asset_activity_status_class(activity):
    status_text = get_asset_activity_status_text(activity)

    if status_text == "Thành công":
        return "history-status-success"

    if status_text in ["Thất bại", "Lỗi hệ thống"]:
        return "history-status-danger"

    return "history-status-neutral"


# THÊM: xác định loại hoạt động giống trang Hoạt động
def get_asset_activity_type(activity):
    module = normalize_match_text(activity.get("module"))
    action = normalize_match_text(activity.get("action"))
    path = normalize_match_text(activity.get("path"))
    target_name = normalize_match_text(activity.get("target_name"))

    text = f"{module} {action} {path} {target_name}"

    if "report" in text or "bao cao" in text:
        return "Báo cáo"

    if "thu hoi" in text or "recover" in text or "recall" in text or "return" in text:
        return "Thu hồi"

    if "assign" in text or "cap phat" in text:
        return "Cấp phát"

    if "asset" in text or "tai san" in text:
        return "Tài sản"

    if "user" in text or "nguoi dung" in text:
        return "Người dùng"

    if "permission" in text or "phan quyen" in text:
        return "Phân quyền"

    if "mail" in text or "email" in text:
        return "Mail"

    if "activity" in text or "hoat dong" in text:
        return "Hoạt động"

    return "Hệ thống"


# THÊM: nội dung hiển thị của log
def build_asset_activity_detail(activity):
    action = activity.get("action") or "Thao tác hệ thống"
    target_name = activity.get("target_name") or ""
    path = activity.get("path") or ""

    if target_name:
        return f"{action} - {target_name}"

    if path:
        return f"{action} ({path})"

    return action


# THÊM: kiểm tra log có thuộc đúng tài sản đang xem hay không
def activity_matches_asset(activity, asset):
    asset = normalize_asset_for_template(asset)

    asset_id = normalize_match_text(asset.get("id"))
    asset_code = normalize_match_text(asset.get("asset_code"))
    asset_name = normalize_match_text(asset.get("asset") or asset.get("asset_name"))

    target_id = normalize_match_text(activity.get("target_id"))

    metadata = activity.get("metadata") or {}

    metadata_text = ""

    if isinstance(metadata, dict):
        metadata_text = " ".join([
            str(value)
            for value in metadata.values()
            if value not in [None, ""]
        ])

    searchable_text = normalize_match_text(" ".join([
        str(activity.get("action") or ""),
        str(activity.get("module") or ""),
        str(activity.get("path") or ""),
        str(activity.get("target_id") or ""),
        str(activity.get("target_name") or ""),
        str(metadata_text or ""),
    ]))

    exact_tokens = [
        token
        for token in [asset_id, asset_code]
        if token
    ]

    for token in exact_tokens:
        if token and (target_id == token or token in searchable_text):
            return True

    if asset_name and asset_name in searchable_text:
        return True

    return False


# THÊM: chuẩn hóa activity log để asset_detail.html render giống bảng hoạt động
def normalize_asset_activity_for_template(activity, index=0):
    if not isinstance(activity, dict):
        activity = {}

    full_name = (
        activity.get("full_name")
        or activity.get("user_name")
        or activity.get("username")
        or activity.get("email")
        or "Chưa xác định"
    )

    created_at = (
        activity.get("created_at")
        or activity.get("updated_at")
        or activity.get("time")
        or activity.get("activity_time")
    )

    action = activity.get("action") or "Thao tác hệ thống"
    module = get_asset_activity_type(activity)
    detail = build_asset_activity_detail(activity)
    status_text = get_asset_activity_status_text(activity)

    return {
        **activity,
        "activity_code": build_asset_activity_code(activity, index),
        "activity_time": format_asset_activity_time(created_at),
        "activity_user": full_name,
        "activity_action": action,
        "activity_module": module,
        "activity_detail": detail,
        "activity_status": status_text,
        "activity_status_class": get_asset_activity_status_class(activity),
    }


# THÊM: gọi API /api/activities theo search term
def fetch_activity_page_from_backend(search_term="", page=1):
    params = {
        "page": page,
    }

    if search_term:
        params["search"] = search_term

    api_url = f"{BACKEND_ACTIVITIES_API}?{urlencode(params)}"

    req = Request(
        api_url,
        method="GET",
        headers=build_headers(),
    )

    try:
        with urlopen(req, timeout=8) as response:
            payload = parse_json_response(response)

        return payload

    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return {
            "success": False,
            "data": [],
            "pagination": {
                "page": page,
                "total_pages": 1,
            },
        }


# THÊM: lấy lịch sử hoạt động của đúng tài sản đang xem detail
# Mặc định chỉ lấy 5 hoạt động mới nhất để trang detail gọn và load nhanh hơn
def fetch_asset_activity_logs_from_backend(asset, max_pages=5, max_items=5):
    asset = normalize_asset_for_template(asset)

    search_terms = []

    for value in [
        asset.get("asset_code"),
        asset.get("asset"),
        asset.get("asset_name"),
        asset.get("id"),
    ]:
        value = str(value or "").strip()

        if value and value not in search_terms:
            search_terms.append(value)

    if not search_terms:
        return []

    matched_logs = []
    seen_ids = set()

    for search_term in search_terms:
        for page in range(1, max_pages + 1):
            payload = fetch_activity_page_from_backend(
                search_term=search_term,
                page=page,
            )

            raw_items = payload.get("data") or []

            for item in raw_items:
                activity_id = str(
                    item.get("id")
                    or item.get("_id")
                    or item.get("activity_id")
                    or item.get("log_id")
                    or ""
                )

                if activity_id and activity_id in seen_ids:
                    continue

                if not activity_matches_asset(item, asset):
                    continue

                if activity_id:
                    seen_ids.add(activity_id)

                matched_logs.append(item)

                # THÊM: đủ 5 hoạt động mới nhất thì dừng luôn
                if len(matched_logs) >= max_items:
                    return [
                        normalize_asset_activity_for_template(log, index)
                        for index, log in enumerate(matched_logs[:max_items])
                    ]

            pagination = payload.get("pagination") or {}
            total_pages = int(pagination.get("total_pages") or 1)

            if page >= total_pages:
                break

    return [
        normalize_asset_activity_for_template(log, index)
        for index, log in enumerate(matched_logs[:max_items])
    ]


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


def create_asset_from_form(form_data):
    payload = build_create_asset_payload(form_data)
    return create_asset_to_backend(payload)


def update_asset_from_form(asset_id, form_data, current_asset):
    payload = build_update_asset_payload(form_data, current_asset)
    return update_asset_to_backend(asset_id, payload)


def build_asset_status_action_payload(asset, action):
    if action == "send_maintenance":
        return {
            "payload": {
                "status": "maintenance",
            },
            "message": "Đã chuyển tài sản sang trạng thái Bảo trì.",
        }

    if action == "maintenance_done":
        if asset_has_user(asset):
            return {
                "payload": {
                    "status": "using",
                },
                "message": "Đã hoàn thành bảo trì. Tài sản đang có người sử dụng nên chuyển sang Đang sử dụng.",
            }

        return {
            "payload": {
                "status": "available",
            },
            "message": "Đã hoàn thành bảo trì. Tài sản không có người sử dụng nên chuyển sang Chưa sử dụng.",
        }

    if action == "maintenance_failed":
        return {
            "payload": {
                "status": "broken",
                "user_id": "",
                "employee_code": "",
                "user": "",
                "receiver": "",
                "department": "",
                "location": "",
            },
            "message": "Bảo trì không hoàn thành. Tài sản đã chuyển về trạng thái Hỏng và bỏ người sử dụng.",
        }

    return None


def handle_asset_status_action(asset_id, action):
    action = (action or "").strip()
    rule = ASSET_STATUS_ACTIONS.get(action)

    if not rule:
        return False, {
            "message": "Thao tác trạng thái không hợp lệ.",
            "status_code": 400,
        }

    asset = fetch_asset_detail_from_backend(asset_id)

    if not asset:
        return False, {
            "message": "Không tìm thấy tài sản hoặc bạn không có quyền cập nhật tài sản này.",
            "status_code": 404,
        }

    asset = normalize_asset_for_template(asset)
    current_status = normalize_status_code(asset.get("status"))

    if current_status not in rule["allowed_from"]:
        return False, {
            "message": (
                "Không thể thực hiện thao tác này khi tài sản đang ở trạng thái "
                f"{get_status_label(current_status)}."
            ),
            "status_code": 400,
        }

    action_payload = build_asset_status_action_payload(asset, action)

    if not action_payload:
        return False, {
            "message": "Không tạo được dữ liệu cập nhật trạng thái.",
            "status_code": 400,
        }

    payload = action_payload["payload"]
    success, result = update_asset_to_backend(asset_id, payload)

    if not success:
        return False, result

    updated_item = result.get("item") or {}
    new_status = updated_item.get("status") or payload.get("status")

    result["message"] = action_payload["message"]
    result["status_action"] = action
    result["old_status"] = current_status
    result["new_status"] = new_status

    return True, result


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