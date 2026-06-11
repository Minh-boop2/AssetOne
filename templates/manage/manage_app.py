from flask import render_template, request, redirect, url_for, flash, session, jsonify

from .manage_backend import (
    get_manage_page_data,
    get_create_page_data,
    create_user_from_form,
    get_user_detail_page_data,
    get_edit_page_data,
    update_user_from_form,
    toggle_user_status,
    delete_user,
)


DENIED_ACTION_MESSAGE = "Bạn không có quyền thực hiện hành động này."


def get_current_user():
    return session.get("user") or session.get("current_user") or {}


def is_logged_in():
    return bool(get_current_user())


def normalize_role_code(role):
    role = str(role or "").strip().upper()

    mapping = {
        "ADMIN": "ADMIN",
        "QUẢN LÝ": "QUAN_LY",
        "QUAN_LY": "QUAN_LY",
        "MANAGER": "QUAN_LY",
        "NHÂN VIÊN": "NHAN_VIEN",
        "NHAN_VIEN": "NHAN_VIEN",
        "USER": "NHAN_VIEN",
        "STAFF": "NHAN_VIEN",
    }

    return mapping.get(role, role)


def user_can(module_key, action):
    user = get_current_user()
    role = normalize_role_code(user.get("role"))

    if user.get("is_admin") or role == "ADMIN":
        return True

    # NOTE: QUAN_LY được vào trang quản lý user và cập nhật user,
    # còn được sửa ai thì kiểm tra tiếp bằng can_manage_target_user().
    if role == "QUAN_LY" and module_key == "users" and action in ["view", "update"]:
        return True

    can = user.get("can") or {}
    return can.get(module_key, {}).get(action) is True


def current_user_identity_values():
    user = get_current_user()

    values = [
        session.get("current_user_id"),
        user.get("_id"),
        user.get("id"),
        user.get("user_id"),
        user.get("employee_code"),
        user.get("email"),
    ]

    return {
        str(value).strip().lower()
        for value in values
        if str(value or "").strip()
    }


def target_user_identity_values(user):
    user = user or {}

    values = [
        user.get("db_id"),
        user.get("_id"),
        user.get("id"),
        user.get("user_id"),
        user.get("employee_code"),
        user.get("email"),
    ]

    return {
        str(value).strip().lower()
        for value in values
        if str(value or "").strip()
    }


def is_current_user_target(target_user):
    # NOTE: Cho QUAN_LY thao tác với chính tài khoản quản lý của mình.
    return bool(current_user_identity_values() & target_user_identity_values(target_user))


def can_manage_target_user(target_user):
    # NOTE: ADMIN thao tác tất cả.
    # QUAN_LY chỉ thao tác NHAN_VIEN hoặc chính tài khoản QUAN_LY của mình.
    if not target_user or not user_can("users", "update"):
        return False

    current_role = normalize_role_code(get_current_user().get("role"))
    target_role = normalize_role_code(
        target_user.get("role_code")
        or target_user.get("role")
    )

    if current_role == "ADMIN":
        return True

    if current_role == "QUAN_LY":
        if target_role == "NHAN_VIEN":
            return True

        if target_role == "QUAN_LY" and is_current_user_target(target_user):
            return True

    return False


def mark_manage_permissions_for_rows(page_data):
    # NOTE: Gắn quyền cho từng dòng để template không tự suy luận sai.
    for row in page_data.get("employees") or []:
        row["can_manage_action"] = can_manage_target_user(row)

    return page_data


def require_login():
    if not is_logged_in():
        return redirect(url_for("login_page"))

    return None


def require_user_permission(action):
    login_redirect = require_login()

    if login_redirect:
        return login_redirect

    if not user_can("users", action):
        flash("Bạn không có quyền thực hiện chức năng này.", "danger")
        return redirect(url_for("dashboard_overview"))

    return None


def manage_permission_context():
    return {
        "current_user": get_current_user(),
        "can_view_user": user_can("users", "view"),
        "can_create_user": user_can("users", "create"),
        "can_update_user": user_can("users", "update"),
        "can_delete_user": user_can("users", "delete"),
    }


def is_ajax_request():
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.accept_mimetypes.best == "application/json"
    )


def clean_manage_page_data(page_data):
    page_data.pop("users_error", None)
    page_data.pop("stats_error", None)
    return page_data


def redirect_back_to_manage():
    return redirect(request.referrer or url_for("manage"))


def normalize_toast_type(category, message=""):
    clean_category = str(category or "").lower()
    clean_message = str(message or "").lower()

    if (
        clean_category in ["danger", "error", "delete", "inactive", "stop"]
        or "ngưng hoạt động" in clean_message
        or "ngừng hoạt động" in clean_message
        or "đã ngưng" in clean_message
        or "xóa" in clean_message
    ):
        return "error"

    if (
        clean_category == "warning"
        or "cập nhật nhân sự" in clean_message
        or "lưu thay đổi" in clean_message
    ):
        return "warning"

    return "success"


def ajax_response(success=True, message="", category="success", **extra):
    payload = {
        "ok": success,
        "success": success,
        "message": message,
        "category": category,
        "toast_type": normalize_toast_type(category, message),
    }

    payload.update(extra)
    return jsonify(payload)


def denied_manage_action_response():
    # NOTE: Request AJAX trả JSON 403 để frontend hiện Sonner lỗi.
    if is_ajax_request():
        return ajax_response(
            False,
            DENIED_ACTION_MESSAGE,
            "danger",
            toast_type="error"
        ), 403

    flash(DENIED_ACTION_MESSAGE, "danger")
    return redirect_back_to_manage()


def not_found_user_response(message="Không tìm thấy nhân sự"):
    if is_ajax_request():
        return ajax_response(False, message, "warning"), 404

    flash(message, "warning")
    return redirect(url_for("manage"))


def register_manage_routes(app):

    @app.route("/manage")
    def manage():
        permission_redirect = require_user_permission("view")

        if permission_redirect:
            return permission_redirect

        page_data = get_manage_page_data(request.args)

        if page_data.get("users_error"):
            flash(page_data["users_error"], "danger")

        if page_data.get("stats_error"):
            flash(page_data["stats_error"], "danger")

        page_data = clean_manage_page_data(page_data)
        page_data = mark_manage_permissions_for_rows(page_data)

        context = {
            **page_data,
            **manage_permission_context(),
        }

        if is_ajax_request():
            return jsonify({
                "ok": True,
                "table_html": render_template(
                    "manage/manage_table.html",
                    **context
                ),
            })

        return render_template(
            "manage/manage_overview.html",
            **context
        )

    @app.route("/manage/create", methods=["GET", "POST"])
    def manage_create():
        permission_redirect = require_user_permission("create")

        if permission_redirect:
            return permission_redirect

        if request.method == "POST":
            success, message, _ = create_user_from_form(request.form)

            if not success:
                if is_ajax_request():
                    return ajax_response(False, message, "danger"), 400

                flash(message, "danger")
                return redirect(url_for("manage_create"))

            if is_ajax_request():
                return ajax_response(
                    True,
                    "Thêm nhân sự thành công",
                    "success",
                    redirect_url=url_for("manage")
                )

            flash("Thêm nhân sự thành công", "success")
            return redirect(url_for("manage"))

        page_data = get_create_page_data()

        if page_data.get("stats_error"):
            flash(page_data["stats_error"], "danger")

        page_data.pop("stats_error", None)

        return render_template(
            "manage/manage_create.html",
            **page_data,
            **manage_permission_context(),
        )

    @app.route("/manage/detail/<string:id>")
    def user_detail(id):
        permission_redirect = require_user_permission("view")

        if permission_redirect:
            return permission_redirect

        user, error = get_user_detail_page_data(id)

        if error:
            return not_found_user_response(error)

        return render_template(
            "manage/manage_detail.html",
            user=user,
            can_manage_detail_target=can_manage_target_user(user),
            **manage_permission_context(),
        )

    @app.route("/manage/edit/<string:id>", methods=["GET", "POST"])
    def user_edit(id):
        permission_redirect = require_user_permission("update")

        if permission_redirect:
            return permission_redirect

        target_user, error = get_user_detail_page_data(id)

        if error:
            return not_found_user_response(error)

        if not can_manage_target_user(target_user):
            return denied_manage_action_response()

        if request.method == "POST":
            success, message, _ = update_user_from_form(id, request.form)

            if not success:
                if is_ajax_request():
                    return ajax_response(False, message, "danger"), 400

                flash(message, "danger")
                return redirect(url_for("user_edit", id=id))

            if is_ajax_request():
                return ajax_response(
                    True,
                    "Cập nhật nhân sự thành công",
                    "warning",
                    redirect_url=url_for("manage")
                )

            flash("Cập nhật nhân sự thành công", "success")
            return redirect(url_for("user_detail", id=id))

        page_data, error = get_edit_page_data(id)

        if error:
            return not_found_user_response(error)

        if page_data.get("stats_error"):
            flash(page_data["stats_error"], "danger")

        page_data.pop("stats_error", None)

        return render_template(
            "manage/manage_edit.html",
            **page_data,
            **manage_permission_context(),
        )

    @app.route("/manage/toggle-status/<string:id>")
    def user_toggle_status(id):
        permission_redirect = require_user_permission("update")

        if permission_redirect:
            if is_ajax_request():
                return ajax_response(
                    False,
                    DENIED_ACTION_MESSAGE,
                    "danger",
                    toast_type="error"
                ), 403

            return permission_redirect

        target_user, error = get_user_detail_page_data(id)

        if error:
            return not_found_user_response(error)

        if not can_manage_target_user(target_user):
            return denied_manage_action_response()

        success, message, category = toggle_user_status(id)
        toast_type = normalize_toast_type(category, message)

        if is_ajax_request():
            status_code = 200 if success else 400

            return ajax_response(
                success,
                message,
                category,
                toast_type=toast_type
            ), status_code

        flash(message, category)
        return redirect_back_to_manage()

    @app.route("/manage/delete/<string:id>", methods=["GET", "POST"])
    def user_delete(id):
        permission_redirect = require_user_permission("delete")

        if permission_redirect:
            return permission_redirect

        success, message, category = delete_user(id)

        if not success:
            if is_ajax_request():
                return ajax_response(False, message, category), 400

            flash(message, category)
            return redirect(url_for("manage"))

        final_message = message or "Cập nhật trạng thái nhân sự thành công"
        final_category = category or "success"

        if is_ajax_request():
            return ajax_response(
                True,
                final_message,
                final_category,
                redirect_url=url_for("manage")
            )

        flash(final_message, final_category)
        return redirect(url_for("manage"))