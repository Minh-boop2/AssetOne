from flask import (
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from time import time
from werkzeug.datastructures import MultiDict

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


# =========================
# AJAX COUNT CACHE
# =========================

_REPORT_FILTER_COUNT_CACHE = {}
_REPORT_FILTER_COUNT_TTL = 45


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


def _safe_int(value, default=1):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _copy_report_args(args):
    copied = MultiDict()

    for key, value in args.items(multi=True):
        if key in {"_ajax", "_ts"}:
            continue

        copied.add(key, value)

    return copied


def _args_with_page(args, page):
    copied = _copy_report_args(args)
    copied["page"] = str(page)
    return copied


def _count_cache_key(args):
    clean_args = _copy_report_args(args)
    clean_args.pop("page", None)

    parts = []

    for key in sorted(clean_args.keys()):
        values = clean_args.getlist(key)

        for value in values:
            parts.append((key, str(value)))

    return tuple(parts)


def _get_cached_counts(args):
    cache_key = _count_cache_key(args)
    cached = _REPORT_FILTER_COUNT_CACHE.get(cache_key)

    if not cached:
        return None

    created_at = cached.get("created_at", 0)

    if time() - created_at > _REPORT_FILTER_COUNT_TTL:
        _REPORT_FILTER_COUNT_CACHE.pop(cache_key, None)
        return None

    return cached.get("counts")


def _set_cached_counts(args, counts):
    cache_key = _count_cache_key(args)

    _REPORT_FILTER_COUNT_CACHE[cache_key] = {
        "created_at": time(),
        "counts": counts or {},
    }

    if len(_REPORT_FILTER_COUNT_CACHE) > 80:
        oldest_key = min(
            _REPORT_FILTER_COUNT_CACHE,
            key=lambda key: _REPORT_FILTER_COUNT_CACHE[key].get("created_at", 0),
        )
        _REPORT_FILTER_COUNT_CACHE.pop(oldest_key, None)


def _row_value(row, key, fallback="Chưa xác định"):
    value = None

    if isinstance(row, dict):
        value = row.get(key)
    elif hasattr(row, "get"):
        try:
            value = row.get(key)
        except Exception:
            value = None

    if value is None:
        value = getattr(row, key, None)

    if value is None or str(value).strip() == "":
        return fallback

    return str(value).strip()


def _build_count_map(rows, key, fallback="Chưa xác định"):
    counts = {}

    for row in rows:
        value = _row_value(row, key, fallback)
        counts[value] = counts.get(value, 0) + 1

    return counts


def _build_filter_counts_from_rows(rows):
    safe_rows = rows or []

    return {
        "total": len(safe_rows),
        "type": _build_count_map(
            safe_rows,
            "display_report_type",
            "Khác",
        ),
        "department": _build_count_map(
            safe_rows,
            "display_department",
            "Chưa xác định",
        ),
        "location": _build_count_map(
            safe_rows,
            "display_location",
            "Chưa xác định",
        ),
        "status": _build_count_map(
            safe_rows,
            "display_report_status",
            "Chờ xử lý",
        ),
    }


def _quick_counts_from_page_data(page_data):
    total_records = _safe_int(
        page_data.get("total_records"),
        len(page_data.get("reports", []) or []),
    )

    return {
        "total": total_records,
        "type": page_data.get("type_counts") or {},
        "department": page_data.get("department_counts") or {},
        "location": page_data.get("location_counts") or {},
        "status": page_data.get("status_counts") or {},
    }


def _find_full_rows_in_page_data(page_data):
    candidate_keys = [
        "all_filtered_reports",
        "filtered_reports",
        "all_reports",
        "reports_all",
        "report_logs",
        "all_report_logs",
        "report_items",
        "all_items",
    ]

    for key in candidate_keys:
        rows = page_data.get(key)

        if isinstance(rows, list) and rows:
            return rows

    return None


def _collect_all_report_rows(first_page_data, args):
    full_rows = _find_full_rows_in_page_data(first_page_data)

    if full_rows is not None:
        return full_rows

    current_page = _safe_int(
        first_page_data.get("current_page"),
        _safe_int(args.get("page"), 1),
    )

    total_pages = _safe_int(first_page_data.get("total_pages"), 1)

    all_rows = []
    seen_keys = set()

    def add_rows(rows):
        for row in rows or []:
            row_key = (
                _row_value(row, "_row_index", ""),
                _row_value(row, "display_report_code", ""),
                _row_value(row, "display_report_name", ""),
                _row_value(row, "display_time", ""),
            )

            if row_key in seen_keys:
                continue

            seen_keys.add(row_key)
            all_rows.append(row)

    for page in range(1, total_pages + 1):
        if page == current_page:
            add_rows(first_page_data.get("reports", []))
            continue

        try:
            page_args = _args_with_page(args, page)
            page_data = get_report_page_data(page_args)
            add_rows(page_data.get("reports", []))
        except Exception:
            continue

    if not all_rows:
        add_rows(first_page_data.get("reports", []))

    return all_rows


def _get_exact_filter_counts(page_data, args):
    cached_counts = _get_cached_counts(args)

    if cached_counts is not None:
        return cached_counts

    all_filtered_rows = _collect_all_report_rows(page_data, args)
    counts = _build_filter_counts_from_rows(all_filtered_rows)

    _set_cached_counts(args, counts)

    return counts


def _attach_quick_filter_counts(page_data, args):
    cached_counts = _get_cached_counts(args)

    if cached_counts is not None:
        counts = cached_counts
        counts_ready = True
    else:
        counts = _quick_counts_from_page_data(page_data)
        counts_ready = False

    visible_total = _safe_int(
        page_data.get("total_records"),
        counts.get("total", 0),
    )

    counts["total"] = visible_total

    page_data["filter_total_count"] = visible_total
    page_data["filter_type_counts"] = counts.get("type", {})
    page_data["filter_department_counts"] = counts.get("department", {})
    page_data["filter_location_counts"] = counts.get("location", {})
    page_data["filter_status_counts"] = counts.get("status", {})
    page_data["filter_counts"] = counts
    page_data["filter_counts_ready"] = counts_ready

    return page_data


def _attach_exact_filter_counts(page_data, args):
    counts = _get_exact_filter_counts(page_data, args)

    visible_total = _safe_int(
        page_data.get("total_records"),
        counts.get("total", 0),
    )

    counts["total"] = visible_total

    page_data["filter_total_count"] = visible_total
    page_data["filter_type_counts"] = counts.get("type", {})
    page_data["filter_department_counts"] = counts.get("department", {})
    page_data["filter_location_counts"] = counts.get("location", {})
    page_data["filter_status_counts"] = counts.get("status", {})
    page_data["filter_counts"] = counts
    page_data["filter_counts_ready"] = True

    return page_data


def register_report_routes(app):

    @app.route("/report")
    def report_page():
        report_args = _copy_report_args(request.args)
        page_data = get_report_page_data(report_args)

        ajax_type = request.args.get("_ajax")

        if _is_ajax_request() and ajax_type == "report_counts":
            exact_counts = _get_exact_filter_counts(page_data, report_args)

            visible_total = _safe_int(
                page_data.get("total_records"),
                exact_counts.get("total", 0),
            )

            exact_counts["total"] = visible_total

            return jsonify({
                "success": True,
                "counts": exact_counts,
                "counts_ready": True,
                "total_records": visible_total,
            })

        if _is_ajax_request() and ajax_type == "report_list":
            page_data = _attach_quick_filter_counts(page_data, report_args)

            table_html = render_template(
                "report/report_table.html",
                **page_data,
            )

            visible_total = _safe_int(
                page_data.get("total_records"),
                page_data.get("filter_total_count", 0),
            )

            filter_counts = page_data.get("filter_counts", {})
            filter_counts["total"] = visible_total

            return jsonify({
                "success": True,
                "table_html": table_html,
                "counts": filter_counts,
                "counts_ready": page_data.get("filter_counts_ready", False),
                "total_records": visible_total,
                "current_page": page_data.get("current_page", 1),
                "total_pages": page_data.get("total_pages", 1),
            })

        page_data = _attach_exact_filter_counts(page_data, report_args)

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