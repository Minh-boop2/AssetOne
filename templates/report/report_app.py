from flask import (
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from templates.report.report_backend import (
    get_report_page_data,
    get_create_page_data,
    create_report_from_form,
    get_report_detail_page_data,
    delete_report,
    approve_report,
    cancel_report,
    delete_file,
    search_report_assets,
    api_get_report_file_content,
)


def _json_or_form_data():
    if request.is_json:
        return request.get_json(silent=True) or {}

    return request.form.to_dict(flat=True)


def _is_ajax_request():
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.accept_mimetypes.best == "application/json"
        or request.is_json
    )


def _get_next_url(default_endpoint="report_page", **kwargs):
    next_url = (
        request.form.get("next")
        or request.args.get("next")
        or request.headers.get("Referer")
        or ""
    )

    if next_url:
        return next_url

    return url_for(default_endpoint, **kwargs)


def register_report_routes(app):

    @app.route("/report")
    def report_page():
        page_data = get_report_page_data(request.args)

        return render_template(
            "report/report.html",
            **page_data,
        )

    @app.route("/report/assets/search")
    def search_report_assets_route():
        keyword = (
            request.args.get("keyword", "")
            or request.args.get("q", "")
            or ""
        )

        return jsonify(search_report_assets(keyword))

    @app.route("/report/files/<path:filename>")
    def report_file_proxy(filename):
        download = request.args.get("download") == "1"

        content, status_code, headers = api_get_report_file_content(
            filename=filename,
            download=download,
        )

        return Response(
            content,
            status=status_code,
            headers=headers,
        )

    @app.route("/report/create", methods=["GET", "POST"])
    @app.route("/report/new", methods=["GET", "POST"])
    def new_report_page():
        if request.method == "POST":
            uploaded_files = []

            for field_name in request.files:
                uploaded_files.extend(request.files.getlist(field_name))

            success, message, data, status_code = create_report_from_form(
                request.form,
                uploaded_files,
            )

            if _is_ajax_request():
                return jsonify({
                    "success": success,
                    "message": message,
                    "data": data,
                }), status_code

            if not success:
                flash(message, "danger")
                return redirect(url_for("new_report_page"))

            flash(message, "success")
            return redirect(url_for("report_page"))

        page_data = get_create_page_data()

        return render_template(
            "report/report_create.html",
            **page_data,
        )

    @app.route("/report/detail/<path:row_index>")
    def report_detail_page(row_index):
        report, error, status_code = get_report_detail_page_data(row_index)

        if error:
            if _is_ajax_request():
                return jsonify({
                    "success": False,
                    "message": error,
                }), status_code

            flash(error, "warning")
            return redirect(url_for("report_page"))

        return render_template(
            "report/report_detail.html",
            report=report,
        )

    @app.route("/report/delete/<path:row_index>", methods=["GET", "POST", "DELETE"])
    def delete_report_log(row_index):
        success, message, category, status_code = delete_report(row_index)

        if _is_ajax_request():
            return jsonify({
                "success": success,
                "message": message,
                "category": category,
            }), status_code

        flash(message, category or "success")
        return redirect(_get_next_url())

    @app.route("/report/approve/<path:row_index>", methods=["POST", "PATCH"])
    def approve_report_log(row_index):
        data = _json_or_form_data()

        success, message, payload, status_code = approve_report(
            row_index,
            data,
        )

        if _is_ajax_request():
            return jsonify({
                "success": success,
                "message": message,
                "data": payload.get("data") if isinstance(payload, dict) else payload,
                "asset_action_result": payload.get("asset_action_result") if isinstance(payload, dict) else None,
            }), status_code

        flash(message, "success" if success else "danger")
        return redirect(_get_next_url("report_detail_page", row_index=row_index))

    @app.route("/report/cancel/<path:row_index>", methods=["POST", "PATCH"])
    def cancel_report_log(row_index):
        data = _json_or_form_data()

        success, message, payload, status_code = cancel_report(
            row_index,
            data,
        )

        if _is_ajax_request():
            return jsonify({
                "success": success,
                "message": message,
                "data": payload.get("data") if isinstance(payload, dict) else payload,
            }), status_code

        flash(message, "success" if success else "danger")
        return redirect(_get_next_url("report_detail_page", row_index=row_index))

    @app.route("/report/file/delete/<path:row_index>/<file_id>", methods=["POST", "DELETE"])
    def delete_report_file_log(row_index, file_id):
        success, message, payload, status_code = delete_file(row_index, file_id)

        if _is_ajax_request():
            return jsonify({
                "success": success,
                "message": message,
                "data": payload.get("data") if isinstance(payload, dict) else payload,
            }), status_code

        flash(message, "success" if success else "danger")
        return redirect(_get_next_url("report_detail_page", row_index=row_index))