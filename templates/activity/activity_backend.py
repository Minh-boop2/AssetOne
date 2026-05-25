import math
import os
from datetime import datetime

import requests


BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:5001")
ACTIVITY_PAGE_LIMIT = 10

DEFAULT_TYPE_OPTIONS = [
    "Báo cáo",
    "Thu hồi",
    "Cấp phát",
    "Tài sản",
    "Người dùng",
    "Phân quyền",
    "Mail",
    "Hoạt động",
    "Hệ thống",
]


def get_current_user_id(current_user):
    if not isinstance(current_user, dict):
        return ""

    return (
        current_user.get("id")
        or current_user.get("_id")
        or current_user.get("user_id")
        or current_user.get("uid")
        or ""
    )


def safe_int(value, default=1):
    try:
        number = int(value)
    except Exception:
        return default

    return number


def format_datetime(value):
    if not value:
        return "Chưa có dữ liệu"

    if isinstance(value, datetime):
        return value.strftime("%H:%M %d/%m/%Y")

    text = str(value).strip()

    if not text:
        return "Chưa có dữ liệu"

    possible_formats = [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%H:%M %d/%m/%Y",
    ]

    clean_text = text.replace("Z", "").replace("+00:00", "")

    for fmt in possible_formats:
        try:
            parsed = datetime.strptime(clean_text[:26], fmt)
            return parsed.strftime("%H:%M %d/%m/%Y")
        except Exception:
            pass

    return text


def get_status_text(activity):
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


def get_activity_type(activity):
    module = str(activity.get("module") or "").lower()
    action = str(activity.get("action") or "").lower()
    path = str(activity.get("path") or "").lower()
    target_name = str(activity.get("target_name") or "").lower()

    text = f"{module} {action} {path} {target_name}"

    if "report" in text or "báo cáo" in text or "bao cao" in text:
        return "Báo cáo"

    if "thu hồi" in text or "thu hoi" in text or "recover" in text or "recall" in text or "return" in text:
        return "Thu hồi"

    if "assign" in text or "cấp phát" in text or "cap phat" in text:
        return "Cấp phát"

    if "asset" in text or "tài sản" in text or "tai san" in text:
        return "Tài sản"

    if "user" in text or "người dùng" in text or "nguoi dung" in text:
        return "Người dùng"

    if "permission" in text or "phân quyền" in text or "phan quyen" in text:
        return "Phân quyền"

    if "mail" in text or "email" in text:
        return "Mail"

    if "activity" in text or "hoạt động" in text or "hoat dong" in text:
        return "Hoạt động"

    return "Hệ thống"


def build_activity_code(activity, index=0):
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


def build_activity_detail(activity):
    action = activity.get("action") or "Thao tác hệ thống"
    target_name = activity.get("target_name") or ""
    path = activity.get("path") or ""

    if target_name:
        return f"{action} - {target_name}"

    if path:
        return f"{action} ({path})"

    return action


def normalize_activity(activity, index=0):
    if not isinstance(activity, dict):
        activity = {}

    full_name = (
        activity.get("full_name")
        or activity.get("user_name")
        or activity.get("username")
        or activity.get("email")
        or "Chưa xác định"
    )

    action = activity.get("action") or "Thao tác hệ thống"
    module = activity.get("module") or "system"
    activity_type = get_activity_type(activity)
    status_text = get_status_text(activity)

    created_at = (
        activity.get("created_at")
        or activity.get("updated_at")
        or activity.get("time")
        or activity.get("activity_time")
    )

    return {
        **activity,

        "display_activity_code": build_activity_code(activity, index),
        "display_activity_time": format_datetime(created_at),
        "display_activity_user": full_name,
        "display_activity_action": action,
        "display_activity_module": activity_type,
        "display_activity_detail": build_activity_detail(activity),
        "display_activity_status": status_text,

        "activity_code": build_activity_code(activity, index),
        "activity_time": format_datetime(created_at),
        "activity_user": full_name,
        "activity_action": action,
        "activity_module": activity_type,
        "activity_detail": build_activity_detail(activity),
        "activity_status": status_text,

        "display_user": full_name,
        "display_action": action,
        "display_module": activity_type,
        "display_detail": build_activity_detail(activity),
        "display_status": status_text,

        "module_raw": module,
    }


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


def get_activity_filter_options(headers):
    url = f"{BACKEND_API_URL}/api/activities/filter-options"

    payload, status_code = get_json(url, headers=headers)

    if status_code != 200 or not payload.get("success"):
        return {
            "total": 0,
            "type_options": [],
            "user_options": [],
            "limit": ACTIVITY_PAGE_LIMIT,
        }

    data = payload.get("data") or {}

    return {
        "total": data.get("total", 0),
        "type_options": data.get("type_options") or [],
        "user_options": data.get("user_options") or [],
        "limit": data.get("limit") or ACTIVITY_PAGE_LIMIT,
    }


def build_type_options(filter_options):
    api_options = filter_options.get("type_options") or []

    values = []

    for item in api_options:
        if isinstance(item, dict):
            value = item.get("value") or item.get("label")
        else:
            value = item

        if value and value not in values:
            values.append(value)

    for value in DEFAULT_TYPE_OPTIONS:
        if value not in values:
            values.append(value)

    return values


def build_type_counts(filter_options):
    counts = {}

    for item in filter_options.get("type_options") or []:
        if not isinstance(item, dict):
            continue

        label = item.get("value") or item.get("label")

        if label:
            counts[label] = item.get("count", 0)

    return counts


def build_user_options(filter_options):
    options = []

    for item in filter_options.get("user_options") or []:
        if not isinstance(item, dict):
            continue

        name = item.get("full_name") or item.get("label") or item.get("value")

        if not name:
            continue

        options.append(name)

    return options


def build_user_counts(filter_options):
    counts = {}

    for item in filter_options.get("user_options") or []:
        if not isinstance(item, dict):
            continue

        name = item.get("full_name") or item.get("label") or item.get("value")

        if name:
            counts[name] = item.get("count", 0)

    return counts


def get_activities_from_api(headers, page, search_value, selected_type, selected_user_name):
    url = f"{BACKEND_API_URL}/api/activities"

    params = {
        "page": page,
        "limit": ACTIVITY_PAGE_LIMIT,
    }

    if search_value:
        params["search"] = search_value

    if selected_type and selected_type != "Tất cả":
        params["type"] = selected_type

    if selected_user_name and selected_user_name != "Tất cả":
        params["user_name"] = selected_user_name

    payload, status_code = get_json(
        url,
        headers=headers,
        params=params,
    )

    if status_code != 200 or not payload.get("success"):
        return {
            "activities": [],
            "pagination": {
                "page": page,
                "limit": ACTIVITY_PAGE_LIMIT,
                "total": 0,
                "total_pages": 1,
            },
            "error": payload.get("message") or "Không thể tải dữ liệu hoạt động",
        }

    raw_activities = payload.get("data") or []
    pagination = payload.get("pagination") or {}

    activities = [
        normalize_activity(activity, index)
        for index, activity in enumerate(raw_activities)
    ]

    return {
        "activities": activities,
        "pagination": {
            "page": pagination.get("page") or page,
            "limit": pagination.get("limit") or ACTIVITY_PAGE_LIMIT,
            "total": pagination.get("total") or len(activities),
            "total_pages": pagination.get("total_pages") or 1,
        },
        "error": None,
    }


def get_activity_page_context(args, current_user):
    current_user_id = get_current_user_id(current_user)

    page = safe_int(args.get("page"), 1)

    if page < 1:
        page = 1

    search_value = (
        args.get("search")
        or args.get("keyword")
        or args.get("q")
        or ""
    ).strip()

    selected_type = (
        args.get("type")
        or args.get("activity_type")
        or "Tất cả"
    ).strip()

    selected_user_name = (
        args.get("user_name")
        or args.get("full_name")
        or "Tất cả"
    ).strip()

    if not selected_type:
        selected_type = "Tất cả"

    if not selected_user_name:
        selected_user_name = "Tất cả"

    headers = {
        "X-User-Id": str(current_user_id),
    }

    filter_options = get_activity_filter_options(headers)

    result = get_activities_from_api(
        headers=headers,
        page=page,
        search_value=search_value,
        selected_type=selected_type,
        selected_user_name=selected_user_name,
    )

    activities = result["activities"]
    pagination = result["pagination"]

    total_records = pagination.get("total", 0)
    current_page = pagination.get("page", page)
    total_pages = pagination.get("total_pages", 1)

    if total_pages < 1:
        total_pages = 1

    type_options = build_type_options(filter_options)
    type_counts = build_type_counts(filter_options)

    user_name_options = build_user_options(filter_options)
    user_name_counts = build_user_counts(filter_options)

    total_activity_count = filter_options.get("total") or total_records

    has_active_filter = bool(
        search_value
        or selected_type != "Tất cả"
        or selected_user_name != "Tất cả"
    )

    return {
        "activities": activities,
        "activity_logs": activities,
        "logs": activities,

        "search_value": search_value,
        "search_q": search_value,

        "selected_type": selected_type,
        "selected_activity_type": selected_type,
        "selected_user_name": selected_user_name,

        "activity_type_options": type_options,
        "type_options": type_options,
        "activity_user_options": user_name_options,
        "user_name_options": user_name_options,

        "type_counts": type_counts,
        "user_name_counts": user_name_counts,

        "total_activity_count": total_activity_count,
        "total_records": total_records,

        "current_page": current_page,
        "total_pages": total_pages,
        "limit": ACTIVITY_PAGE_LIMIT,

        "has_active_filter": has_active_filter,
        "activity_error": result.get("error"),

        "current_user": current_user,
    }
def export_activities_excel(args, current_user):
    current_user_id = get_current_user_id(current_user)

    headers = {
        "X-User-Id": str(current_user_id),
    }

    params = {}

    search_value = (
        args.get("search")
        or args.get("keyword")
        or args.get("q")
        or ""
    ).strip()

    selected_type = (
        args.get("type")
        or args.get("activity_type")
        or "Tất cả"
    ).strip()

    selected_user_name = (
        args.get("user_name")
        or args.get("full_name")
        or "Tất cả"
    ).strip()

    if search_value:
        params["search"] = search_value

    if selected_type and selected_type != "Tất cả":
        params["type"] = selected_type

    if selected_user_name and selected_user_name != "Tất cả":
        params["user_name"] = selected_user_name

    try:
        response = requests.get(
            f"{BACKEND_API_URL}/api/activities/export",
            headers=headers,
            params=params,
            timeout=30,
        )

        content_type = response.headers.get(
            "Content-Type",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        disposition = response.headers.get("Content-Disposition", "")
        filename = "Activities.xlsx"

        if "filename=" in disposition:
            filename = disposition.split("filename=")[-1].strip().strip('"')

        return {
            "success": response.status_code == 200,
            "content": response.content,
            "filename": filename,
            "content_type": content_type,
            "status_code": response.status_code,
        }

    except requests.RequestException as error:
        return {
            "success": False,
            "content": str(error).encode("utf-8"),
            "filename": "Activities.xlsx",
            "content_type": "text/plain; charset=utf-8",
            "status_code": 500,
        }