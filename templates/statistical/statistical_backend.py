# File: templates/statistical/statistical_backend.py

import os
import requests

from templates.assets.asset_backend import (
    fetch_assets_from_backend,
    get_status_label,
    normalize_asset_for_template,
)


BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:5001")


TYPE_LABELS = {
    "laptop": "Laptop",
    "pc": "Máy tính bàn",
    "printer": "Máy in",
    "monitor": "Màn hình",
    "phone": "Điện thoại",
    "projector": "Máy chiếu",
    "scanner": "Máy scan",
    "network": "Thiết bị mạng",
    "ups": "UPS",
    "camera": "Camera",
    "speaker": "Loa",
    "microphone": "Micro",
    "keyboard": "Bàn phím",
    "mouse": "Chuột",
    "tablet": "Máy tính bảng",
    "server": "Máy chủ",
    "router": "Router",
    "switch": "Switch",
    "storage": "Lưu trữ",
    "accessory": "Phụ kiện",
    "other": "Khác",
}

STATUS_COLORS = {
    "using": "#22c55e",
    "available": "#3b82f6",
    "maintenance": "#f97316",
    "broken": "#ef4444",
    "pending": "#8b5cf6",
}

STATUS_CLASSES = {
    "using": "green",
    "available": "cyan",
    "maintenance": "orange",
    "broken": "red",
    "pending": "purple",
}


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


def get_default_assets_context():
    return {
        "total_assets": 0,
        "total_damaged": 0,
        "total_broken_assets": 0,
        "type_items": [],
        "status_segments": [],
        "damaged_assets": [],
        "recent_assets": [],
        "statistical_error": None,
        "current_user": {},
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
        return {"success": False, "message": str(error)}, 500


def safe_int(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


def percent(value, total):
    if total <= 0:
        return 0

    return round((safe_int(value) / total) * 100, 1)


def build_type_items(type_counts, total):
    items = []

    for key, value in (type_counts or {}).items():
        if key == "all":
            continue

        count = safe_int(value)

        if count <= 0:
            continue

        items.append({
            "label": TYPE_LABELS.get(key, key),
            "value": count,
            "value_text": count,
            "percent": percent(count, total),
        })

    return sorted(items, key=lambda item: item["value"], reverse=True)


def build_status_segments(status_counts, total):
    current = 0
    segments = []

    for key in ["using", "available", "maintenance", "broken", "pending"]:
        count = safe_int((status_counts or {}).get(key))

        if count <= 0:
            continue

        value_percent = percent(count, total)
        degrees = round((count / total) * 360, 2) if total else 0
        next_value = current + degrees

        segments.append({
            "label": get_status_label(key),
            "value": count,
            "value_text": count,
            "percent": value_percent,
            "from_deg": current,
            "to_deg": next_value,
            "color": STATUS_COLORS.get(key, "#94a3b8"),
            "class": STATUS_CLASSES.get(key, "purple"),
        })

        current = next_value

    return segments


def format_asset_status_class(status):
    return STATUS_CLASSES.get(status, "purple")


def normalize_recent_asset(asset):
    item = normalize_asset_for_template(asset)
    status = item.get("status") or "available"

    return {
        "asset_code": item.get("asset_code") or "---",
        "asset": item.get("asset") or item.get("asset_name") or "---",
        "type": item.get("type") or item.get("category") or "---",
        "receiver": item.get("receiver") or item.get("user") or "---",
        "status": get_status_label(status),
        "status_class": format_asset_status_class(status),
    }


def normalize_maintenance_asset(asset):
    item = normalize_asset_for_template(asset)
    issue = item.get("issue") or item.get("notes") or item.get("spec") or "Cần kiểm tra bảo trì"
    cost = item.get("repair_cost_text") or item.get("repair_cost") or "0 đ"

    return {
        "asset_code": item.get("asset_code") or "---",
        "asset": item.get("asset") or item.get("asset_name") or "---",
        "issue": issue,
        "repair_cost_text": cost,
    }


def fetch_recent_assets(limit=5):
    payload = fetch_assets_from_backend(page=1, per_page=limit)
    items = payload.get("items", []) or []

    return [
        normalize_recent_asset(asset)
        for asset in items[:limit]
    ], payload


def fetch_maintenance_assets(limit=5):
    items = []

    for status in ["maintenance", "broken"]:
        payload = fetch_assets_from_backend(
            page=1,
            per_page=limit,
            status=status,
        )

        for asset in payload.get("items", []) or []:
            if len(items) >= limit:
                return items

            items.append(normalize_maintenance_asset(asset))

    return items


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

    context.update(payload.get("data") or {})
    context["statistical_error"] = None

    return context


def get_statistical_assets_context(args, current_user):
    recent_assets, payload = fetch_recent_assets(limit=5)
    pagination = payload.get("pagination", {}) or {}
    filter_counts = payload.get("filter_counts", {}) or {}

    status_counts = filter_counts.get("status", {}) or {}
    type_counts = filter_counts.get("type", {}) or {}

    total_assets = safe_int(
        pagination.get("total_items")
        or status_counts.get("all")
        or type_counts.get("all")
    )

    context = get_default_assets_context()
    context.update({
        "current_user": current_user or {},
        "total_assets": total_assets,
        "total_damaged": safe_int(status_counts.get("maintenance")),
        "total_broken_assets": safe_int(status_counts.get("broken")),
        "type_items": build_type_items(type_counts, total_assets),
        "status_segments": build_status_segments(status_counts, total_assets),
        "damaged_assets": fetch_maintenance_assets(limit=5),
        "recent_assets": recent_assets,
        "statistical_error": payload.get("message"),
    })

    return context


def get_statistical_overview_context(args, current_user):
    return get_statistical_employees_context(args, current_user)