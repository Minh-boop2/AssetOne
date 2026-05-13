from flask import render_template, request, redirect, url_for, flash, jsonify

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
    assign_asset_to_user_api,
    unassign_asset_from_user_api,
)


def get_asset_categories_from_inventory():
    inventory = get_inventory_from_assets_api()

    categories = sorted(
        list({
            item.get("type") or item.get("category")
            for item in inventory
            if item.get("type") or item.get("category")
        })
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
def enrich_assigned_user_info(info):
    if not info:
        return info

    # Nếu đã có ID rồi thì không cần tìm lại
    if info.get("employee_code") or info.get("user_id") or info.get("receiver_id"):
        return info

    receiver_name = (
        info.get("receiver")
        or info.get("user")
        or ""
    ).strip()

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
        info.get("employee_code")
        or matched_user.get("employee_code")
        or ""
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
            },
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

        # Đồng bộ loại thiết bị với database tài sản hiện tại
        inventory, asset_categories = get_asset_categories_from_inventory()

        if asset_categories:
            categories = asset_categories

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

    # --- 2. API SEARCH USER CHO TRANG CẤP PHÁT ---
    @app.route("/assign/users/search", methods=["GET"])
    def assign_search_users():
        keyword = request.args.get("keyword", "", type=str).strip()

        users = get_active_users_from_api(keyword=keyword)

        return jsonify({
            "items": users
        }), 200

    # --- 3. TRANG TẠO MỚI ---
    @app.route("/assign/create", methods=["GET", "POST"])
    def assign_create():
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
        )

    # --- 4. TRANG CẤP PHÁT ---
    @app.route("/assign/give/<string:id>", methods=["GET", "POST"])
    def assign_give(id):
        info, error = api_request("GET", f"/api/assign/{id}")

        if error or not info:
            flash(error or "Không tìm thấy tài sản cần cấp phát.", "danger")
            return redirect(url_for("assign_page"))

        allow_assign = can_assign_asset(info)

        if request.method == "POST":
            user_id = request.form.get("user_id", "").strip()

            if not allow_assign:
                flash(
                    "Tài sản này không ở trạng thái Chưa dùng nên không thể cấp phát.",
                    "danger",
                )
                return redirect(url_for("assign_page"))

            if not user_id:
                flash("Vui lòng chọn người dùng nhận tài sản.", "warning")
                return redirect(url_for("assign_give", id=id))

            success, result = assign_asset_to_user_api(id, user_id)

            if not success:
                flash(result.get("message", "Cấp phát tài sản thất bại."), "danger")
                return redirect(url_for("assign_give", id=id))

            flash("Cấp phát tài sản thành công.", "success")

            # Quay về trang assign không filter
            return redirect(url_for("assign_page"))

        return render_template(
            "assign/assign_give.html",
            info=info,
            users=[],
            allow_assign=allow_assign,
        )

    # --- 5. TRANG CHI TIẾT ---
    @app.route("/assign/detail/<string:id>")
    def assign_detail(id):
        info, error = api_request("GET", f"/api/assign/{id}")

        if error or not info:
            flash(error or "Không tìm thấy thông tin.", "danger")
            return redirect(url_for("assign_page"))
        info = enrich_assigned_user_info(info)

        specs = {
            "spec": (
                info.get("spec")
                or info.get("notes")
                or "Không có dữ liệu cấu hình."
            )
        }

        return render_template(
            "assign/assign_detail.html",
            info=info,
            specs=specs,
        )

    # --- 6. THU HỒI TÀI SẢN ---
    @app.route("/assign/unassign/<string:id>", methods=["POST"])
    def assign_unassign(id):
        info, error = api_request("GET", f"/api/assign/{id}")

        if error or not info:
            flash(error or "Không tìm thấy tài sản cần thu hồi.", "danger")
            return redirect(url_for("assign_page"))

        if not can_unassign_asset(info):
            flash("Chỉ có tài sản đang sử dụng mới có thể thu hồi.", "warning")
            return redirect(url_for("assign_page"))

        success, result = unassign_asset_from_user_api(id)

        if not success:
            flash(result.get("message", "Thu hồi tài sản thất bại."), "danger")
            return redirect(url_for("assign_page"))

        flash("Thu hồi tài sản thành công.", "success")

        # Quay về trang assign không filter
        return redirect(url_for("assign_page"))

    # --- 7. TRANG CHỈNH SỬA ---
    @app.route("/assign/edit/<string:id>", methods=["GET", "POST"])
    def assign_edit(id):
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
        )

    # --- 8. ACTION PHÊ DUYỆT ---
    @app.route("/assign/approve/<string:id>")
    def approve_request(id):
        data, error = api_request("PATCH", f"/api/assign/{id}/approve")

        if error:
            flash(error, "danger")
        else:
            flash(f"Đã phê duyệt phiếu #{id}", "success")

        return redirect(url_for("assign_page"))

    # --- 9. ACTION TỪ CHỐI ---
    @app.route("/assign/reject/<string:id>")
    def reject_request(id):
        data, error = api_request("PATCH", f"/api/assign/{id}/reject")

        if error:
            flash(error, "danger")
        else:
            flash(f"Đã từ chối yêu cầu phiếu #{id}", "warning")

        return redirect(url_for("assign_page"))

    # --- 10. ACTION XÓA ---
    @app.route("/assign/delete/<string:id>")
    def delete_assign(id):
        data, error = api_request("DELETE", f"/api/assign/{id}")

        if error:
            flash(error, "danger")
        else:
            flash(f"Đã xóa bản ghi #{id}", "warning")

        return redirect(url_for("assign_page"))