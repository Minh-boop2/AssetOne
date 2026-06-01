from flask import Response, flash, jsonify, redirect, render_template, request, session, url_for
from secrets import choice
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

_REPORT_FILTER_COUNT_CACHE = {}
_REPORT_FILTER_COUNT_TTL = 45
_CODE_PREFIX = "REPORT-"
_CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_CODE_KEYS = ("report_code", "display_report_code", "code", "auto_report_id")


def _clear_report_cache():
    _REPORT_FILTER_COUNT_CACHE.clear()


def _safe_int(value, default=1):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _row_get(row, key, fb=""):
    if isinstance(row, dict):
        value = row.get(key)
    else:
        value = getattr(row, key, None)
        if value is None and hasattr(row, "get"):
            try:
                value = row.get(key)
            except Exception:
                value = None

    value = str(value or "").strip()
    return value or fb


def _norm_code(value):
    code = str(value or "").strip().upper()

    if code == "REPORT-000000":
        return ""

    tail = code.replace(_CODE_PREFIX, "", 1)
    return code if code.startswith(_CODE_PREFIX) and len(tail) == 8 and tail.isalnum() else ""


def _row_code(row):
    for key in _CODE_KEYS:
        code = _norm_code(_row_get(row, key))
        if code:
            return code

    return ""


def _make_code(existing=None):
    used = {_norm_code(x) for x in existing or [] if _norm_code(x)}

    while True:
        code = _CODE_PREFIX + "".join(choice(_CODE_CHARS) for _ in range(8))
        if code not in used:
            return code


def _set_row_code(row, code):
    if not row or not code:
        return row

    for key in _CODE_KEYS:
        try:
            row[key] = code
        except Exception:
            try:
                setattr(row, key, code)
            except Exception:
                pass

    return row


def _row_fingerprint(row):
    return "|".join([
        _row_get(row, "display_report_name") or _row_get(row, "report_name"),
        _row_get(row, "display_reporter") or _row_get(row, "reporter"),
        _row_get(row, "display_time") or _row_get(row, "time"),
        _row_get(row, "display_report_type") or _row_get(row, "report_type"),
    ]).lower()


def _form_fingerprint(form):
    return "|".join([
        str(form.get("report_name") or "").strip(),
        str(form.get("reporter") or "").strip(),
        str(form.get("time") or "").strip(),
        str(form.get("report_type") or "").strip(),
    ]).lower()


def _remember_code(real_code, form_data, returned_data=None):
    if not real_code:
        return

    code_map = session.get("report_code_map", {})
    finger_map = session.get("report_code_finger_map", {})

    for key in _CODE_KEYS:
        other = _norm_code((returned_data or {}).get(key) if isinstance(returned_data, dict) else "")
        if other:
            code_map[other] = real_code

    finger = _form_fingerprint(form_data)
    if finger:
        finger_map[finger] = real_code

    session["last_report_code"] = real_code
    session["report_code_map"] = code_map
    session["report_code_finger_map"] = finger_map
    session.modified = True


def _fix_row_code(row):
    code_map = session.get("report_code_map", {})
    finger_map = session.get("report_code_finger_map", {})

    row_code = _row_code(row)
    fixed = code_map.get(row_code) or finger_map.get(_row_fingerprint(row))

    return _set_row_code(row, fixed) if fixed else row


def _fix_page_codes(page_data):
    for key in ("reports", "all_reports", "filtered_reports", "all_filtered_reports", "report_logs"):
        rows = page_data.get(key)
        if isinstance(rows, list):
            for row in rows:
                _fix_row_code(row)

    return page_data


def _fix_detail_code(report):
    return _fix_row_code(report)


def _copy_args(args):
    copied = MultiDict()

    for key, value in args.items(multi=True):
        if key not in {"_ajax", "_ts"}:
            copied.add(key, value)

    return copied


def _args_page(args, page):
    copied = _copy_args(args)
    copied["page"] = str(page)
    return copied


def _find_full_rows(page_data):
    for key in ("all_filtered_reports", "filtered_reports", "all_reports", "reports_all", "report_logs", "all_report_logs"):
        rows = page_data.get(key)
        if isinstance(rows, list) and rows:
            return rows

    return None


def _collect_rows(first_data, args):
    full_rows = _find_full_rows(first_data)
    if full_rows is not None:
        return full_rows

    cur = _safe_int(first_data.get("current_page"), _safe_int(args.get("page"), 1))
    total = _safe_int(first_data.get("total_pages"), 1)
    rows, seen = [], set()

    def add(items):
        for row in items or []:
            key = (
                _row_get(row, "_row_index"),
                _row_code(row),
                _row_get(row, "display_report_name"),
                _row_get(row, "display_time"),
            )

            if key not in seen:
                seen.add(key)
                rows.append(row)

    for page in range(1, total + 1):
        if page == cur:
            add(first_data.get("reports", []))
            continue

        try:
            add(get_report_page_data(_args_page(args, page)).get("reports", []))
        except Exception:
            pass

    if not rows:
        add(first_data.get("reports", []))

    return rows


def _existing_codes():
    args = MultiDict([("page", "1")])

    try:
        data = _fix_page_codes(get_report_page_data(args))
        rows = _collect_rows(data, args)
    except Exception:
        rows = []

    return {code for code in (_row_code(row) for row in rows) if code}


def _prepare_create_data():
    data = get_create_page_data() or {}
    existing = _existing_codes()

    code = _norm_code(data.get("auto_report_id") or data.get("report_code") or data.get("display_report_code") or data.get("code"))

    if not code or code in existing:
        code = _make_code(existing)

    for key in _CODE_KEYS:
        data[key] = code

    data["existing_report_codes"] = sorted(existing)
    session["pending_report_code"] = code
    session.modified = True

    return data


def _prepare_post_form(form):
    data = MultiDict(form)
    existing = _existing_codes()

    code = ""

    for key in _CODE_KEYS:
        code = _norm_code(data.get(key))
        if code:
            break

    pending = _norm_code(session.get("pending_report_code"))

    if not code:
        code = pending

    if not code:
        code = _make_code(existing)

    for key in _CODE_KEYS:
        data.setlist(key, [code])

    data.setlist("ma_bao_cao", [code])
    data.setlist("report_id", [code])
    data.setlist("display_code", [code])

    return data, code


def _json_or_form_data():
    return request.get_json(silent=True) or {} if request.is_json else request.form.to_dict(flat=True)


def _is_ajax():
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.accept_mimetypes.best == "application/json"
        or request.is_json
    )


def _next_url(default_endpoint="report_page", **kwargs):
    return request.form.get("next") or request.args.get("next") or request.headers.get("Referer") or url_for(default_endpoint, **kwargs)


def _count_key(args):
    clean = _copy_args(args)
    clean.pop("page", None)
    return tuple((k, str(v)) for k in sorted(clean.keys()) for v in clean.getlist(k))


def _cached_counts(args):
    key = _count_key(args)
    item = _REPORT_FILTER_COUNT_CACHE.get(key)

    if not item:
        return None

    if time() - item.get("created_at", 0) > _REPORT_FILTER_COUNT_TTL:
        _REPORT_FILTER_COUNT_CACHE.pop(key, None)
        return None

    return item.get("counts")


def _save_counts(args, counts):
    _REPORT_FILTER_COUNT_CACHE[_count_key(args)] = {"created_at": time(), "counts": counts or {}}

    if len(_REPORT_FILTER_COUNT_CACHE) > 80:
        oldest = min(_REPORT_FILTER_COUNT_CACHE, key=lambda k: _REPORT_FILTER_COUNT_CACHE[k].get("created_at", 0))
        _REPORT_FILTER_COUNT_CACHE.pop(oldest, None)


def _count_map(rows, key, fb="Chưa xác định"):
    out = {}

    for row in rows or []:
        value = _row_get(row, key, fb)
        out[value] = out.get(value, 0) + 1

    return out


def _counts_from_rows(rows):
    rows = rows or []

    return {
        "total": len(rows),
        "type": _count_map(rows, "display_report_type", "Khác"),
        "department": _count_map(rows, "display_department", "Chưa xác định"),
        "location": _count_map(rows, "display_location", "Chưa xác định"),
        "status": _count_map(rows, "display_report_status", "Chờ xử lý"),
    }


def _quick_counts(data):
    return {
        "total": _safe_int(data.get("total_records"), len(data.get("reports", []) or [])),
        "type": data.get("type_counts") or {},
        "department": data.get("department_counts") or {},
        "location": data.get("location_counts") or {},
        "status": data.get("status_counts") or {},
    }


def _exact_counts(data, args):
    cached = _cached_counts(args)

    if cached is not None:
        return cached

    counts = _counts_from_rows(_collect_rows(data, args))
    _save_counts(args, counts)
    return counts


def _apply_counts(data, counts, ready):
    total = _safe_int(data.get("total_records"), counts.get("total", 0))
    counts["total"] = total

    data.update({
        "filter_total_count": total,
        "filter_type_counts": counts.get("type", {}),
        "filter_department_counts": counts.get("department", {}),
        "filter_location_counts": counts.get("location", {}),
        "filter_status_counts": counts.get("status", {}),
        "filter_counts": counts,
        "filter_counts_ready": ready,
    })

    return data


def register_report_routes(app):
    @app.route("/report")
    def report_page():
        args = _copy_args(request.args)
        data = _fix_page_codes(get_report_page_data(args))
        ajax = request.args.get("_ajax")

        if _is_ajax() and ajax == "report_counts":
            counts = _exact_counts(data, args)
            counts["total"] = _safe_int(data.get("total_records"), counts.get("total", 0))
            return jsonify({"success": True, "counts": counts, "counts_ready": True, "total_records": counts["total"]})

        if _is_ajax() and ajax == "report_list":
            cached = _cached_counts(args)
            data = _apply_counts(data, cached, True) if cached is not None else _apply_counts(data, _quick_counts(data), False)
            counts = data.get("filter_counts", {})
            counts["total"] = _safe_int(data.get("total_records"), data.get("filter_total_count", 0))

            return jsonify({
                "success": True,
                "table_html": render_template("report/report_table.html", **data),
                "counts": counts,
                "counts_ready": data.get("filter_counts_ready", False),
                "total_records": counts["total"],
                "current_page": data.get("current_page", 1),
                "total_pages": data.get("total_pages", 1),
            })

        return render_template("report/report.html", **_apply_counts(data, _exact_counts(data, args), True))

    @app.route("/report/assets/search")
    def search_report_assets_route():
        return jsonify(search_report_assets(request.args.get("keyword", "") or request.args.get("q", "") or ""))

    @app.route("/report/files/<path:filename>")
    def report_file_proxy(filename):
        content, status_code, headers = api_get_report_file_content(
            filename=filename,
            download=request.args.get("download") == "1",
        )
        return Response(content, status=status_code, headers=headers)

    @app.route("/report/create", methods=["GET", "POST"])
    @app.route("/report/new", methods=["GET", "POST"])
    def new_report_page():
        if request.method == "POST":
            uploaded_files = []

            for field_name in request.files:
                uploaded_files.extend(request.files.getlist(field_name))

            form_data, real_code = _prepare_post_form(request.form)
            success, message, data, status_code = create_report_from_form(form_data, uploaded_files)

            if success:
                _clear_report_cache()
                _remember_code(real_code, form_data, data if isinstance(data, dict) else None)

            if isinstance(data, dict):
                for key in _CODE_KEYS:
                    data[key] = real_code

            if _is_ajax():
                return jsonify({"success": success, "message": message, "data": data}), status_code

            flash(message, "success" if success else "danger")
            return redirect(url_for("report_page" if success else "new_report_page"))

        return render_template("report/report_create.html", **_prepare_create_data())

    @app.route("/report/detail/<path:row_index>")
    def report_detail_page(row_index):
        report, error, status_code = get_report_detail_page_data(row_index)

        if error:
            if _is_ajax():
                return jsonify({"success": False, "message": error}), status_code

            flash(error, "warning")
            return redirect(url_for("report_page"))

        return render_template("report/report_detail.html", report=_fix_detail_code(report))

    @app.route("/report/delete/<path:row_index>", methods=["GET", "POST", "DELETE"])
    def delete_report_log(row_index):
        success, message, category, status_code = delete_report(row_index)

        if success:
            _clear_report_cache()

        if _is_ajax():
            return jsonify({"success": success, "message": message, "category": category}), status_code

        flash(message, category or "success")
        return redirect(_next_url())

    @app.route("/report/approve/<path:row_index>", methods=["POST", "PATCH"])
    def approve_report_log(row_index):
        success, message, payload, status_code = approve_report(row_index, _json_or_form_data())

        if success:
            _clear_report_cache()

        if _is_ajax():
            return jsonify({
                "success": success,
                "message": message,
                "data": payload.get("data") if isinstance(payload, dict) else payload,
                "asset_action_result": payload.get("asset_action_result") if isinstance(payload, dict) else None,
            }), status_code

        flash(message, "success" if success else "danger")
        return redirect(_next_url("report_detail_page", row_index=row_index))

    @app.route("/report/cancel/<path:row_index>", methods=["POST", "PATCH"])
    def cancel_report_log(row_index):
        success, message, payload, status_code = cancel_report(row_index, _json_or_form_data())

        if success:
            _clear_report_cache()

        if _is_ajax():
            return jsonify({
                "success": success,
                "message": message,
                "data": payload.get("data") if isinstance(payload, dict) else payload,
            }), status_code

        flash(message, "success" if success else "danger")
        return redirect(_next_url("report_detail_page", row_index=row_index))

    @app.route("/report/file/delete/<path:row_index>/<file_id>", methods=["POST", "DELETE"])
    def delete_report_file_log(row_index, file_id):
        success, message, payload, status_code = delete_file(row_index, file_id)

        if _is_ajax():
            return jsonify({
                "success": success,
                "message": message,
                "data": payload.get("data") if isinstance(payload, dict) else payload,
            }), status_code

        flash(message, "success" if success else "danger")
        return redirect(_next_url("report_detail_page", row_index=row_index))