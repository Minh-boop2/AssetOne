import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

from flask import session


BACKEND_ASSETS_API = "http://127.0.0.1:5001/api/assets"
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


STATUS_BADGE_CLASSES = {
    "using": "status-using",
    "available": "status-free",
    "maintenance": "status-error",
    "broken": "status-error",
    "pending": "status-free",
}


ACTIVITY_DOT_CLASSES = {
    "POST": "activity-dot-success",
    "PUT": "activity-dot-info",
    "PATCH": "activity-dot-info",
    "DELETE": "activity-dot-danger",
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


def build_headers():
    headers = {
        "Accept": "application/json",
    }

    current_user_id = get_current_user_id()

    if current_user_id:
        headers["X-User-Id"] = current_user_id

    return headers


def safe_percent(value, total):
    if not total:
        return 0

    return min(100, max(0, round((value / total) * 100)))


def normalize_limit(limit, default=4, max_value=20):
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = default

    return max(1, min(limit, max_value))


def empty_dashboard_assets_payload(limit=4, message=None, status_code=None):
    return {
        "items": [],
        "pagination": {
            "page": 1,
            "per_page": limit,
            "total_items": 0,
            "total_pages": 1,
        },
        "filter_counts": DEFAULT_FILTER_COUNTS,
        "scope": {},
        "message": message,
        "status_code": status_code,
    }


def empty_dashboard_activities_payload(limit=6, message=None, status_code=None):
    return {
        "success": False,
        "message": message,
        "data": [],
        "pagination": {
            "page": 1,
            "limit": limit,
            "total": 0,
            "total_pages": 1,
        },
        "viewer": {},
        "status_code": status_code,
    }


def parse_json_response(response):
    raw = response.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def fetch_dashboard_assets_from_backend(limit=4):
    limit = normalize_limit(limit, default=4, max_value=20)

    params = {
        "page": 1,
        "per_page": limit,
        "search": "",
        "type": "Tất cả",
        "department": "Tất cả",
        "status": "Tất cả",
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
        try:
            payload = json.loads(e.read().decode("utf-8"))
        except Exception:
            payload = {}

        return empty_dashboard_assets_payload(
            limit=limit,
            message=payload.get(
                "message",
                f"Lấy dữ liệu tài sản dashboard thất bại. HTTP {e.code}"
            ),
            status_code=e.code,
        )

    except (URLError, TimeoutError, json.JSONDecodeError):
        return empty_dashboard_assets_payload(
            limit=limit,
            message="Không thể kết nối đến backend để lấy dữ liệu tài sản dashboard.",
            status_code=500,
        )


def fetch_dashboard_activities_from_backend(limit=6):
    limit = normalize_limit(limit, default=6, max_value=20)

    params = {
        "page": 1,
        "limit": limit,
    }

    api_url = f"{BACKEND_ACTIVITIES_API}?{urlencode(params)}"

    req = Request(
        api_url,
        method="GET",
        headers=build_headers(),
    )

    try:
        with urlopen(req, timeout=5) as response:
            return parse_json_response(response)

    except HTTPError as e:
        try:
            payload = json.loads(e.read().decode("utf-8"))
        except Exception:
            payload = {}

        return empty_dashboard_activities_payload(
            limit=limit,
            message=payload.get(
                "message",
                f"Lấy dữ liệu hoạt động dashboard thất bại. HTTP {e.code}"
            ),
            status_code=e.code,
        )

    except (URLError, TimeoutError, json.JSONDecodeError):
        return empty_dashboard_activities_payload(
            limit=limit,
            message="Không thể kết nối đến backend để lấy dữ liệu hoạt động gần đây.",
            status_code=500,
        )


def build_dashboard_stats(filter_counts):
    filter_counts = filter_counts or DEFAULT_FILTER_COUNTS
    status_counts = filter_counts.get("status", {})

    total = status_counts.get("all", 0)
    using = status_counts.get("using", 0)
    available = status_counts.get("available", 0)
    maintenance = status_counts.get("maintenance", 0)
    broken = status_counts.get("broken", 0)

    problem = maintenance + broken

    return {
        "total": total,
        "using": using,
        "available": available,
        "maintenance": maintenance,
        "broken": broken,
        "problem": problem,
        "using_percent": safe_percent(using, total),
        "available_percent": safe_percent(available, total),
        "problem_percent": safe_percent(problem, total),
    }


def build_recent_asset_item(asset):
    asset = asset or {}
    status = asset.get("status") or "pending"

    user_display = (
        asset.get("user")
        or asset.get("receiver")
        or asset.get("department")
        or "—"
    )

    return {
        "id": asset.get("id") or "",
        "asset_name": asset.get("asset_name") or asset.get("asset") or "",
        "asset_code": asset.get("asset_code") or "",
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "status_class": STATUS_BADGE_CLASSES.get(status, "status-free"),
        "user": user_display,
    }


def build_recent_activity_item(activity):
    activity = activity or {}

    method = activity.get("method") or ""
    method = method.upper()

    dot_class = ACTIVITY_DOT_CLASSES.get(method, "activity-dot-info")

    return {
        "id": activity.get("id") or "",
        "user_id": activity.get("user_id") or "",
        "employee_code": activity.get("employee_code") or "",
        "full_name": activity.get("full_name") or "",
        "email": activity.get("email") or "",
        "role": activity.get("role") or "",

        "action": activity.get("action") or "Có hoạt động mới",
        "module": activity.get("module") or "",
        "method": method,
        "path": activity.get("path") or "",
        "status_code": activity.get("status_code"),

        "target_id": activity.get("target_id") or "",
        "target_name": activity.get("target_name") or "",

        "created_at": activity.get("created_at") or "",
        "dot_class": dot_class,
    }


def get_dashboard_overview_data(limit=4, activity_limit=6):
    asset_payload = fetch_dashboard_assets_from_backend(limit=limit)
    activity_payload = fetch_dashboard_activities_from_backend(limit=activity_limit)

    filter_counts = asset_payload.get("filter_counts") or DEFAULT_FILTER_COUNTS
    items = asset_payload.get("items") or []

    activity_items = activity_payload.get("data") or []

    stats = build_dashboard_stats(filter_counts)

    recent_assets = [
        build_recent_asset_item(item)
        for item in items
    ]

    recent_activities = [
        build_recent_activity_item(item)
        for item in activity_items
    ]

    status_code = asset_payload.get("status_code")

    return {
        "stats": stats,
        "recent_assets": recent_assets,
        "recent_activities": recent_activities,

        "scope": asset_payload.get("scope", {}),
        "activity_viewer": activity_payload.get("viewer", {}),

        "message": asset_payload.get("message"),
        "activity_message": activity_payload.get("message"),

        "status_code": status_code,
        "activity_status_code": activity_payload.get("status_code"),
    }