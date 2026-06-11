# File: templates/statistical/statistical_backend.py

import os
import re
import unicodedata
from datetime import datetime

import requests

from templates.assets.asset_backend import (
    fetch_assets_from_backend,
    get_status_label,
    normalize_asset_for_template,
)

from templates.report.report_backend import (
    api_get_reports,
    normalize_report,
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


def clean(value):
    return str(value or "").strip()


def norm(value):
    text = clean(value).lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d")


def safe_int(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


def percent(value, total):
    if total <= 0:
        return 0
    return round((safe_int(value) / total) * 100, 1)


def parse_time(value):
    text = clean(value).replace("Z", "").replace("+00:00", "")

    if not text:
        return datetime.min

    for fmt in [
        "%H:%M %d/%m/%Y",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]:
        try:
            return datetime.strptime(text[:26], fmt)
        except Exception:
            pass

    return datetime.min


def split_values(value):
    if value is None:
        return []

    if isinstance(value, dict):
        for key in ["asset_code", "code", "asset_name", "asset", "name", "id", "_id"]:
            if value.get(key):
                return split_values(value.get(key))
        return []

    if isinstance(value, (list, tuple, set)):
        result = []

        for item in value:
            result.extend(split_values(item))

        return [item for item in result if item]

    text = clean(value)

    if not text:
        return []

    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]

    return [
        part.strip().strip("'\"[]()")
        for part in re.split(r"\s*(?:,|;|\n|\|)\s*", text)
        if part.strip().strip("'\"[]()")
    ]


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


def extract_items(payload):
    if not isinstance(payload, dict):
        return []

    if isinstance(payload.get("items"), list):
        return payload.get("items")

    data = payload.get("data")

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ["items", "assets", "reports", "logs", "data"]:
            if isinstance(data.get(key), list):
                return data.get(key)

    for key in ["assets", "reports", "logs"]:
        if isinstance(payload.get(key), list):
            return payload.get(key)

    return []


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
    status_keys = ["using", "available", "maintenance", "broken"]

    if safe_int((status_counts or {}).get("pending")) > 0:
        status_keys.append("pending")

    for key in status_keys:
        count = safe_int((status_counts or {}).get(key))
        degrees = round((count / total) * 360, 2) if total and count > 0 else 0
        next_value = current + degrees

        segments.append({
            "label": get_status_label(key),
            "value": count,
            "value_text": count,
            "percent": percent(count, total),
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


def asset_key_values(asset):
    item = normalize_asset_for_template(asset)
    asset_code = clean(item.get("asset_code") or item.get("code"))
    asset_name = clean(item.get("asset") or item.get("asset_name") or item.get("name"))
    asset_id = clean(item.get("id") or item.get("_id") or item.get("asset_id"))

    return {
        "id": asset_id,
        "code": asset_code,
        "name": asset_name,
        "label": clean(f"{asset_code} - {asset_name}") if asset_code and asset_name else asset_code or asset_name or asset_id,
        "item": item,
    }


def report_asset_values(report):
    codes = split_values(
        report.get("asset_codes")
        or report.get("display_asset_code")
        or report.get("asset_code")
    )

    names = split_values(
        report.get("asset_names")
        or report.get("display_asset_name")
        or report.get("asset_name")
    )

    ids = split_values(
        report.get("asset_ids")
        or report.get("asset_id")
        or report.get("assets")
    )

    return codes, names, ids


def report_matches_asset(report, asset_info):
    codes, names, ids = report_asset_values(report)

    asset_id = norm(asset_info.get("id"))
    asset_code = norm(asset_info.get("code"))
    asset_name = norm(asset_info.get("name"))
    asset_label = norm(asset_info.get("label"))

    code_set = {norm(item) for item in codes if item}
    name_set = {norm(item) for item in names if item}
    id_set = {norm(item) for item in ids if item}
    full_text = norm(" ".join(codes + names + ids))

    return bool(
        (asset_id and asset_id in id_set)
        or (asset_code and asset_code in code_set)
        or (asset_name and asset_name in name_set)
        or (asset_label and asset_label in full_text)
        or (asset_code and asset_code in full_text)
        or (asset_name and asset_name in full_text)
    )


def issue_from_report(report, asset_info):
    description = clean(
        report.get("display_detail")
        or report.get("description")
        or report.get("detail")
        or report.get("content")
    )

    if not description:
        return ""

    labels = [
        asset_info.get("label"),
        asset_info.get("code"),
        asset_info.get("name"),
        asset_info.get("id"),
    ]

    lines = [line.strip() for line in description.splitlines() if line.strip()]

    for line in lines:
        if ":" not in line:
            continue

        left, right = line.split(":", 1)
        left_norm = norm(left)

        for label in labels:
            label_norm = norm(label)

            if label_norm and (left_norm == label_norm or label_norm in left_norm):
                return clean(right) or description

    return description


def fetch_report_issue_map(maintenance_assets, per_page=100):
    if not maintenance_assets:
        return {}

    success, payload, _ = api_get_reports({
        "page": 1,
        "limit": per_page,
    })

    if not success:
        return {}

    reports = [
        normalize_report(item, index)
        for index, item in enumerate(extract_items(payload))
    ]

    reports = sorted(
        reports,
        key=lambda report: parse_time(
            report.get("display_time")
            or report.get("time")
            or report.get("created_at")
        ),
        reverse=True,
    )

    issue_map = {}

    for raw_asset in maintenance_assets:
        asset_info = asset_key_values(raw_asset)
        map_key = norm(asset_info.get("id") or asset_info.get("code") or asset_info.get("name"))

        if not map_key:
            continue

        for report in reports:
            report_type = norm(
                report.get("display_report_type")
                or report.get("report_type")
                or report.get("type")
            )

            report_status = norm(
                report.get("display_report_status")
                or report.get("status")
                or report.get("report_status")
            )

            if "bao hong" not in report_type and "can cap moi" not in report_type:
                continue

            if any(text in report_status for text in ["tu choi", "da huy", "huy"]):
                continue

            if not report_matches_asset(report, asset_info):
                continue

            issue = issue_from_report(report, asset_info)

            if issue:
                issue_map[map_key] = issue
                break

    return issue_map


def normalize_maintenance_asset(asset, issue_map=None):
    asset_info = asset_key_values(asset)
    item = asset_info["item"]
    map_key = norm(asset_info.get("id") or asset_info.get("code") or asset_info.get("name"))
    issue = (
        (issue_map or {}).get(map_key)
        or item.get("issue")
        or item.get("notes")
        or item.get("spec")
        or "Cần kiểm tra bảo trì"
    )

    return {
        "asset_code": item.get("asset_code") or "---",
        "asset": item.get("asset") or item.get("asset_name") or "---",
        "issue": issue,
        "repair_cost_text": item.get("repair_cost_text") or item.get("repair_cost") or "0 đ",
    }


def fetch_recent_assets(limit=5):
    payload = fetch_assets_from_backend(page=1, per_page=limit)
    items = payload.get("items", []) or []

    return [
        normalize_recent_asset(asset)
        for asset in items[:limit]
    ], payload


def fetch_maintenance_assets(limit=5):
    payload = fetch_assets_from_backend(
        page=1,
        per_page=limit,
        status="maintenance",
    )

    items = payload.get("items", []) or []
    issue_map = fetch_report_issue_map(items, per_page=100)

    return [
        normalize_maintenance_asset(asset, issue_map)
        for asset in items[:limit]
    ]


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