from flask import render_template, request, redirect, url_for, flash

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

        # Đồng bộ loại thiết bị của trang cấp phát với database tài sản hiện tại
        # Không lấy loại từ lịch sử cấp phát nữa
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

    # --- 2. TRANG TẠO MỚI ---
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