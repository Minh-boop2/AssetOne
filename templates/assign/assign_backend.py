import os
import random
import string
import requests


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5001")
REQUEST_TIMEOUT = 5


DEFAULT_DEPARTMENTS = [
    "IT",
    "HR",
    "Finance",
    "Marketing",
    "Sales",
    "Operations",
]

DEFAULT_CATEGORIES = [
    "Laptop",
    "Desktop",
    "Monitor",
    "Printer",
    "Phone",
    "Tablet",
    "Network",
    "Other",
]

DEFAULT_LOCATIONS = [
    "Văn phòng HSU",
    "Tầng 1",
    "Tầng 2",
    "Tầng 3",
    "Kho IT",
    "Phòng họp",
]

DEFAULT_STATUS_OPTIONS = [
    "Đang sử dụng",
    "Chưa dùng",
]


def api_url(path):
    return f"{API_BASE_URL}{path}"


def api_request(method, path, **kwargs):
    try:
        response = requests.request(
            method,
            api_url(path),
            timeout=REQUEST_TIMEOUT,
            **kwargs
        )

        try:
            data = response.json()
        except Exception:
            data = {}

        if response.status_code >= 400:
            message = data.get("message") or f"Lỗi API {response.status_code}"
            return None, message

        return data, None

    except requests.RequestException as error:
        return None, f"Không kết nối được API backend: {error}"


def generate_frontend_asset_code():
    random_str = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=6)
    )
    return f"HSU-{random_str}"


def remove_all_key(count_dict):
    count_dict = count_dict or {}

    return {
        key: value
        for key, value in count_dict.items()
        if key != "all"
    }


def convert_counts_for_template(filter_counts):
    filter_counts = filter_counts or {}

    type_counts = filter_counts.get("type", {})
    department_counts = filter_counts.get("department", {})
    location_counts = filter_counts.get("location", {})
    status_counts = filter_counts.get("status", {})

    total = (
        type_counts.get("all")
        or department_counts.get("all")
        or location_counts.get("all")
        or status_counts.get("all")
        or 0
    )

    return {
        "total": total,
        "categories": remove_all_key(type_counts),
        "departments": remove_all_key(department_counts),
        "locations": remove_all_key(location_counts),
        "status": remove_all_key(status_counts),
    }


def build_filter_options(counts):
    categories = list((counts.get("categories") or {}).keys())
    departments = list((counts.get("departments") or {}).keys())
    locations = list((counts.get("locations") or {}).keys())
    statuses = list((counts.get("status") or {}).keys())

    if not categories:
        categories = DEFAULT_CATEGORIES

    if not departments:
        departments = DEFAULT_DEPARTMENTS

    if not locations:
        locations = DEFAULT_LOCATIONS

    alias_status_keys = {
        "pending",
        "processing",
        "completed",
        "rejected",
        "using",
        "available",
        "maintenance",
    }

    statuses = [
        status
        for status in statuses
        if status not in alias_status_keys
    ]

    for status in DEFAULT_STATUS_OPTIONS:
        if status not in statuses:
            statuses.append(status)

    return categories, departments, locations, statuses


def normalize_inventory_item(item):
    return {
        "name": item.get("name")
        or item.get("asset_name")
        or item.get("asset")
        or "",

        "type": item.get("type")
        or item.get("category")
        or "",

        "spec": item.get("spec")
        or item.get("notes")
        or item.get("description")
        or "",
    }


def get_inventory_from_assets_api():
    data, error = api_request(
        "GET",
        "/api/assets",
        params={
            "page": 1,
            "per_page": 1000,
            "search": "",
            "type": "Tất cả",
            "department": "Tất cả",
            "status": "Tất cả",
        }
    )

    if error:
        return []

    items = data.get("items", [])
    inventory = []

    for item in items:
        normalized = normalize_inventory_item(item)

        if normalized["name"]:
            inventory.append(normalized)

    return inventory