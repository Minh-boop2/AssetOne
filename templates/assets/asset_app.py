from flask import render_template, request, redirect, url_for, jsonify, flash, session

from .asset_backend import (
    DEFAULT_FILTER_COUNTS,
    fetch_assets_from_backend,
    fetch_asset_detail_from_backend,
    fetch_asset_types_from_backend,
    create_asset_to_backend,
    update_asset_to_backend,
    delete_asset_from_backend,
)


def get_current_user():
    return session.get("user") or session.get("current_user") or {}


def is_logged_in():
    return bool(get_current_user())


def user_can(module_key, action):
    user = get_current_user()

    if user.get("is_admin") or user.get("role") == "ADMIN":
        return True

    can = user.get("can") or {}

    return can.get(module_key, {}).get(action) is True


def is_staff_user():
    user = get_current_user()
    return user.get("role") == "NHAN_VIEN"


def require_login():
    if not is_logged_in():
        return redirect(url_for("login_page"))

    return None


def require_asset_permission(action):
    login_redirect = require_login()

    if login_redirect:
        return login_redirect

    if not user_can("assets", action):
        flash("Bạn không có quyền thực hiện chức năng này.", "danger")
        return redirect(url_for("dashboard_overview"))

    return None


def asset_permission_context():
    user = get_current_user()

    return {
        "current_user": user,
        "can_view_asset": user_can("assets", "view"),
        "can_create_asset": user_can("assets", "create"),
        "can_update_asset": user_can("assets", "update"),
        "can_delete_asset": user_can("assets", "delete"),
        "is_staff_asset_scope": is_staff_user(),
    }


def normalize_asset_for_template(info):
    info = dict(info or {})

    info["id"] = str(info.get("id") or info.get("_id") or info.get("asset_code") or "")
    info["asset"] = info.get("asset") or info.get("asset_name") or ""
    info["asset_name"] = info.get("asset_name") or info.get("asset") or ""

    info["type"] = info.get("type") or info.get("category") or ""
    info["category"] = info.get("category") or info.get("type") or ""

    info["user"] = info.get("user") or info.get("receiver") or ""
    info["receiver"] = info.get("receiver") or info.get("user") or ""

    info["asset_code"] = info.get("asset_code") or ""
    info["status"] = info.get("status") or "available"
    info["department"] = info.get("department") or ""
    info["location"] = info.get("location") or ""
    info["warranty"] = info.get("warranty") or ""

    info["spec"] = info.get("spec") or info.get("notes") or ""
    info["notes"] = info.get("notes") or info.get("spec") or ""

    info["user_id"] = info.get("user_id") or ""
    info["employee_code"] = info.get("employee_code") or ""

    return info


def handle_api_auth_error(status_code, default_message=None):
    if status_code == 401:
        session.clear()
        flash("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.", "warning")
        return redirect(url_for("login_page"))

    if status_code == 403:
        flash(default_message or "Bạn không có quyền thực hiện chức năng này.", "danger")
        return redirect(url_for("dashboard_overview"))

    return None


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

        status_code = api_result.get("status_code")
        auth_redirect = handle_api_auth_error(
            status_code,
            api_result.get("message", "Bạn không có quyền xem tài sản."),
        )

        if auth_redirect:
            return auth_redirect

        assets = api_result.get("items", [])
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

            asset_type = form_data.get("type", "").strip()
            asset_name = form_data.get("asset_name", "").strip()
            spec = form_data.get("spec", "").strip()

            payload = {
                "asset_code": form_data.get("asset_code", "").strip(),
                "asset_name": asset_name,
                "asset": asset_name,
                "type": asset_type,
                "category": asset_type,
                "warranty": form_data.get("warranty", "").strip(),
                "spec": spec,
                "notes": spec,
                "status": "available",
                "user": "",
                "receiver": "",
                "user_id": "",
                "employee_code": "",
                "department": "",
                "location": "",
            }

            success, result = create_asset_to_backend(payload)

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

            asset_name = form_data.get("asset_name", "").strip()
            asset_type = form_data.get("type", "").strip()
            spec = form_data.get("spec", "").strip()

            payload = {
                "asset_code": form_data.get("asset_code", "").strip() or info.get("asset_code", ""),
                "asset_name": asset_name,
                "asset": asset_name,
                "type": asset_type,
                "category": asset_type,
                "warranty": form_data.get("warranty", "").strip(),
                "spec": spec,
                "notes": spec,
            }

            success, result = update_asset_to_backend(asset_id, payload)

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

            form_data = normalize_asset_for_template({
                **info,
                **form_data,
                "asset": asset_name,
                "asset_name": asset_name,
                "category": asset_type,
                "type": asset_type,
                "notes": spec,
                "spec": spec,
            })

            return render_template(
                "assets/assets_edit.html",
                asset_id=asset_id,
                form_data=form_data,
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