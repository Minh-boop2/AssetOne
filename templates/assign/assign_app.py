from flask import render_template, request, redirect, url_for, flash
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
    """
    Backend API trả:
    {
        "type": {"all": 10, "Laptop": 3},
        "department": {"all": 10, "IT": 2},
        "location": {"all": 10},
        "status": {"all": 10}
    }

    Template cũ cần:
    {
        "total": 10,
        "categories": {},
        "departments": {},
        "locations": {},
        "status": {}
    }
    """

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


def register_assign_routes(app):
    # --- 1. TRANG DANH SÁCH ---
    @app.route("/assign")
    def assign_page():
        search_q = request.args.get("search", "", type=str).strip()
        selected_dept = request.args.get("department", "Tất cả", type=str)

        selected_cat = (
            request.args.get("category", None, type=str)
            or request.args.get("type", "Tất cả", type=str)
        )

        selected_loc = request.args.get("location", "Tất cả", type=str)
        selected_status = request.args.get("status", "Tất cả", type=str)

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        data, error = api_request(
            "GET",
            "/api/assign",
            params={
                "page": page,
                "per_page": per_page,
                "search": search_q,
                "type": selected_cat,
                "department": selected_dept,
                "status": selected_status,
                "location": selected_loc,
            }
        )

        if error:
            flash(error, "danger")
            data = {
                "items": [],
                "pagination": {
                    "page": 1,
                    "per_page": per_page,
                    "total_items": 0,
                    "total_pages": 1,
                },
                "filter_counts": {},
            }

        assigns = data.get("items", [])
        pagination = data.get("pagination", {})
        counts = convert_counts_for_template(data.get("filter_counts", {}))

        categories, departments, locations, status_options = build_filter_options(counts)

        return render_template(
            "assign/assign_overview.html",
            assigns=assigns,
            counts=counts,
            departments=departments,
            categories=categories,
            locations=locations,
            status_options=status_options,
            current_page=pagination.get("page", page),
            total_pages=pagination.get("total_pages", 1),
            total_items=pagination.get("total_items", 0),
            search_q=search_q,
            selected_dept=selected_dept,
            selected_cat=selected_cat,
            selected_loc=selected_loc,
            selected_status=selected_status,
        )

    # --- 2. TRANG TẠO MỚI ---
    @app.route("/assign/create", methods=["GET", "POST"])
    def assign_create():
        if request.method == "POST":
            flash("API tạo phiếu cấp phát chưa được bật.", "warning")
            return redirect(url_for("assign_page"))

        inventory = get_inventory_from_assets_api()

        inventory_types = sorted(
            list({
                item.get("type")
                for item in inventory
                if item.get("type")
            })
        )

        if not inventory_types:
            inventory_types = DEFAULT_CATEGORIES

        return render_template(
            "assign/assign_create.html",
            inventory=inventory,
            departments=DEFAULT_DEPARTMENTS,
            locations=DEFAULT_LOCATIONS,
            categories=inventory_types,
            inventory_types=inventory_types,
            suggested_code=generate_frontend_asset_code(),
        )

    # --- 3. TRANG CHI TIẾT ---
    @app.route("/assign/detail/<string:id>")
    def assign_detail(id):
        info, error = api_request("GET", f"/api/assign/{id}")

        if error or not info:
            flash(error or "Không tìm thấy thông tin.", "danger")
            return redirect(url_for("assign_page"))

        specs = {
            "spec": info.get("spec")
            or info.get("notes")
            or "Không có dữ liệu cấu hình."
        }

        return render_template(
            "assign/assign_detail.html",
            info=info,
            specs=specs,
        )

    # --- 4. TRANG CHỈNH SỬA ---
    @app.route("/assign/edit/<string:id>", methods=["GET", "POST"])
    def assign_edit(id):
        assign, error = api_request("GET", f"/api/assign/{id}")

        if error or not assign:
            flash(error or "Bản ghi không tồn tại.", "danger")
            return redirect(url_for("assign_page"))

        if request.method == "POST":
            flash("API cập nhật phiếu cấp phát chưa được bật.", "warning")
            return redirect(url_for("assign_detail", id=id))

        inventory = get_inventory_from_assets_api()

        return render_template(
            "assign/assign_edit.html",
            assign=assign,
            inventory=inventory,
            departments=DEFAULT_DEPARTMENTS,
            categories=DEFAULT_CATEGORIES,
            locations=DEFAULT_LOCATIONS,
            status_options=DEFAULT_STATUS_OPTIONS,
        )

    # --- 5. ACTION PHÊ DUYỆT ---
    @app.route("/assign/approve/<string:id>")
    def approve_request(id):
        data, error = api_request("PATCH", f"/api/assign/{id}/approve")

        if error:
            flash(error, "danger")
        else:
            flash(f"Đã phê duyệt phiếu #{id}", "success")

        return redirect(url_for("assign_page"))

    # --- 6. ACTION TỪ CHỐI ---
    @app.route("/assign/reject/<string:id>")
    def reject_request(id):
        data, error = api_request("PATCH", f"/api/assign/{id}/reject")

        if error:
            flash(error, "danger")
        else:
            flash(f"Đã từ chối yêu cầu phiếu #{id}", "warning")

        return redirect(url_for("assign_page"))

    # --- 7. ACTION XÓA ---
    @app.route("/assign/delete/<string:id>")
    def delete_assign(id):
        data, error = api_request("DELETE", f"/api/assign/{id}")

        if error:
            flash(error, "danger")
        else:
            flash(f"Đã xóa bản ghi #{id}", "warning")

        return redirect(url_for("assign_page"))