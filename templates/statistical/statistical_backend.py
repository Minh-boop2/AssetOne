<<<<<<< HEAD
import os
import re
import unicodedata
=======
# File: templates/statistical/statistical_backend.py
# Nhiệm vụ:
# - Giữ thống kê nhân viên từ API cũ.
# - Thống kê tài sản lấy trực tiếp cùng nguồn với trang /assets.
# - Bảng Bảo trì tài sản chỉ hiện 5 tài sản mới nhất đang status = maintenance.
# - Cột Lỗi lấy từ nội dung / ghi chú báo cáo gần nhất liên quan tới tài sản.

import os
import re
import unicodedata
from collections import Counter
>>>>>>> 619993c3769599db132f4ea465a37b35f7832fb3
from datetime import datetime

import requests

from templates.assets.asset_backend import (
    fetch_assets_from_backend,
    normalize_asset_for_template,
)

from templates.report.report_backend import (
    api_get_reports,
    normalize_report,
)
<<<<<<< HEAD

=======
>>>>>>> 619993c3769599db132f4ea465a37b35f7832fb3

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:5001").rstrip("/")

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:5001").rstrip("/")

STATUS_LABELS = {
    "using": "Đang sử dụng",
    "available": "Chưa sử dụng",
    "maintenance": "Bảo trì",
    "broken": "Hỏng",
    "pending": "Chờ duyệt",
}

STATUS_CLASSES = {
    "using": "success",
    "available": "info",
    "maintenance": "warning",
    "broken": "danger",
    "pending": "purple",
}

STATUS_COLORS = {
    "using": "#22c55e",
    "available": "#3b82f6",
    "maintenance": "#f97316",
    "broken": "#ef4444",
    "pending": "#8b5cf6",
}

STATUS_DOTS = {
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
<<<<<<< HEAD
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
=======
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.replace("đ", "d")


def first(source, *keys, default=""):
    if not isinstance(source, dict):
        return default

    for key in keys:
        value = source.get(key)
        if value not in [None, ""]:
            return value

    return default
>>>>>>> 619993c3769599db132f4ea465a37b35f7832fb3


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


def get_default_assets_context(current_user=None):
    return {
        "current_user": current_user or {},
        "statistical_error": None,
        "total_assets": 0,
        "total_damaged": 0,
        "total_broken_assets": 0,
        "total_repair_cost_text": "0 ₫",
        "type_items": [],
        "status_segments": [],
        "damaged_assets": [],
        "recent_assets": [],
    }


<<<<<<< HEAD
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
=======
def get_json(url, headers=None, params=None):
    try:
        response = requests.get(url, headers=headers or {}, params=params or {}, timeout=8)

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


def extract_pagination(payload):
    if not isinstance(payload, dict):
        return {}

    if isinstance(payload.get("pagination"), dict):
        return payload.get("pagination")

    data = payload.get("data")

    if isinstance(data, dict) and isinstance(data.get("pagination"), dict):
        return data.get("pagination")

    return {}


def get_total_pages(payload):
    pagination = extract_pagination(payload)

    try:
        return int(pagination.get("total_pages") or pagination.get("pages") or 1)
    except Exception:
        return 1


def parse_time(value):
    text = clean(value)

    if not text:
        return datetime.min

    text = text.replace("Z", "").replace("+00:00", "")

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
        return split_values(
            first(
                value,
                "asset_code",
                "code",
                "asset_name",
                "asset",
                "name",
                "id",
                "_id",
            )
        )

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
        for part in re.split(r"\s*(?:,|;|\|)\s*", text)
        if part.strip().strip("'\"[]()")
    ]


def normalize_asset(item):
    asset = normalize_asset_for_template(item or {})
    status = clean(asset.get("status") or "pending") or "pending"

    return {
        **asset,
        "id": clean(asset.get("id") or asset.get("_id") or asset.get("asset_code")),
        "asset_code": clean(asset.get("asset_code") or asset.get("code") or asset.get("id")),
        "asset": clean(asset.get("asset") or asset.get("asset_name") or asset.get("name") or asset.get("asset_code")) or "Chưa có tên tài sản",
        "asset_name": clean(asset.get("asset_name") or asset.get("asset") or asset.get("name")),
        "type": clean(asset.get("type") or asset.get("category")) or "Khác",
        "status": status,
        "status_text": STATUS_LABELS.get(status, clean(asset.get("status")) or status),
        "status_class": STATUS_CLASSES.get(status, "info"),
        "receiver": clean(asset.get("receiver") or asset.get("user")) or "---",
        "created_at": clean(asset.get("created_at") or asset.get("time") or asset.get("date")),
        "updated_at": clean(asset.get("updated_at") or asset.get("created_at") or asset.get("time") or asset.get("date")),
        "notes": clean(asset.get("notes") or asset.get("spec") or asset.get("description")),
    }


def unique_assets(items):
    result = []
    seen = set()

    for item in items:
        asset = normalize_asset(item)
        key = norm(asset.get("id") or asset.get("asset_code") or asset.get("asset"))

        if not key or key in seen:
            continue

        seen.add(key)
        result.append(asset)

    return result


def fetch_all_assets(max_pages=50, per_page=100):
    all_items = []

    for page in range(1, max_pages + 1):
        payload = fetch_assets_from_backend(
            page=page,
            per_page=per_page,
            search="",
            asset_type="Tất cả",
            asset_types=None,
            department="Tất cả",
            status="Tất cả",
        )

        items = extract_items(payload)
        all_items.extend(items)

        total_pages = get_total_pages(payload)

        if page >= total_pages or not items:
            break

    return unique_assets(all_items)


def fetch_all_reports(max_pages=50, per_page=100):
    reports = []

    for page in range(1, max_pages + 1):
        success, payload, _ = api_get_reports({
            "page": page,
            "limit": per_page,
        })

        if not success:
            break

        items = extract_items(payload)
        reports.extend([
            normalize_report(item, index)
            for index, item in enumerate(items)
        ])

        total_pages = get_total_pages(payload)

        if page >= total_pages or not items:
            break

    return reports


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


def report_matches_asset(report, asset):
    codes, names, ids = report_asset_values(report)

    asset_id = norm(asset.get("id"))
    asset_code = norm(asset.get("asset_code"))
    asset_name = norm(asset.get("asset"))

    code_set = {norm(item) for item in codes if item}
    name_set = {norm(item) for item in names if item}
    id_set = {norm(item) for item in ids if item}

    if asset_id and asset_id in id_set:
        return True

    if asset_code and asset_code in code_set:
        return True

    if asset_name and asset_name in name_set:
        return True

    full_text = norm(" ".join(codes + names + ids))

    return bool(
        (asset_id and asset_id in full_text)
        or (asset_code and asset_code in full_text)
        or (asset_name and asset_name in full_text)
    )


def issue_from_report(report, asset):
    description = clean(
        report.get("display_detail")
        or report.get("description")
        or report.get("detail")
        or report.get("content")
    )

    if not description:
        return ""

    labels = [
        clean(f"{asset.get('asset_code')} - {asset.get('asset')}"),
        clean(asset.get("asset_code")),
        clean(asset.get("asset")),
        clean(asset.get("id")),
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


def build_issue_map(reports, assets):
    issue_map = {}
    sorted_reports = sorted(
        reports,
        key=lambda report: parse_time(
            report.get("display_time")
            or report.get("time")
            or report.get("created_at")
        ),
        reverse=True,
    )

    for asset in assets:
        asset_key = norm(asset.get("id") or asset.get("asset_code") or asset.get("asset"))

        if not asset_key:
            continue

        for report in sorted_reports:
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

            if any(value in report_status for value in ["da huy", "tu choi", "huy"]):
                continue

            if not report_matches_asset(report, asset):
                continue

            issue = issue_from_report(report, asset)

            if issue:
                issue_map[asset_key] = issue
                break

    return issue_map


def percent_items(counter):
    max_value = max(counter.values()) if counter else 1

    return [
        {
            "label": label or "Khác",
            "value": value,
            "value_text": value,
            "percent": round((value / max_value) * 100, 2) if max_value else 0,
        }
        for label, value in counter.most_common()
    ]


def status_segments_from_counter(counter, total):
    total = total or sum(counter.values()) or 0
    start = 0
    result = []

    for status in ["using", "available", "maintenance", "broken", "pending"]:
        value = counter.get(status, 0)

        if not value:
            continue

        percent = round((value / total) * 100, 1) if total else 0
        degrees = (value / total) * 360 if total else 0
        end = start + degrees

        result.append({
            "label": STATUS_LABELS.get(status, status),
            "class": STATUS_DOTS.get(status, "purple"),
            "color": STATUS_COLORS.get(status, "#8b5cf6"),
            "value": value,
            "value_text": value,
            "percent": percent,
            "from_deg": round(start, 2),
            "to_deg": round(end, 2),
        })

        start = end

    return result
>>>>>>> 619993c3769599db132f4ea465a37b35f7832fb3


def get_statistical_employees_context(args, current_user):
    payload, status_code = get_json(
        f"{BACKEND_API_URL}/api/statistical/employees",
        params=args,
    )

    context = get_default_employees_context()
    context["current_user"] = current_user or {}

    if status_code != 200 or not payload.get("success"):
<<<<<<< HEAD
        context["statistical_error"] = payload.get("message") or "Không thể tải dữ liệu thống kê nhân viên"
=======
        context["statistical_error"] = (
            payload.get("message")
            or "Không thể tải dữ liệu thống kê nhân viên"
        )
>>>>>>> 619993c3769599db132f4ea465a37b35f7832fb3
        return context

    data = payload.get("data") or {}
    context.update(data)
    context["statistical_error"] = None

    return context


<<<<<<< HEAD
def get_statistical_assets_context(args, current_user):
    recent_assets, payload = fetch_recent_assets(limit=5)
    pagination = payload.get("pagination", {}) or {}
    filter_counts = payload.get("filter_counts", {}) or {}
    status_counts = filter_counts.get("status", {}) or {}
    type_counts = filter_counts.get("type", {}) or {}
=======
def get_statistical_assets_context(args=None, current_user=None):
    context = get_default_assets_context(current_user)
    assets = fetch_all_assets()

    if not assets:
        return context
>>>>>>> 619993c3769599db132f4ea465a37b35f7832fb3

    reports = fetch_all_reports()
    issue_map = build_issue_map(reports, assets)

    total_assets = len(assets)
    type_counter = Counter(asset.get("type") or "Khác" for asset in assets)
    status_counter = Counter(asset.get("status") or "pending" for asset in assets)

    maintenance_all = [
        asset
        for asset in assets
        if asset.get("status") == "maintenance"
    ]

    maintenance_latest = [
        asset
        for _, asset in sorted(
            enumerate(maintenance_all),
            key=lambda pair: (
                parse_time(pair[1].get("updated_at") or pair[1].get("created_at")),
                -pair[0],
            ),
            reverse=True,
        )[:5]
    ]

    broken_assets = [
        asset
        for asset in assets
        if asset.get("status") == "broken"
    ]

    damaged_assets = []

    for asset in maintenance_latest:
        key = norm(asset.get("id") or asset.get("asset_code") or asset.get("asset"))

        damaged_assets.append({
            "asset_code": asset.get("asset_code") or "---",
            "asset": asset.get("asset") or "---",
            "issue": issue_map.get(key) or asset.get("notes") or "Cần kiểm tra hoặc bảo trì",
        })

    recent_assets = sorted(
        enumerate(assets),
        key=lambda pair: (
            parse_time(pair[1].get("created_at") or pair[1].get("updated_at")),
            -pair[0],
        ),
        reverse=True,
    )[:5]

    context.update({
        "total_assets": total_assets,
        "total_damaged": len(maintenance_all),
        "total_broken_assets": len(broken_assets),
        "total_repair_cost_text": "0 ₫",
        "type_items": percent_items(type_counter),
        "status_segments": status_segments_from_counter(status_counter, total_assets),
        "damaged_assets": damaged_assets,
        "recent_assets": [
            {
                "asset_code": asset.get("asset_code") or "---",
                "asset": asset.get("asset") or "---",
                "type": asset.get("type") or "---",
                "receiver": asset.get("receiver") or "---",
                "status": asset.get("status_text") or STATUS_LABELS.get(asset.get("status"), asset.get("status") or "---"),
                "status_class": asset.get("status_class") or STATUS_CLASSES.get(asset.get("status"), "info"),
            }
            for _, asset in recent_assets
        ],
    })

    return context