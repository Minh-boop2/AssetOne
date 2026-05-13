from flask import render_template, request, redirect, url_for, flash

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


def register_manage_routes(app):

    @app.route("/manage")
    def manage():
        page_data = get_manage_page_data(request.args)

        if page_data.get("users_error"):
            flash(page_data["users_error"], "danger")

        if page_data.get("stats_error"):
            flash(page_data["stats_error"], "danger")

        page_data.pop("users_error", None)
        page_data.pop("stats_error", None)

        return render_template(
            "manage/manage_overview.html",
            **page_data
        )

    @app.route("/manage/create", methods=["GET", "POST"])
    def manage_create():
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
            **page_data
        )

    @app.route("/manage/detail/<string:id>")
    def user_detail(id):
        user, error = get_user_detail_page_data(id)

        if error:
            flash(error, "warning")
            return redirect(url_for("manage"))

        return render_template(
            "manage/manage_detail.html",
            user=user
        )

    @app.route("/manage/edit/<string:id>", methods=["GET", "POST"])
    def user_edit(id):
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
            **page_data
        )

    @app.route("/manage/toggle-status/<string:id>")
    def user_toggle_status(id):
        success, message, category = toggle_user_status(id)

        flash(message, category)

        if not success:
            return redirect(url_for("manage"))

        return redirect(url_for("user_detail", id=id))

    @app.route("/manage/delete/<string:id>", methods=["GET", "POST"])
    def user_delete(id):
        success, message, category = delete_user(id)

        if not success:
            flash(message, category)
            return redirect(url_for("manage"))

        flash("Xóa nhân sự thành công", category or "success")
        return redirect(url_for("manage"))