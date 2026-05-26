from flask import render_template, request, redirect, url_for, jsonify, flash

from .asset_backend import (
    DEFAULT_FILTER_COUNTS,
    asset_permission_context,
    create_asset_from_form,
    delete_asset_from_backend,
    fetch_asset_detail_from_backend,
    fetch_asset_types_from_backend,
    fetch_assets_from_backend,
    handle_api_auth_error,
    handle_asset_status_action,
    is_logged_in,
    is_staff_user,
    merge_asset_form_data,
    normalize_asset_for_template,
    require_asset_permission,
    user_can,
    update_asset_from_form,
)


def wants_json_response():
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.is_json
        or "application/json" in request.headers.get("Accept", "")
    )


def redirect_back_to_assets():
    return redirect(request.referrer or url_for("assets_page"))


def get_status_action_from_request():
    json_data = request.get_json(silent=True)
    data = json_data if isinstance(json_data, dict) else request.form

    return (data.get("action") or "").strip()


def register_assets_routes(app):
    @app.route("/assets")
    def assets_page():
        permission_redirect = require_asset_permission("view")

        if permission_redirect:
            return permission_redirect

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

        auth_redirect = handle_api_auth_error(
            api_result.get("status_code"),
            api_result.get("message", "Bạn không có quyền xem tài sản."),
        )

        if auth_redirect:
            return auth_redirect

        assets = [
            normalize_asset_for_template(asset)
            for asset in api_result.get("items", [])
        ]

        pagination = api_result.get("pagination", {})
        filter_counts = api_result.get("filter_counts", DEFAULT_FILTER_COUNTS)
        scope = api_result.get("scope", {})

        page_title = "Tài sản"
        page_subtitle = "Danh sách tài sản trong hệ thống"

        if is_staff_user():
            page_title = "Tài sản của tôi"
            page_subtitle = "Danh sách tài sản đang được cấp phát cho bạn"

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
            scope=scope,
            page_title=page_title,
            page_subtitle=page_subtitle,
            **asset_permission_context(),
        )

    @app.route("/assets/create", methods=["GET", "POST"])
    def asset_create():
        permission_redirect = require_asset_permission("create")

        if permission_redirect:
            return permission_redirect

        asset_types = fetch_asset_types_from_backend()

        if request.method == "POST":
            form_data = request.form.to_dict()
            success, result = create_asset_from_form(form_data)

            auth_redirect = handle_api_auth_error(
                result.get("status_code"),
                result.get("message"),
            )

            if auth_redirect:
                return auth_redirect

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
                **asset_permission_context(),
            )

        return render_template(
            "assets/asset_create.html",
            error_message=None,
            form_data={},
            asset_types=asset_types,
            **asset_permission_context(),
        )

    @app.route("/assets/edit/<string:asset_id>", methods=["GET", "POST"])
    def asset_edit(asset_id):
        permission_redirect = require_asset_permission("update")

        if permission_redirect:
            return permission_redirect

        asset_types = fetch_asset_types_from_backend()
        info = fetch_asset_detail_from_backend(asset_id)

        if not info:
            flash("Không tìm thấy tài sản hoặc bạn không có quyền sửa tài sản này.", "warning")
            return redirect(url_for("assets_page"))

        info = normalize_asset_for_template(info)

        if request.method == "POST":
            form_data = request.form.to_dict()
            success, result = update_asset_from_form(
                asset_id=asset_id,
                form_data=form_data,
                current_asset=info,
            )

            auth_redirect = handle_api_auth_error(
                result.get("status_code"),
                result.get("message"),
            )

            if auth_redirect:
                return auth_redirect

            if success:
                flash("Cập nhật tài sản thành công.", "success")
                return redirect(url_for("asset_detail_view", asset_id=asset_id))

            error_message = result.get("message", "Cập nhật tài sản thất bại")
            flash(error_message, "danger")

            return render_template(
                "assets/assets_edit.html",
                asset_id=asset_id,
                form_data=merge_asset_form_data(info, form_data),
                asset_types=asset_types,
                error_message=error_message,
                **asset_permission_context(),
            )

        return render_template(
            "assets/assets_edit.html",
            asset_id=asset_id,
            form_data=info,
            asset_types=asset_types,
            error_message=None,
            **asset_permission_context(),
        )

    @app.route("/assets/detail/<string:asset_id>")
    def asset_detail_view(asset_id):
        permission_redirect = require_asset_permission("view")

        if permission_redirect:
            return permission_redirect

        info = fetch_asset_detail_from_backend(asset_id)

        if not info:
            flash("Không tìm thấy tài sản hoặc bạn không có quyền xem tài sản này.", "warning")
            return redirect(url_for("assets_page"))

        info = normalize_asset_for_template(info)

        specs = {
            "spec": info.get("spec") or "Thông số kỹ thuật đang được cập nhật",
            "warranty": info.get("warranty") or "N/A",
        }

        return render_template(
            "assets/asset_detail.html",
            info=info,
            specs=specs,
            **asset_permission_context(),
        )

    @app.route("/assets/status-action/<string:asset_id>", methods=["POST"])
    def asset_status_action_view(asset_id):
        is_ajax = wants_json_response()

        if not is_logged_in():
            result = {
                "message": "Bạn chưa đăng nhập.",
            }

            if is_ajax:
                return jsonify(result), 401

            flash(result["message"], "warning")
            return redirect(url_for("login_page"))

        if not user_can("assets", "update"):
            result = {
                "message": "Bạn không có quyền cập nhật trạng thái tài sản.",
            }

            if is_ajax:
                return jsonify(result), 403

            flash(result["message"], "danger")
            return redirect(url_for("assets_page"))

        action = get_status_action_from_request()

        success, result = handle_asset_status_action(
            asset_id=asset_id,
            action=action,
        )

        auth_redirect = handle_api_auth_error(
            result.get("status_code"),
            result.get("message"),
        )

        if auth_redirect:
            return auth_redirect

        if is_ajax:
            return jsonify(result), 200 if success else result.get("status_code", 400)

        if success:
            flash(result.get("message", "Cập nhật trạng thái tài sản thành công."), "success")
        else:
            flash(result.get("message", "Cập nhật trạng thái tài sản thất bại."), "danger")

        return redirect_back_to_assets()

    @app.route("/assets/delete/<string:asset_id>", methods=["POST"])
    def asset_delete_view(asset_id):
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if not is_logged_in():
            result = {
                "message": "Bạn chưa đăng nhập."
            }

            if is_ajax:
                return jsonify(result), 401

            flash(result["message"], "warning")
            return redirect(url_for("login_page"))

        if not user_can("assets", "delete"):
            result = {
                "message": "Bạn không có quyền xóa tài sản."
            }

            if is_ajax:
                return jsonify(result), 403

            flash(result["message"], "danger")
            return redirect(url_for("assets_page"))

        success, result = delete_asset_from_backend(asset_id)

        if is_ajax:
            return jsonify(result), 200 if success else result.get("status_code", 400)

        auth_redirect = handle_api_auth_error(
            result.get("status_code"),
            result.get("message"),
        )

        if auth_redirect:
            return auth_redirect

        if success:
            flash("Xóa tài sản thành công.", "success")
        else:
            flash(result.get("message", "Xóa tài sản thất bại."), "danger")

        return redirect(url_for("assets_page"))