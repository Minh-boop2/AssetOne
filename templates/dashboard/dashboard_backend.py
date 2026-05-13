import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode


BACKEND_ASSETS_API = "http://127.0.0.1:5001/api/assets"


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


def safe_percent(value, total):
    if not total:
        return 0

    return min(100, max(0, round((value / total) * 100)))


def normalize_limit(limit):
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 4

    return max(1, min(limit, 20))


def fetch_dashboard_assets_from_backend(limit=4):
    limit = normalize_limit(limit)

    params = {
        "page": 1,
        "per_page": limit,
        "search": "",
        "type": "Tất cả",
        "department": "Tất cả",
        "status": "Tất cả",
    }

    api_url = f"{BACKEND_ASSETS_API}?{urlencode(params)}"

    try:
        with urlopen(api_url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))

        return payload

    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
        return {
            "items": [],
            "pagination": {
                "page": 1,
                "per_page": limit,
                "total_items": 0,
                "total_pages": 1,
            },
            "filter_counts": DEFAULT_FILTER_COUNTS,
        }


def build_dashboard_stats(filter_counts):
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


def get_dashboard_overview_data(limit=4):
    payload = fetch_dashboard_assets_from_backend(limit=limit)

    filter_counts = payload.get("filter_counts") or DEFAULT_FILTER_COUNTS
    items = payload.get("items") or []

    stats = build_dashboard_stats(filter_counts)

    recent_assets = [
        build_recent_asset_item(item)
        for item in items
    ]

    return {
        "stats": stats,
        "recent_assets": recent_assets,
    }