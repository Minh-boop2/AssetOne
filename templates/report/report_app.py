from collections import Counter
from datetime import datetime
import math
import random

from flask import flash, jsonify, redirect, render_template, request, url_for

import data


REPORT_TYPES = [
    "Sự cố thiết bị",
    "Báo hỏng",
    "Bảo trì",
    "Mất thiết bị",
    "Cấp phát",
    "Thu hồi",
    "Bàn giao",
    "Kiểm kê",
    "Cập nhật thông tin",
    "Khác",
]

REPORT_STATUSES = [
    "Chờ xử lý",
    "Đã xem",
    "Đang xử lý",
    "Hoàn thành",
    "Từ chối",
]


def _clean(value):
    return str(value or "").strip()


def _norm(value):
    return _clean(value).lower()


def _first(source, *keys, default=""):
    for key in keys:
        value = source.get(key)

        if value not in [None, ""]:
            return value

    return default


def _unique(values):
    result = []

    for value in values:
        value = _clean(value)

        if value and value not in result:
            result.append(value)

    return result


def _now_text():
    return datetime.now().strftime("%H:%M %d/%m/%Y")


def _current_admin():
    current_user = getattr(data, "CURRENT_USER", {})

    if isinstance(current_user, dict):
        name = _first(
            current_user,
            "name",
            "username",
            "display_name",
            default="Admin",
        )

        role = _first(
            current_user,
            "role",
            "position",
            default="Admin",
        )

        return _clean(name), _clean(role)

    return "Admin", "Admin"


def _report_type(log):
    raw = _clean(
        _first(
            log,
            "report_type",
            "type",
            "action",
            "activity",
            "event",
        )
    )

    value = _norm(raw)

    rules = [
        (["sự cố", "su co"], "Sự cố thiết bị"),
        (["báo hỏng", "bao hong", "hỏng"], "Báo hỏng"),
        (["bảo trì", "bao tri", "maintenance", "sửa chữa"], "Bảo trì"),
        (["mất", "mat", "lost"], "Mất thiết bị"),
        (["cấp phát", "cap phat", "assign"], "Cấp phát"),
        (["thu hồi", "thu hoi", "return", "revoke"], "Thu hồi"),
        (["bàn giao", "ban giao"], "Bàn giao"),
        (["kiểm kê", "kiem ke"], "Kiểm kê"),
        (["cập nhật", "cap nhat", "update"], "Cập nhật thông tin"),
    ]

    for keywords, label in rules:
        if any(keyword in value for keyword in keywords):
            return label

    return raw or "Khác"


def _report_status(log):
    raw = _clean(_first(log, "report_status", "status"))
    value = _norm(raw)

    if value in ["đã xem", "da xem", "viewed"]:
        return "Đã xem"

    if value in ["đang xử lý", "dang xu ly", "processing"]:
        return "Đang xử lý"

    if value in ["hoàn thành", "hoan thanh", "success", "done", "completed"]:
        return "Hoàn thành"

    if value in ["từ chối", "tu choi", "rejected", "denied"]:
        return "Từ chối"

    return "Chờ xử lý"


def _asset_name(log):
    return _clean(_first(log, "asset_name", "asset", "name"))


def _asset_code(log):
    return _clean(_first(log, "asset_code", "code"))


def _department(log):
    return _clean(_first(log, "department", "dept"))


def _location(log):
    return _clean(_first(log, "location", "position", "place", "floor"))


def _reporter(log):
    return _clean(_first(log, "reporter", "user", "receiver", "username"))


def _matched_assignment(asset_name):
    asset_key = _norm(asset_name)

    if not asset_key:
        return {}

    assignments = getattr(data, "ASSIGN_DATA", [])

    for item in assignments:
        if _norm(item.get("asset")) == asset_key:
            return item

    for item in assignments:
        item_key = _norm(item.get("asset"))

        if item_key and (asset_key in item_key or item_key in asset_key):
            return item

    return {}


def _report_name(log):
    name = _clean(log.get("report_name"))

    if name:
        return name

    report_type = _report_type(log)
    asset_name = _asset_name(log) or "Chưa xác định"

    return f"{report_type} - {asset_name}"


def _prepare_report(row_index, log):
    item = dict(log)
    asset_name = _asset_name(log)
    assignment = _matched_assignment(asset_name)

    item["_row_index"] = row_index

    item["display_report_code"] = _clean(
        _first(
            log,
            "report_code",
            "id",
            default=f"Report-{row_index + 1:06d}",
        )
    )

    item["display_report_name"] = _report_name(log)
    item["display_report_type"] = _report_type(log)
    item["display_report_status"] = _report_status(log)
    item["display_priority"] = _clean(log.get("priority")) or "Bình thường"

    item["display_reporter"] = _reporter(log) or _clean(assignment.get("receiver"))
    item["display_reporter_role"] = _clean(_first(log, "reporter_role", "role"))

    item["display_created_by"] = _clean(log.get("created_by")) or "Admin"
    item["display_created_by_role"] = _clean(log.get("created_by_role")) or "Admin"

    item["display_department"] = _department(log) or _clean(assignment.get("department"))
    item["display_location"] = _location(log) or _clean(assignment.get("location"))

    item["display_asset_name"] = asset_name
    item["display_asset_code"] = _asset_code(log) or _clean(assignment.get("asset_code"))

    item["display_detail"] = _clean(_first(log, "description", "detail"))
    item["display_note"] = _clean(log.get("note"))
    item["display_time"] = _clean(_first(log, "time", "created_at", "date"))

    return item


def _all_reports():
    raw_logs = getattr(data, "DATABASE_LOGS", [])

    return [
        _prepare_report(index, log)
        for index, log in enumerate(raw_logs)
    ]


def _filter_options(reports):
    type_values = list(getattr(data, "LOG_TYPES", [])) + REPORT_TYPES
    department_values = list(getattr(data, "DEPARTMENTS", []))
    location_values = list(getattr(data, "LOCATIONS", []))

    type_values += [report.get("display_report_type") for report in reports]
    department_values += [report.get("display_department") for report in reports]
    location_values += [report.get("display_location") for report in reports]

    return {
        "report_type_options": _unique(type_values),
        "department_options": _unique(department_values),
        "location_options": _unique(location_values),
        "report_status_options": REPORT_STATUSES,
    }


def _search_reports(reports, keyword):
    keyword = _norm(keyword)

    if not keyword:
        return reports

    search_fields = [
        "display_report_code",
        "display_report_name",
        "display_report_type",
        "display_report_status",
        "display_priority",
        "display_reporter",
        "display_reporter_role",
        "display_created_by",
        "display_department",
        "display_location",
        "display_asset_name",
        "display_asset_code",
        "display_detail",
        "display_note",
        "display_time",
    ]

    return [
        report for report in reports
        if any(keyword in _norm(report.get(field)) for field in search_fields)
    ]


def _apply_filters(reports, selected_type, selected_dept, selected_location, selected_status):
    if selected_type != "Tất cả":
        reports = [
            report for report in reports
            if _norm(report.get("display_report_type")) == _norm(selected_type)
        ]

    if selected_dept != "Tất cả":
        reports = [
            report for report in reports
            if _norm(report.get("display_department")) == _norm(selected_dept)
        ]

    if selected_location != "Tất cả":
        reports = [
            report for report in reports
            if _norm(report.get("display_location")) == _norm(selected_location)
        ]

    if selected_status != "Tất cả":
        reports = [
            report for report in reports
            if _norm(report.get("display_report_status")) == _norm(selected_status)
        ]

    return reports


def _paginate(items, page, per_page):
    total_records = len(items)
    total_pages = max(1, math.ceil(total_records / per_page))
    current_page = max(1, min(page, total_pages))

    start = (current_page - 1) * per_page
    end = start + per_page

    return {
        "items": items[start:end],
        "total_records": total_records,
        "total_pages": total_pages,
        "current_page": current_page,
        "per_page": per_page,
    }


def _existing_report_codes():
    codes = set()

    for log in getattr(data, "DATABASE_LOGS", []):
        code = _clean(_first(log, "report_code", "id"))

        if code:
            codes.add(code.lower())

    return codes


def _generate_report_id():
    existing_codes = _existing_report_codes()

    while True:
        code = f"Report-{random.randint(100000, 999999)}"

        if code.lower() not in existing_codes:
            return code


def _safe_report_code(code):
    code = _clean(code)

    if code and code.lower() not in _existing_report_codes():
        return code

    return _generate_report_id()


def _asset_sources():
    names = [
        "INVENTORY_LIST",
        "ASSET_DATA",
        "ASSETS_DATA",
        "ASSETS",
        "DEVICE_DATA",
        "DEVICES",
        "ASSIGN_DATA",
    ]

    return [getattr(data, name, []) for name in names]


def _normalize_asset(item):
    return {
        "code": _clean(_first(item, "asset_code", "code", "id")),
        "name": _clean(_first(item, "asset_name", "asset", "name")),
        "type": _clean(_first(item, "type", "category", "device_type")),
        "department": _clean(_first(item, "department", "dept")),
        "location": _clean(_first(item, "location", "position", "place", "floor")),
        "status": _clean(item.get("status")),
    }


def _asset_options():
    results = []
    seen = set()

    for source in _asset_sources():
        for item in source:
            asset = _normalize_asset(item)
            key = _norm(asset["code"] or asset["name"])

            if not key or key in seen:
                continue

            seen.add(key)
            results.append(asset)

    return results


def get_report_page_data(args):
    search_q = args.get("search", "").strip()
    selected_type = args.get("type", "Tất cả")
    selected_dept = args.get("department", "Tất cả")
    selected_location = args.get("location", "Tất cả")
    selected_status = args.get("status", "Tất cả")

    has_active_filter = (
        search_q != ""
        or selected_type != "Tất cả"
        or selected_dept != "Tất cả"
        or selected_location != "Tất cả"
        or selected_status != "Tất cả"
    )

    page = max(1, args.get("page", 1, type=int))
    per_page = 10

    all_reports = _all_reports()
    options = _filter_options(all_reports)

    filtered_reports = _search_reports(all_reports, search_q)
    filtered_reports = _apply_filters(
        filtered_reports,
        selected_type,
        selected_dept,
        selected_location,
        selected_status,
    )

    pagination = _paginate(filtered_reports, page, per_page)

    return {
        "reports": pagination["items"],
        "logs": pagination["items"],
        "report_logs": pagination["items"],

        "total_records": pagination["total_records"],
        "total_logs": pagination["total_records"],
        "total_report_count": len(all_reports),

        "current_page": pagination["current_page"],
        "total_pages": pagination["total_pages"],
        "per_page": pagination["per_page"],

        "search_q": search_q,
        "search_query": search_q,
        "search_value": search_q,

        "selected_type": selected_type,
        "selected_dept": selected_dept,
        "selected_location": selected_location,
        "selected_status": selected_status,
        "has_active_filter": has_active_filter,

        "type_counts": Counter(
            report.get("display_report_type") or "Khác"
            for report in all_reports
        ),
        "department_counts": Counter(
            report.get("display_department")
            for report in all_reports
            if report.get("display_department")
        ),
        "location_counts": Counter(
            report.get("display_location")
            for report in all_reports
            if report.get("display_location")
        ),
        "status_counts": Counter(
            report.get("display_report_status") or "Chờ xử lý"
            for report in all_reports
        ),

        **options,
    }


def get_create_page_data():
    reports = _all_reports()
    current_admin_name, current_admin_role = _current_admin()
    role_options = list(getattr(data, "ROLES", ["Admin", "Manager", "Staff"]))

    return {
        "current_time": _now_text(),
        "auto_report_id": _generate_report_id(),
        "current_admin_name": current_admin_name,
        "current_admin_role": current_admin_role,
        "role_options": role_options,
        "reporter_role_options": role_options,
        "asset_options": _asset_options(),
        **_filter_options(reports),
    }


def create_report_from_form(form):
    report_code = _safe_report_code(form.get("report_code"))
    report_type = _clean(form.get("report_type"))
    report_name = _clean(form.get("report_name"))
    reporter = _clean(form.get("reporter"))
    asset_name = _clean(form.get("asset_name")) or "Chưa xác định"
    department = _clean(form.get("department"))
    location = _clean(form.get("location"))
    description = _clean(form.get("description"))
    note = _clean(form.get("note"))
    priority = _clean(form.get("priority")) or "Bình thường"
    reporter_role = _clean(form.get("reporter_role"))
    created_time = _clean(form.get("time")) or _now_text()

    current_admin_name, current_admin_role = _current_admin()

    if not report_name:
        return False, "Vui lòng nhập tên báo cáo.", None

    if not report_type:
        return False, "Vui lòng chọn loại báo cáo.", None

    if not reporter:
        return False, "Vui lòng nhập người báo cáo.", None

    if not reporter_role:
        return False, "Vui lòng chọn chức vụ người báo cáo.", None

    if not department:
        return False, "Vui lòng chọn phòng ban.", None

    if not location:
        return False, "Vui lòng chọn vị trí.", None

    if not description:
        return False, "Vui lòng nhập nội dung báo cáo.", None

    new_report = {
        "id": report_code,
        "report_code": report_code,

        "report_name": report_name,
        "report_type": report_type,
        "type": report_type,
        "priority": priority,

        "asset_name": asset_name,
        "asset": asset_name,
        "asset_code": _clean(form.get("asset_code")),

        "reporter": reporter,
        "user": reporter,

        "reporter_role": reporter_role,
        "role": reporter_role,

        "department": department,
        "dept": department,
        "location": location,

        "status": "Chờ xử lý",
        "report_status": "Chờ xử lý",

        "description": description,
        "detail": description,
        "note": note,

        "time": created_time,
        "created_at": created_time,

        "created_by": current_admin_name,
        "created_by_role": current_admin_role,
    }

    data.DATABASE_LOGS.insert(0, new_report)

    return True, "Tạo báo cáo thành công", new_report


def get_report_detail_page_data(row_index):
    raw_logs = getattr(data, "DATABASE_LOGS", [])

    if row_index < 0 or row_index >= len(raw_logs):
        return None, "Không tìm thấy báo cáo."

    current_status = _norm(raw_logs[row_index].get("status"))

    if current_status in ["", "chờ", "cho", "chờ xử lý", "cho xu ly"]:
        raw_logs[row_index]["status"] = "Đã xem"
        raw_logs[row_index]["report_status"] = "Đã xem"

    return _prepare_report(row_index, raw_logs[row_index]), None


def delete_report(row_index):
    raw_logs = getattr(data, "DATABASE_LOGS", [])

    if row_index < 0 or row_index >= len(raw_logs):
        return False, "Không tìm thấy báo cáo cần xóa.", "warning"

    del raw_logs[row_index]

    return True, "Xóa báo cáo thành công", "danger"


def register_report_routes(app):
    @app.route("/report")
    def report_page():
        page_data = get_report_page_data(request.args)

        return render_template(
            "report/report.html",
            **page_data,
        )

    @app.route("/report/assets/search")
    def search_report_assets():
        keyword = _norm(request.args.get("keyword", "") or request.args.get("q", ""))

        if not keyword:
            return jsonify({"items": []})

        results = []
        seen = set()

        for source in _asset_sources():
            for item in source:
                asset = _normalize_asset(item)

                if not asset["code"] and not asset["name"]:
                    continue

                text = _norm(
                    f"{asset['code']} {asset['name']} {asset['type']} "
                    f"{asset['department']} {asset['location']} {asset['status']}"
                )

                key = _norm(asset["code"] or asset["name"])

                if keyword in text and key and key not in seen:
                    seen.add(key)
                    results.append(asset)

        return jsonify({"items": results[:10]})

    @app.route("/report/create", methods=["GET", "POST"])
    @app.route("/report/new", methods=["GET", "POST"])
    def new_report_page():
        if request.method == "POST":
            success, message, _ = create_report_from_form(request.form)

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

    @app.route("/report/detail/<int:row_index>")
    def report_detail_page(row_index):
        report, error = get_report_detail_page_data(row_index)

        if error:
            flash(error, "warning")
            return redirect(url_for("report_page"))

        return render_template(
            "report/report_detail.html",
            report=report,
        )

    @app.route("/report/delete/<int:row_index>", methods=["GET", "POST"])
    def delete_report_log(row_index):
        success, message, category = delete_report(row_index)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            status_code = 200 if success else 404

            return jsonify({
                "success": success,
                "message": message,
                "category": category,
            }), status_code

        flash(message, category or "success")

        return redirect(url_for("report_page"))