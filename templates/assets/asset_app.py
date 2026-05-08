from flask import render_template, request, redirect, url_for, jsonify, flash

from .asset_backend import (
    DEFAULT_FILTER_COUNTS,
    fetch_assets_from_backend,
    fetch_asset_detail_from_backend,
    fetch_asset_types_from_backend,
    create_asset_to_backend,
    delete_asset_from_backend,
)


def register_assets_routes(app):
    @app.route("/assets")
    def assets_page():
        search_q = request.args.get("search", "").strip()
        sel_type = request.args.get("type", "Tất cả")
        sel_dept = request.args.get("department", "Tất cả")
        sel_status = request.args.get("status", "Tất cả")
        page = request.args.get("page", 1, type=int)
        per_page = 10

        api_result = fetch_assets_from_backend(
            page=page,
            per_page=per_page,
            search=search_q,
            asset_type=sel_type,
            department=sel_dept,
            status=sel_status,
        )

        assets = api_result.get("items", [])
        pagination = api_result.get("pagination", {})
        filter_counts = api_result.get("filter_counts", DEFAULT_FILTER_COUNTS)

        return render_template(
            "assets/assets.html",
            assets=assets,
            current_page=pagination.get("page", 1),
            total_pages=pagination.get("total_pages", 1),
            search_q=search_q,
            total_count=pagination.get("total_items", 0),
            selected_type=sel_type,
            selected_dept=sel_dept,
            selected_status=sel_status,
            filter_counts=filter_counts,
        )

    @app.route("/assets/create", methods=["GET", "POST"])
    def asset_create():
        asset_types = fetch_asset_types_from_backend()

        if request.method == "POST":
            form_data = request.form.to_dict()

            asset_type = form_data.get("type", "").strip()

            payload = {
                "asset_code": form_data.get("asset_code", "").strip(),
                "asset_name": form_data.get("asset_name", "").strip(),

                # Cho phép nhập custom loại thiết bị
                "type": asset_type,
                "category": asset_type,

                "warranty": form_data.get("warranty", "").strip(),
                "spec": form_data.get("spec", "").strip(),
                "notes": form_data.get("spec", "").strip(),

                # Mặc định khi tạo tài sản mới
                # Chưa sử dụng, chưa có người nhận, chưa có phòng ban, chưa có vị trí
                "status": "available",
                "user": "",
                "receiver": "",
                "department": "",
                "location": "",
            }

            success, result = create_asset_to_backend(payload)

            if success:
                flash("Thêm thiết bị thành công.", "success")
                return redirect(url_for("assets_page"))

            error_message = result.get("message", "Tạo tài sản thất bại")
            flash(error_message, "danger")

            return render_template(
                "assets/asset_create.html",
                error_message=error_message,
                form_data=form_data,
                asset_types=asset_types,
            )

        return render_template(
            "assets/asset_create.html",
            error_message=None,
            form_data={},
            asset_types=asset_types,
        )

    @app.route("/assets/detail/<string:asset_id>")
    def asset_detail_view(asset_id):
        info = fetch_asset_detail_from_backend(asset_id)

        if not info:
            return redirect(url_for("assets_page"))

        info["asset"] = info.get("asset") or info.get("asset_name") or ""
        info["asset_name"] = info.get("asset_name") or info.get("asset") or ""

        specs = {
            "spec": info.get("spec") or "Thông số kỹ thuật đang được cập nhật",
            "warranty": info.get("warranty") or "N/A",
        }

        return render_template(
            "assets/asset_detail.html",
            info=info,
            specs=specs,
        )

    @app.route("/assets/delete/<string:asset_id>", methods=["POST"])
    def asset_delete_view(asset_id):
        success, result = delete_asset_from_backend(asset_id)

        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if is_ajax:
            return jsonify(result), 200 if success else 400

        return redirect(url_for("assets_page"))