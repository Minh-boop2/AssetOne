from flask import render_template, request, redirect, url_for, flash, jsonify, session

from .assign_backend import (
    DEFAULT_DEPARTMENTS,
    DEFAULT_CATEGORIES,
    DEFAULT_LOCATIONS,
    DEFAULT_STATUS_OPTIONS,
    api_request,
    generate_frontend_asset_code,
    convert_counts_for_template,
    build_filter_options,
    get_inventory_from_assets_api,
    get_active_users_from_api,
    assign_many_assets_to_user_api,
    unassign_asset_from_user_api,
)


TYPE_LABELS = {
    "laptop": "Laptop",
    "pc": "Máy tính bàn",
    "desktop": "Máy tính bàn",
    "printer": "Máy in",
    "monitor": "Màn hình",
    "phone": "Điện thoại",
    "projector": "Máy chiếu",
    "scanner": "Máy quét",
    "network": "Thiết bị mạng",
    "ups": "UPS",
    "camera": "Camera",
    "webcam": "Camera",
    "speaker": "Loa",
    "microphone": "Micro",
    "mic": "Micro",
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


def get_current_user():
    return session.get("user") or session.get("current_user") or {}


def is_logged_in():
    return bool(get_current_user())


def is_ajax_request():
    return (
        request.args.get("ajax") == "1"
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


def is_fast_table_request():
    # NOTE: Dùng riêng cho fetch HTML thay .assign-table-card.
    # Request này không thay filter nên không cần gọi inventory và counts.
    return (
        request.args.get("fast_table") == "1"
        or request.headers.get("X-Requested-With") == "fetch"
    )


def wants_json_response():
    # NOTE: Dùng cho thao tác POST bằng fetch như thu hồi nhiều.
    # Không dùng hàm này cho GET /assign vì trang đang fetch HTML để thay bảng.
    return (
        request.headers.get("X-Requested-With") in ["XMLHttpRequest", "fetch"]
        or request.is_json
        or "application/json" in request.headers.get("Accept", "")
    )


def user_can(module_key, action):
    user = get_current_user()
    role = user.get("role")

    if user.get("is_admin") or role == "ADMIN":
        return True

    if module_key == "assign" and role == "QUAN_LY":
        return action in ["view", "create", "update", "delete", "approve"]

    can = user.get("can") or {}
    return can.get(module_key, {}).get(action) is True


def require_login():
    if not is_logged_in():
        return redirect(url_for("login_page"))

    return None


def require_assign_permission(action):
    login_redirect = require_login()

    if login_redirect:
        return login_redirect

    if not user_can("assign", action):
        flash("Bạn không có quyền thực hiện chức năng này.", "danger")
        return redirect(url_for("dashboard_overview"))

    return None


def assign_permission_context():
    return {
        "current_user": get_current_user(),
        "can_view_assign": user_can("assign", "view"),
        "can_create_assign": user_can("assign", "create"),
        "can_update_assign": user_can("assign", "update"),
        "can_delete_assign": user_can("assign", "delete"),
        "can_approve_assign": user_can("assign", "approve"),
    }


def get_asset_categories_from_inventory():
    inventory = get_inventory_from_assets_api()

    categories = sorted(
        list(
            {
                item.get("type") or item.get("category")
                for item in inventory
                if item.get("type") or item.get("category")
            }
        )
    )

    if not categories:
        categories = DEFAULT_CATEGORIES

    return inventory, categories


def can_assign_asset(assign):
    if not assign:
        return False

    status = assign.get("status")
    asset_status = assign.get("asset_status")

    return (
        status in ["Chưa dùng", "Chưa sử dụng"]
        or asset_status in ["available", "Chưa sử dụng"]
    )


def can_unassign_asset(assign):
    if not assign:
        return False

    return assign.get("status") == "Đang sử dụng"


def get_type_label(value):
    if not value:
        return "---"

    return TYPE_LABELS.get(str(value).lower(), value)


def get_status_class(status):
    if status == "Đang sử dụng":
        return "status-hoanthanh"

    if status in ["Chưa dùng", "Chưa sử dụng"]:
        return "status-reject"

    return "status-dangxuly"


def split_asset_ids(raw_ids="", fallback_id=""):
    asset_ids = []

    for value in str(raw_ids or "").split(","):
        value = value.strip()

        if value and value not in asset_ids:
            asset_ids.append(value)

    if fallback_id and fallback_id not in asset_ids:
        asset_ids.insert(0, fallback_id)

    return asset_ids


def get_asset_ids_for_give(default_id):
    raw_ids = (
        request.form.get("asset_ids", "").strip()
        if request.method == "POST"
        else request.args.get("ids", "").strip()
    )

    asset_ids = split_asset_ids(raw_ids, fallback_id=default_id)

    if request.method == "POST":
        for extra_id in request.form.getlist("asset_id_list"):
            extra_id = str(extra_id or "").strip()

            if extra_id and extra_id not in asset_ids:
                asset_ids.append(extra_id)

    return asset_ids


def load_assign_assets(asset_ids):
    assets = []
    errors = []

    for asset_id in asset_ids:
        info, error = api_request("GET", f"/api/assign/{asset_id}")

        if error or not info:
            errors.append(error or f"Không tìm thấy tài sản #{asset_id}")
        else:
            assets.append(info)

    return assets, errors


def build_give_redirect_url(id, asset_ids):
    if len(asset_ids) <= 1:
        return url_for("assign_give", id=id)

    return url_for("assign_give", id=id, ids=",".join(asset_ids))


def build_assign_row_payload(row):
    row_id = (
        row.get("id")
        or row.get("_id")
        or row.get("assign_id")
        or row.get("asset_id")
        or ""
    )

    row_type = row.get("type") or row.get("category") or ""
    row_status = row.get("status") or "---"
    asset_name = row.get("asset") or row.get("asset_name") or "---"
    asset_code = row.get("asset_code") or "---"
    receiver = row.get("receiver") or row.get("user") or "---"

    detail_url = url_for("assign_detail", id=row_id) if row_id else "#"
    give_url = url_for("assign_give", id=row_id) if row_id else "#"
    unassign_url = url_for("assign_unassign", id=row_id) if row_id else "#"

    return {
        "id": row_id,
        "asset_code": asset_code,
        "asset_name": asset_name,
        "type": row_type or "---",
        "type_label": get_type_label(row_type),
        "status": row_status,
        "status_class": get_status_class(row_status),
        "receiver": receiver,
        "department": row.get("department") or "---",
        "location": row.get("location") or "---",
        "can_assign": can_assign_asset(row),
        "can_unassign": can_unassign_asset(row),
        "detail_url": detail_url,
        "give_url": give_url,
        "unassign_url": unassign_url,
    }


def build_assign_ajax_payload(
    assigns,
    counts,
    pagination,
    search_q,
    selected_dept,
    selected_cat,
    selected_loc,
    selected_status,
    scope,
):
    current_page = pagination.get("page", 1)
    total_pages = pagination.get("total_pages", 1)
    total_items = pagination.get("total_items", 0)

    return {
        "success": True,
        "items": [build_assign_row_payload(row) for row in assigns],
        "counts": counts,
        "pagination": {
            "page": current_page,
            "per_page": pagination.get("per_page", 10),
            "total_items": total_items,
            "total_pages": total_pages,
            "shown": len(assigns),
        },
        "filters": {
            "search": search_q,
            "department": selected_dept,
            "category": selected_cat,
            "location": selected_loc,
            "status": selected_status,
        },
        "scope": scope,
    }


def enrich_assigned_user_info(info):
    if not info:
        return info

    if info.get("employee_code") or info.get("user_id") or info.get("receiver_id"):
        return info

    receiver_name = (info.get("receiver") or info.get("user") or "").strip()

    if not receiver_name:
        return info

    data, error = api_request(
        "GET",
        "/api/users",
        params={
            "page": 1,
            "limit": 20,
            "keyword": receiver_name,
        },
    )

    if error or not data:
        return info

    users = data.get("data", [])

    if not users:
        return info

    receiver_name_lower = receiver_name.lower()
    matched_user = None

    for user in users:
        full_name = (user.get("full_name") or "").strip().lower()

        if full_name == receiver_name_lower:
            matched_user = user
            break

    if not matched_user:
        matched_user = users[0]

    info["employee_code"] = (
        info.get("employee_code") or matched_user.get("employee_code") or ""
    )

    info["user_id"] = (
        info.get("user_id")
        or matched_user.get("id")
        or matched_user.get("_id")
        or ""
    )

    info["receiver_id"] = info.get("receiver_id") or info.get("user_id") or ""

    return info


def register_assign_routes(app):
    @app.route("/assign")
    def assign_page():
        ajax = is_ajax_request()
        fast_table = is_fast_table_request()
        permission_redirect = require_assign_permission("view")

        if permission_redirect:
            if ajax:
                return jsonify(
                    {
                        "success": False,
                        "message": "Bạn không có quyền xem dữ liệu cấp phát.",
                    }
                ), 403

            return permission_redirect

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
                # NOTE: fast_table chỉ reload table nên bỏ tính counts để giảm delay.
                "include_counts": 0 if fast_table else 1,
            },
        )

        if error:
            if ajax:
                return jsonify(
                    {
                        "success": False,
                        "message": error,
                        "items": [],
                        "counts": {},
                        "pagination": {
                            "page": 1,
                            "per_page": per_page,
                            "total_items": 0,
                            "total_pages": 1,
                            "shown": 0,
                        },
                    }
                ), 500

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
                "scope": {},
            }

        assigns = data.get("items", [])
        pagination = data.get("pagination", {})
        counts = convert_counts_for_template(data.get("filter_counts", {}))
        scope = data.get("scope", {})

        if fast_table:
            # NOTE: Frontend chỉ lấy .assign-table-card nên không cần gọi /api/assets lấy inventory.
            categories = DEFAULT_CATEGORIES
            departments = DEFAULT_DEPARTMENTS
            locations = DEFAULT_LOCATIONS
            status_options = DEFAULT_STATUS_OPTIONS
        else:
            categories, departments, locations, status_options = build_filter_options(counts)

            inventory, asset_categories = get_asset_categories_from_inventory()

            if asset_categories:
                categories = asset_categories

        if ajax:
            return jsonify(
                build_assign_ajax_payload(
                    assigns=assigns,
                    counts=counts,
                    pagination=pagination,
                    search_q=search_q,
                    selected_dept=selected_dept,
                    selected_cat=selected_cat,
                    selected_loc=selected_loc,
                    selected_status=selected_status,
                    scope=scope,
                )
            )

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
            scope=scope,
            type_labels=TYPE_LABELS,
            **assign_permission_context(),
        )

    @app.route("/assign/users/search", methods=["GET"])
    def assign_search_users():
        if not is_logged_in():
            return jsonify(
                {
                    "message": "Bạn chưa đăng nhập.",
                    "items": [],
                }
            ), 401

        if not user_can("assign", "update") and not user_can("assign", "create"):
            return jsonify(
                {
                    "message": "Bạn không có quyền tìm người nhận tài sản.",
                    "items": [],
                }
            ), 403

        keyword = request.args.get("keyword", "", type=str).strip()
        users = get_active_users_from_api(keyword=keyword)

        return jsonify({"items": users}), 200

    @app.route("/assign/create", methods=["GET", "POST"])
    def assign_create():
        permission_redirect = require_assign_permission("create")

        if permission_redirect:
            return permission_redirect

        if request.method == "POST":
            flash("API tạo phiếu cấp phát chưa được bật.", "warning")
            return redirect(url_for("assign_page"))

        inventory, inventory_types = get_asset_categories_from_inventory()

        return render_template(
            "assign/assign_create.html",
            inventory=inventory,
            departments=DEFAULT_DEPARTMENTS,
            locations=DEFAULT_LOCATIONS,
            categories=inventory_types,
            inventory_types=inventory_types,
            suggested_code=generate_frontend_asset_code(),
            **assign_permission_context(),
        )

    @app.route("/assign/give/<string:id>", methods=["GET", "POST"])
    def assign_give(id):
        permission_redirect = require_assign_permission("update")

        if permission_redirect:
            return permission_redirect

        asset_ids = get_asset_ids_for_give(id)
        assets, errors = load_assign_assets(asset_ids)

        if errors or not assets:
            flash(
                errors[0] if errors else "Không tìm thấy tài sản cần cấp phát.",
                "danger",
            )
            return redirect(url_for("assign_page"))

        info = assets[0]
        allow_assign = all(can_assign_asset(item) for item in assets)
        is_bulk_assign = len(asset_ids) > 1

        if request.method == "POST":
            user_id = request.form.get("user_id", "").strip()

            if not allow_assign:
                return redirect(build_give_redirect_url(id, asset_ids))

            if not user_id:
                return redirect(build_give_redirect_url(id, asset_ids))

            success, result = assign_many_assets_to_user_api(asset_ids, user_id)

            if not success:
                flash(
                    result.get("message")
                    or (
                        f"Đã cấp phát {result.get('success_count', 0)} tài sản, "
                        f"còn {result.get('failed_count', 0)} tài sản thất bại."
                    ),
                    "danger",
                )
                return redirect(url_for("assign_page"))

            flash(
                f"Cấp phát thành công {len(asset_ids)} tài sản."
                if is_bulk_assign
                else "Cấp phát tài sản thành công.",
                "success",
            )
            return redirect(url_for("assign_page"))

        return render_template(
            "assign/assign_give.html",
            info=info,
            assets=assets,
            users=[],
            allow_assign=allow_assign,
            is_bulk_assign=is_bulk_assign,
            selected_asset_ids=",".join(asset_ids),
            **assign_permission_context(),
        )

    @app.route("/assign/detail/<string:id>")
    def assign_detail(id):
        permission_redirect = require_assign_permission("view")

        if permission_redirect:
            return permission_redirect

        info, error = api_request("GET", f"/api/assign/{id}")

        if error or not info:
            flash(error or "Không tìm thấy thông tin.", "danger")
            return redirect(url_for("assign_page"))

        info = enrich_assigned_user_info(info)

        specs = {
            "spec": info.get("spec")
            or info.get("notes")
            or "Không có dữ liệu cấu hình."
        }

        return render_template(
            "assign/assign_detail.html",
            info=info,
            specs=specs,
            **assign_permission_context(),
        )

    @app.route("/assign/unassign/<string:id>", methods=["POST"])
    def assign_unassign(id):
        permission_redirect = require_assign_permission("update")
        json_response = wants_json_response()

        if permission_redirect:
            if json_response:
                return jsonify(
                    {
                        "success": False,
                        "message": "Bạn không có quyền thu hồi tài sản.",
                    }
                ), 403

            return permission_redirect

        info, error = api_request("GET", f"/api/assign/{id}")

        if error or not info:
            message = error or "Không tìm thấy tài sản cần thu hồi."

            if json_response:
                return jsonify(
                    {
                        "success": False,
                        "message": message,
                    }
                ), 404

            flash(message, "danger")
            return redirect(url_for("assign_page"))

        if not can_unassign_asset(info):
            message = "Chỉ có tài sản đang sử dụng mới có thể thu hồi."

            if json_response:
                return jsonify(
                    {
                        "success": False,
                        "message": message,
                    }
                ), 400

            flash(message, "warning")
            return redirect(url_for("assign_page"))

        success, result = unassign_asset_from_user_api(id)

        if not success:
            message = result.get("message", "Thu hồi tài sản thất bại.")

            if json_response:
                return jsonify(
                    {
                        "success": False,
                        "message": message,
                    }
                ), 400

            flash(message, "danger")
            return redirect(url_for("assign_page"))

        message = "Thu hồi tài sản thành công."

        if json_response:
            return jsonify(
                {
                    "success": True,
                    "message": message,
                    "toast_type": "warning",
                    "item": result.get("item") if isinstance(result, dict) else None,
                }
            ), 200

        flash(message, "warning")
        return redirect(url_for("assign_page"))

    @app.route("/assign/edit/<string:id>", methods=["GET", "POST"])
    def assign_edit(id):
        permission_redirect = require_assign_permission("update")

        if permission_redirect:
            return permission_redirect

        assign, error = api_request("GET", f"/api/assign/{id}")

        if error or not assign:
            flash(error or "Bản ghi không tồn tại.", "danger")
            return redirect(url_for("assign_page"))

        if request.method == "POST":
            flash("API cập nhật phiếu cấp phát chưa được bật.", "warning")
            return redirect(url_for("assign_detail", id=id))

        inventory, inventory_types = get_asset_categories_from_inventory()

        return render_template(
            "assign/assign_edit.html",
            assign=assign,
            inventory=inventory,
            departments=DEFAULT_DEPARTMENTS,
            categories=inventory_types,
            locations=DEFAULT_LOCATIONS,
            status_options=DEFAULT_STATUS_OPTIONS,
            **assign_permission_context(),
        )

    @app.route("/assign/approve/<string:id>")
    def approve_request(id):
        permission_redirect = require_assign_permission("approve")

        if permission_redirect:
            return permission_redirect

        data, error = api_request("PATCH", f"/api/assign/{id}/approve")

        if error:
            flash(error, "danger")
        else:
            flash(f"Đã phê duyệt phiếu #{id}", "success")

        return redirect(url_for("assign_page"))

    @app.route("/assign/reject/<string:id>")
    def reject_request(id):
        permission_redirect = require_assign_permission("approve")

        if permission_redirect:
            return permission_redirect

        data, error = api_request("PATCH", f"/api/assign/{id}/reject")

        if error:
            flash(error, "danger")
        else:
            flash(f"Đã từ chối yêu cầu phiếu #{id}", "warning")

        return redirect(url_for("assign_page"))

    @app.route("/assign/delete/<string:id>")
    def delete_assign_route(id):
        permission_redirect = require_assign_permission("delete")

        if permission_redirect:
            return permission_redirect

        data, error = api_request("DELETE", f"/api/assign/{id}")

        if error:
            flash(error, "danger")
        else:
            flash(f"Đã xóa bản ghi #{id}", "warning")

        return redirect(url_for("assign_page"))