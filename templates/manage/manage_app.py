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
                flash(message, "danger")
                return redirect(url_for("manage_create"))

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
            flash(error, "warning")
            return redirect(url_for("manage"))

        return render_template(
            "manage/manage_detail.html",
            user=user,
            **manage_permission_context(),
        )

    @app.route("/manage/edit/<string:id>", methods=["GET", "POST"])
    def user_edit(id):
        permission_redirect = require_user_permission("update")

        if permission_redirect:
            return permission_redirect

        if request.method == "POST":
            success, message, _ = update_user_from_form(id, request.form)

            if not success:
                flash(message, "danger")
                return redirect(url_for("user_edit", id=id))

            flash("Cập nhật nhân sự thành công", "success")
            return redirect(url_for("user_detail", id=id))

        page_data, error = get_edit_page_data(id)

        if error:
            flash(error, "warning")
            return redirect(url_for("manage"))

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
            return permission_redirect

        success, message, category = toggle_user_status(id)

        flash(message, category)

        return redirect_back_to_manage()

    @app.route("/manage/delete/<string:id>", methods=["GET", "POST"])
    def user_delete(id):
        permission_redirect = require_user_permission("delete")

        if permission_redirect:
            return permission_redirect

        success, message, category = delete_user(id)

        if not success:
            flash(message, category)
            return redirect(url_for("manage"))

        flash(message or "Cập nhật trạng thái nhân sự thành công", category or "success")
        return redirect(url_for("manage"))