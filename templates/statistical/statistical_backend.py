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


BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:5001").rstrip("/")

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
    return round((safe_int(value) / total) * 100, 1) if total > 0 else 0


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


def get_json(url, params=None):
    try:
        response = requests.get(url, params=params or {}, timeout=8)

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
    keys = ["using", "available", "maintenance", "broken"]

    if safe_int((status_counts or {}).get("pending")) > 0:
        keys.append("pending")

    for key in keys:
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
    code = clean(item.get("asset_code") or item.get("code"))
    name = clean(item.get("asset") or item.get("asset_name") or item.get("name"))
    asset_id = clean(item.get("id") or item.get("_id") or item.get("asset_id"))

    return {
        "id": asset_id,
        "code": code,
        "name": name,
        "label": clean(f"{code} - {name}") if code and name else code or name or asset_id,
        "item": item,
    }


def asset_map_key(asset_info):
    return norm(asset_info.get("id") or asset_info.get("code") or asset_info.get("name"))


def asset_time(asset):
    item = normalize_asset_for_template(asset)

    for source in [item, asset if isinstance(asset, dict) else {}]:
        for key in ["maintenance_at", "updated_at", "modified_at", "created_at", "assigned_at", "time", "date"]:
            value = source.get(key)

            if value:
                parsed = parse_time(value)

                if parsed != datetime.min:
                    return parsed

    return datetime.min


def report_asset_values(report):
    codes = split_values(report.get("asset_codes") or report.get("display_asset_code") or report.get("asset_code"))
    names = split_values(report.get("asset_names") or report.get("display_asset_name") or report.get("asset_name"))
    ids = split_values(report.get("asset_ids") or report.get("asset_id"))

    return codes, names, ids


def report_asset_entries(report):
    assets = report.get("assets")

    if isinstance(assets, list) and assets:
        entries = []

        for asset in assets:
            if isinstance(asset, dict):
                code = clean(asset.get("asset_code") or asset.get("code"))
                name = clean(asset.get("asset_name") or asset.get("asset") or asset.get("name"))
                asset_id = clean(asset.get("asset_id") or asset.get("id") or asset.get("_id"))
            else:
                code = clean(asset)
                name = ""
                asset_id = ""

            label = clean(f"{code} - {name}") if code and name else code or name or asset_id

            if label:
                entries.append({
                    "id": asset_id,
                    "code": code,
                    "name": name,
                    "label": label,
                })

        if entries:
            return entries

    codes, names, ids = report_asset_values(report)
    total = max(len(codes), len(names), len(ids), 0)
    entries = []

    for index in range(total):
        code = codes[index] if index < len(codes) else ""
        name = names[index] if index < len(names) else ""
        asset_id = ids[index] if index < len(ids) else ""
        label = clean(f"{code} - {name}") if code and name else code or name or asset_id

        if label:
            entries.append({
                "id": asset_id,
                "code": code,
                "name": name,
                "label": label,
            })

    return entries


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

    for line in [line.strip() for line in description.splitlines() if line.strip()]:
        if ":" not in line:
            continue

        left, right = line.split(":", 1)
        left_norm = norm(left)

        for label in labels:
            label_norm = norm(label)

            if label_norm and (left_norm == label_norm or label_norm in left_norm):
                return clean(right) or description

    return description


def is_maintenance_report(report):
    report_type = norm(report.get("display_report_type") or report.get("report_type") or report.get("type"))
    report_status = norm(report.get("display_report_status") or report.get("status") or report.get("report_status"))

    if "bao hong" not in report_type and "can cap moi" not in report_type:
        return False

    return not any(text in report_status for text in ["tu choi", "da huy", "huy"])


def build_asset_lookup(assets):
    lookup = {}
    asset_by_key = {}

    for asset in assets:
        asset_info = asset_key_values(asset)
        key = asset_map_key(asset_info)

        if not key:
            continue

        asset_by_key[key] = asset

        for value in [asset_info.get("id"), asset_info.get("code"), asset_info.get("name"), asset_info.get("label")]:
            value_key = norm(value)

            if value_key:
                lookup[value_key] = key

    return lookup, asset_by_key


def match_entry_key(entry, lookup):
    for value in [entry.get("id"), entry.get("code"), entry.get("name"), entry.get("label")]:
        value_key = norm(value)

        if value_key and value_key in lookup:
            return lookup[value_key]

    entry_text = norm(" ".join([
        entry.get("id", ""),
        entry.get("code", ""),
        entry.get("name", ""),
        entry.get("label", ""),
    ]))

    for value_key, map_key in lookup.items():
        if value_key and value_key in entry_text:
            return map_key

    return ""


def fetch_report_records(per_page=200):
    success, payload, _ = api_get_reports({
        "page": 1,
        "limit": per_page,
    })

    if not success:
        return []

    reports = [
        normalize_report(item, index)
        for index, item in enumerate(extract_items(payload))
    ]

    return sorted(
        reports,
        key=lambda report: parse_time(report.get("display_time") or report.get("time") or report.get("created_at"))
    )


def build_maintenance_report_context(maintenance_assets):
    lookup, asset_by_key = build_asset_lookup(maintenance_assets)
    reports = fetch_report_records(per_page=200)
    issue_map = {}
    ordered_keys = []

    for report in reports:
        if not is_maintenance_report(report):
            continue

        for entry in report_asset_entries(report):
            key = match_entry_key(entry, lookup)

            if not key or key not in asset_by_key:
                continue

            issue = issue_from_report(report, asset_key_values(asset_by_key[key]))

            if issue:
                issue_map[key] = issue

            if key in ordered_keys:
                ordered_keys.remove(key)

            ordered_keys.append(key)

    return issue_map, ordered_keys, asset_by_key


def fallback_maintenance_keys(maintenance_assets):
    has_time = any(asset_time(asset) != datetime.min for asset in maintenance_assets)
    ordered_assets = sorted(maintenance_assets, key=asset_time) if has_time else list(reversed(maintenance_assets))
    keys = []

    for asset in ordered_assets:
        key = asset_map_key(asset_key_values(asset))

        if key and key not in keys:
            keys.append(key)

    return keys


def normalize_maintenance_asset(asset, issue_map=None):
    asset_info = asset_key_values(asset)
    item = asset_info["item"]
    map_key = asset_map_key(asset_info)

    return {
        "asset_code": item.get("asset_code") or "---",
        "asset": item.get("asset") or item.get("asset_name") or "---",
        "issue": (
            (issue_map or {}).get(map_key)
            or item.get("issue")
            or item.get("notes")
            or item.get("spec")
            or "Cần kiểm tra bảo trì"
        ),
        "repair_cost_text": item.get("repair_cost_text") or item.get("repair_cost") or "0 đ",
    }


def fetch_recent_assets(limit=5):
    payload = fetch_assets_from_backend(page=1, per_page=limit)
    items = payload.get("items", []) or []

    return [normalize_recent_asset(asset) for asset in items[:limit]], payload


def fetch_maintenance_assets(limit=5):
    payload = fetch_assets_from_backend(
        page=1,
        per_page=max(limit * 12, 60),
        status="maintenance",
    )

    maintenance_assets = payload.get("items", []) or []

    if not maintenance_assets:
        return []

    issue_map, report_keys, asset_by_key = build_maintenance_report_context(maintenance_assets)
    ordered_keys = []

    for key in report_keys + fallback_maintenance_keys(maintenance_assets):
        if key in asset_by_key and key not in ordered_keys:
            ordered_keys.append(key)

    latest_keys = list(reversed(ordered_keys[-limit:]))

    return [
        normalize_maintenance_asset(asset_by_key[key], issue_map)
        for key in latest_keys
        if key in asset_by_key
    ]


def get_statistical_employees_context(args, current_user):
    payload, status_code = get_json(
        f"{BACKEND_API_URL}/api/statistical/employees",
        params=args,
    )

    context = get_default_employees_context()
    context["current_user"] = current_user or {}

    if status_code != 200 or not payload.get("success"):
        context["statistical_error"] = payload.get("message") or "Không thể tải dữ liệu thống kê nhân viên"
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