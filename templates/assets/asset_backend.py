import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode, quote


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

    try:
        with urlopen(api_url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))

        return payload

    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
        return {
            "items": [],
            "pagination": {
                "page": 1,
                "per_page": per_page,
                "total_items": 0,
                "total_pages": 1,
            },
            "filter_counts": DEFAULT_FILTER_COUNTS,
        }


def fetch_asset_detail_from_backend(asset_id):
    api_url = f"{BACKEND_ASSETS_API}/{quote(asset_id)}"

    try:
        with urlopen(api_url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))

        return payload

    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
        return None


def delete_asset_from_backend(asset_id):
    api_url = f"{BACKEND_ASSETS_API}/{quote(asset_id)}"
    req = Request(api_url, method="DELETE")

    try:
        with urlopen(req, timeout=5) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}

        return True, payload

    except HTTPError as e:
        try:
            raw = e.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
        except Exception:
            payload = {}

        return False, {
            "message": payload.get("message", f"Xóa tài sản thất bại. HTTP {e.code}")
        }

    except (URLError, TimeoutError, json.JSONDecodeError):
        return False, {
            "message": "Không thể kết nối đến backend để xóa tài sản."
        }