import os
import re
from collections import Counter
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from flask import request, session


BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:5001").rstrip("/")

REPORT_DEFAULT_STATUSES = [
    "Chờ xử lý",
    "Hoàn thành",
    "Đã hủy",
]

REPORT_DEFAULT_TYPES = [
    "Báo hỏng",
    "Cần cấp mới",
    "Khác",
]

DEFAULT_ROLE_OPTIONS = [
    "Admin",
    "Manager",
    "Staff",
]

ASSET_FORM_FIELDS = [
    "asset_ids",
    "asset_codes",
    "assets",
    "selected_assets",
    "selected_asset_ids",
    "selected_asset_codes",
    "asset_id",
    "asset_code",
    "asset",
]

ASSET_ID_LIKE_FIELDS = [
    "asset_ids",
    "selected_asset_ids",
    "assets",
    "selected_assets",
    "asset_id",
    "asset",
]

ASSET_CODE_LIKE_FIELDS = [
    "asset_codes",
    "selected_asset_codes",
    "asset_code",
]


def _clean(value):
    return str(value or "").strip()


def _norm(value):
    return _clean(value).lower()


def _safe_int(value, default=1, min_value=1, max_value=None):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = default

    value = max(min_value, value)

    if max_value is not None:
        value = min(value, max_value)

    return value


def _first(source, *keys, default=""):
    if not isinstance(source, dict):
        return default

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


def _flatten_values(value):
    values = []

    if value is None:
        return values

    if isinstance(value, dict):
        for key in [
            "asset_id",
            "id",
            "_id",
            "asset_code",
            "code",
            "value",
            "asset",
        ]:
            if value.get(key) not in [None, ""]:
                values.extend(_flatten_values(value.get(key)))
                break

        return values

    if isinstance(value, (list, tuple, set)):
        for item in value:
            values.extend(_flatten_values(item))

        return values

    text = _clean(value)

    if not text:
        return values

    for part in re.split(r"[,;]", text):
        part = _clean(part)

        if part:
            values.append(part)

    return values


def _join_values(value, separator=", "):
    values = _unique(_flatten_values(value))

    if values:
        return separator.join(values)

    return _clean(value)


def _get_form_values(form_data, key):
    if not form_data:
        return []

    if hasattr(form_data, "getlist"):
        try:
            return form_data.getlist(key)
        except Exception:
            pass

    if isinstance(form_data, dict):
        value = form_data.get(key)

        if isinstance(value, (list, tuple, set)):
            return list(value)

        if value not in [None, ""]:
            return [value]

    return []


def _collect_form_values(form_data, fields):
    values = []

    for field in fields:
        for value in _get_form_values(form_data, field):
            values.extend(_flatten_values(value))

    return _unique(values)


def _build_report_form_payload(form_data):
    if hasattr(form_data, "items"):
        data = {
            key: value
            for key, value in form_data.items()
        }
    elif isinstance(form_data, dict):
        data = dict(form_data)
    else:
        data = {}

    for field in ASSET_FORM_FIELDS:
        values = _collect_form_values(form_data, [field])

        if values:
            data[field] = ",".join(values)

    asset_id_values = _collect_form_values(form_data, ASSET_ID_LIKE_FIELDS)
    asset_code_values = _collect_form_values(form_data, ASSET_CODE_LIKE_FIELDS)

    if asset_id_values:
        data["asset_ids"] = ",".join(asset_id_values)

    if asset_code_values:
        data["asset_codes"] = ",".join(asset_code_values)

    return data


def _now_text():
    return datetime.now().strftime("%H:%M %d/%m/%Y")


def _get_session_user():
    for key in ["current_user", "user", "auth_user", "login_user"]:
        value = session.get(key)

        if isinstance(value, dict):
            return value

    return {}


def _current_user_id():
    user = _get_session_user()

    return (
        request.headers.get("X-User-Id")
        or user.get("id")
        or user.get("_id")
        or user.get("user_id")
        or ""
    )


def _current_employee_code():
    user = _get_session_user()

    return (
        request.headers.get("X-Employee-Code")
        or user.get("employee_code")
        or ""
    )


def _current_user_name():
    user = _get_session_user()

    return (
        user.get("full_name")
        or user.get("name")
        or user.get("username")
        or user.get("email")
        or "Admin"
    )


def _current_user_department():
    user = _get_session_user()

    return (
        user.get("department")
        or user.get("dept")
        or ""
    )


def _current_user_location():
    user = _get_session_user()

    return (
        user.get("floor")
        or user.get("location")
        or user.get("place")
        or ""
    )


def _current_user_role():
    user = _get_session_user()
    role = user.get("role") or "Admin"

    if role == "ADMIN":
        return "Admin"

    if role == "QUAN_LY":
        return "Manager"

    if role == "NHAN_VIEN":
        return "Staff"

    return role


def _api_url(path):
    return urljoin(BACKEND_API_URL + "/", path.lstrip("/"))


def _api_headers(accept_json=True):
    headers = {}

    if accept_json:
        headers["Accept"] = "application/json"

    user_id = _current_user_id()
    employee_code = _current_employee_code()

    if user_id:
        headers["X-User-Id"] = str(user_id)

    if employee_code:
        headers["X-Employee-Code"] = str(employee_code)

    auth_header = request.headers.get("Authorization")

    if auth_header:
        headers["Authorization"] = auth_header

    return headers


def _api_request(method, path, params=None, data=None, json_data=None, files=None):
    url = _api_url(path)

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=_api_headers(),
            params=params,
            data=data,
            json=json_data,
            files=files,
            timeout=25,
        )

        try:
            payload = response.json()
        except Exception:
            payload = {
                "success": False,
                "message": response.text or "Backend không trả về JSON.",
            }

        success = 200 <= response.status_code < 300

        return success, payload, response.status_code

    except requests.RequestException as error:
        return False, {
            "success": False,
            "message": f"Không kết nối được backend API: {error}",
        }, 503


def _extract_filename_from_file_record(file_record):
    if not isinstance(file_record, dict):
        return ""

    stored_name = _clean(file_record.get("stored_name"))

    if stored_name:
        return stored_name

    raw_url = _clean(file_record.get("url"))

    if not raw_url:
        return ""

    parsed = urlparse(raw_url)
    path = parsed.path or raw_url

    return os.path.basename(path)


def _normalize_report_files(files):
    if not isinstance(files, list):
        return []

    normalized_files = []

    for file_record in files:
        if not isinstance(file_record, dict):
            continue

        item = dict(file_record)
        stored_name = _extract_filename_from_file_record(item)

        if stored_name:
            item["stored_name"] = stored_name
            item["url"] = f"/report/files/{stored_name}"
            item["download_url"] = f"/report/files/{stored_name}?download=1"

        normalized_files.append(item)

    return normalized_files


def api_get_report_file_content(filename, download=False):
    params = {}

    if download:
        params["download"] = "1"

    url = _api_url(f"/api/reports/files/{filename}")

    try:
        response = requests.get(
            url=url,
            headers=_api_headers(accept_json=False),
            params=params,
            timeout=30,
        )

        ignored_headers = {
            "content-encoding",
            "content-length",
            "transfer-encoding",
            "connection",
        }

        headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() not in ignored_headers
        }

        if download and "Content-Disposition" not in headers:
            headers["Content-Disposition"] = f'attachment; filename="{os.path.basename(filename)}"'

        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/octet-stream"

        return response.content, response.status_code, headers

    except requests.RequestException as error:
        return str(error).encode("utf-8"), 503, {
            "Content-Type": "text/plain; charset=utf-8"
        }


def _build_files_payload(uploaded_files):
    files = []

    for uploaded_file in uploaded_files or []:
        if not uploaded_file or not uploaded_file.filename:
            continue

        try:
            uploaded_file.stream.seek(0)
        except Exception:
            pass

        files.append((
            "files",
            (
                uploaded_file.filename,
                uploaded_file.stream,
                uploaded_file.mimetype or "application/octet-stream",
            )
        ))

    return files


def _extract_items(payload):
    if not isinstance(payload, dict):
        return []

    items = payload.get("items")

    if isinstance(items, list):
        return items

    data = payload.get("data")

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        nested_items = data.get("items")

        if isinstance(nested_items, list):
            return nested_items

        nested_assets = data.get("assets")

        if isinstance(nested_assets, list):
            return nested_assets

    assets = payload.get("assets")

    if isinstance(assets, list):
        return assets

    return []


def _extract_data(payload):
    if not isinstance(payload, dict):
        return {}

    data = payload.get("data")

    if isinstance(data, dict):
        return data

    return {}


def _extract_pagination(payload):
    if not isinstance(payload, dict):
        return {}

    pagination = payload.get("pagination")

    if isinstance(pagination, dict):
        return pagination

    data = payload.get("data")

    if isinstance(data, dict) and isinstance(data.get("pagination"), dict):
        return data.get("pagination")

    return {}


def _normalize_asset(item):
    if not isinstance(item, dict):
        item = {}

    asset_id = _clean(_first(item, "id", "_id", "asset_id", "value"))
    asset_code = _clean(_first(item, "asset_code", "code"))
    asset_name = _clean(_first(item, "asset_name", "asset", "name"))

    value = _clean(_first(item, "value", "id", "_id", "asset_id", "asset_code", "code"))
    label = _clean(item.get("label"))

    if not label:
        if asset_code and asset_name:
            label = f"{asset_code} - {asset_name}"
        else:
            label = asset_name or asset_code or value

    return {
        "id": asset_id or asset_code,
        "value": value or asset_id or asset_code,
        "code": asset_code,
        "asset_code": asset_code,
        "name": asset_name,
        "asset_name": asset_name,
        "label": label,
        "type": _clean(_first(item, "type", "category")),
        "category": _clean(_first(item, "category", "type")),
        "department": _clean(_first(item, "department", "dept")),
        "location": _clean(_first(item, "location", "floor", "place")),
        "status": _clean(item.get("status")),
        "user": _clean(_first(item, "user", "receiver")),
        "receiver": _clean(_first(item, "receiver", "user")),
        "employee_code": _clean(item.get("employee_code")),
    }


def _asset_text(asset):
    return _norm(
        f"{asset.get('code')} {asset.get('asset_code')} "
        f"{asset.get('name')} {asset.get('asset_name')}"
    )


def _assets_from_report_assets(assets, *keys):
    values = []

    if not isinstance(assets, list):
        return values

    for asset in assets:
        if not isinstance(asset, dict):
            continue

        for key in keys:
            value = asset.get(key)

            if value not in [None, ""]:
                values.append(value)
                break

    return values


def normalize_report(item, index=0):
    if not isinstance(item, dict):
        item = {}

    report_id = _clean(_first(item, "id", "_id", "report_code", default=str(index)))

    report_code = _clean(
        _first(
            item,
            "report_code",
            "code",
            "id",
            default=f"Report-{index + 1:06d}",
        )
    )

    report_name = _clean(
        _first(
            item,
            "report_name",
            "title",
            "name",
            default="Báo cáo chưa có tên",
        )
    )

    report_type = _clean(_first(item, "report_type", "type", default="Khác"))
    report_status = _clean(_first(item, "status", "report_status", default="Chờ xử lý"))

    asset_name = _clean(
        _first(
            item,
            "asset_name",
            "asset",
            default="Chưa xác định",
        )
    ) or "Chưa xác định"

    asset_code = _clean(_first(item, "asset_code", "code"))

    asset_names = _join_values(
        item.get("asset_names")
        or _assets_from_report_assets(item.get("assets"), "asset_name", "asset", "name")
    )

    asset_codes = _join_values(
        item.get("asset_codes")
        or _assets_from_report_assets(item.get("assets"), "asset_code", "code")
    )

    asset_ids = _join_values(
        item.get("asset_ids")
        or _assets_from_report_assets(item.get("assets"), "asset_id", "id", "_id")
    )

    reporter = _clean(
        _first(
            item,
            "reporter",
            "user",
            "receiver",
            "created_by",
        )
    )

    reporter_role = _clean(_first(item, "reporter_role", "role"))
    department = _clean(_first(item, "department", "dept"))
    location = _clean(_first(item, "location", "floor", "place"))
    description = _clean(_first(item, "description", "detail", "content"))
    note = _clean(_first(item, "note", "approval_note", "cancel_reason"))
    created_time = _clean(_first(item, "time", "created_at", "date"))

    item["_row_index"] = report_id
    item["row_index"] = report_id
    item["report_id"] = report_id

    item["display_report_code"] = report_code
    item["display_report_name"] = report_name
    item["display_report_type"] = report_type
    item["display_report_status"] = report_status
    item["display_priority"] = _clean(item.get("priority")) or "Bình thường"

    item["display_reporter"] = reporter
    item["display_reporter_role"] = reporter_role

    item["display_created_by"] = _clean(item.get("approved_by")) or _clean(item.get("created_by")) or reporter
    item["display_created_by_role"] = _clean(item.get("created_by_role")) or reporter_role

    item["display_department"] = department
    item["display_location"] = location

    item["display_asset_name"] = asset_names or asset_name
    item["display_asset_code"] = asset_codes or asset_code

    item["asset_ids"] = asset_ids
    item["asset_codes"] = asset_codes
    item["asset_names"] = asset_names

    item["display_detail"] = description
    item["display_note"] = note
    item["display_time"] = created_time

    item["can_approve"] = report_status in ["Chờ xử lý", "Đang xử lý"]
    item["can_cancel"] = report_status in ["Chờ xử lý", "Đang xử lý"]
    item["can_delete"] = report_status != "Hoàn thành"

    item["files"] = _normalize_report_files(item.get("files", []))

    return item


def api_get_report_options():
    return _api_request("GET", "/api/reports/options")


def api_get_my_asset_options(params=None):
    return _api_request(
        "GET",
        "/api/reports/assets/options",
        params=params or {},
    )


def api_get_reports(params=None):
    return _api_request(
        "GET",
        "/api/reports",
        params=params or {},
    )


def api_get_report_detail(report_id):
    return _api_request(
        "GET",
        f"/api/reports/{report_id}",
    )


def api_create_report(form_data, uploaded_files=None):
    data = _build_report_form_payload(form_data)

    if data.get("report_code") in ["Report-000000", "REPORT-000000"]:
        data.pop("report_code", None)

    files = _build_files_payload(uploaded_files)

    return _api_request(
        "POST",
        "/api/reports",
        data=data,
        files=files or None,
    )


def api_delete_report(report_id):
    return _api_request(
        "DELETE",
        f"/api/reports/{report_id}",
    )


def api_approve_report(report_id, data=None):
    return _api_request(
        "POST",
        f"/api/reports/{report_id}/approve",
        json_data=data or {},
    )


def api_cancel_report(report_id, data=None):
    return _api_request(
        "POST",
        f"/api/reports/{report_id}/cancel",
        json_data=data or {},
    )


def api_delete_report_file(report_id, file_id):
    return _api_request(
        "DELETE",
        f"/api/reports/{report_id}/files/{file_id}",
    )


def _get_asset_options(report_type=None, search="", page=1, limit=10):
    params = {
        "page": _safe_int(page, default=1),
        "limit": _safe_int(limit, default=10, max_value=100),
    }

    report_type = _clean(report_type)

    if report_type:
        params["report_type"] = report_type

    search = _clean(search)

    if search:
        params["search"] = search
        params["q"] = search

    success, payload, _ = api_get_my_asset_options(params)

    if not success:
        return [], {}, payload.get("message", "Không lấy được danh sách tài sản.")

    items = [
        _normalize_asset(item)
        for item in _extract_items(payload)
        if isinstance(item, dict)
    ]

    return items, _extract_pagination(payload), ""


def _get_options(report_type=None):
    success, payload, _ = api_get_report_options()

    if not success:
        payload = {}

    data = _extract_data(payload)

    report_types = data.get("report_types") or data.get("types") or REPORT_DEFAULT_TYPES
    statuses = data.get("statuses") or REPORT_DEFAULT_STATUSES
    reporter_roles = data.get("reporter_roles") or DEFAULT_ROLE_OPTIONS

    default_report_type = report_type or (report_types[0] if report_types else "Báo hỏng")
    asset_options, asset_pagination, asset_error = _get_asset_options(
        report_type=default_report_type,
        page=1,
        limit=10,
    )

    return {
        "report_type_options": _unique(report_types),
        "report_status_options": _unique(statuses),
        "reporter_role_options": _unique(reporter_roles),
        "role_options": _unique(reporter_roles),
        "asset_options": asset_options,
        "asset_pagination": asset_pagination,
        "asset_option_error": asset_error,
        "asset_option_endpoint": "/report/assets/search",
        "allowed_file_extensions": data.get("allowed_file_extensions", []),
    }


def _get_all_reports_for_options():
    success, payload, _ = api_get_reports({
        "page": 1,
        "limit": 10,
    })

    if not success:
        return []

    return [
        normalize_report(item, index)
        for index, item in enumerate(_extract_items(payload))
    ]


def _generate_preview_report_id():
    reports = _get_all_reports_for_options()
    max_number = 0

    for report in reports:
        code = _clean(report.get("report_code") or report.get("display_report_code"))
        match = re.search(r"Report-(\d+)", code)

        if match:
            max_number = max(max_number, int(match.group(1)))

    return f"Report-{max_number + 1:06d}"


def _build_api_report_params(args):
    search_q = args.get("search", "").strip()
    selected_type = args.get("type", args.get("report_type", "Tất cả"))
    selected_dept = args.get("department", "Tất cả")
    selected_location = args.get("location", "Tất cả")
    selected_status = args.get("status", "Tất cả")

    page = max(1, args.get("page", 1, type=int))
    per_page = max(1, args.get("per_page", args.get("limit", 10), type=int))

    params = {
        "page": page,
        "limit": per_page,
    }

    if search_q:
        params["search"] = search_q

    if selected_type and selected_type != "Tất cả":
        params["report_type"] = selected_type

    if selected_dept and selected_dept != "Tất cả":
        params["department"] = selected_dept

    if selected_location and selected_location != "Tất cả":
        params["location"] = selected_location

    if selected_status and selected_status != "Tất cả":
        params["status"] = selected_status

    return params


def get_report_page_data(args):
    search_q = args.get("search", "").strip()
    selected_type = args.get("type", args.get("report_type", "Tất cả"))
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

    params = _build_api_report_params(args)
    success, payload, _ = api_get_reports(params)

    reports = []
    pagination = {}
    api_error = ""

    if success:
        reports = [
            normalize_report(item, index)
            for index, item in enumerate(_extract_items(payload))
        ]
        pagination = _extract_pagination(payload)
    else:
        api_error = payload.get("message", "Không lấy được danh sách báo cáo.")

    options = _get_options()
    all_reports = _get_all_reports_for_options()

    if not all_reports:
        all_reports = reports

    department_options = _unique([
        report.get("display_department")
        for report in all_reports
    ])

    location_options = _unique([
        report.get("display_location")
        for report in all_reports
    ])

    type_counts = Counter(
        report.get("display_report_type") or "Khác"
        for report in all_reports
    )

    department_counts = Counter(
        report.get("display_department")
        for report in all_reports
        if report.get("display_department")
    )

    location_counts = Counter(
        report.get("display_location")
        for report in all_reports
        if report.get("display_location")
    )

    status_counts = Counter(
        report.get("display_report_status") or "Chờ xử lý"
        for report in all_reports
    )

    current_page = int(
        pagination.get("page")
        or pagination.get("current_page")
        or params.get("page")
        or 1
    )

    per_page = int(
        pagination.get("per_page")
        or pagination.get("limit")
        or params.get("limit")
        or 10
    )

    total_records = int(
        pagination.get("total_items")
        or pagination.get("total")
        or payload.get("total", 0)
        if isinstance(payload, dict)
        else 0
    )

    if not total_records and reports:
        total_records = len(reports)

    total_pages = int(
        pagination.get("total_pages")
        or 1
    )

    return {
        "reports": reports,
        "logs": reports,
        "report_logs": reports,

        "total_records": total_records,
        "total_logs": total_records,
        "total_report_count": len(all_reports),

        "current_page": current_page,
        "total_pages": total_pages,
        "per_page": per_page,

        "search_q": search_q,
        "search_query": search_q,
        "search_value": search_q,

        "selected_type": selected_type,
        "selected_dept": selected_dept,
        "selected_location": selected_location,
        "selected_status": selected_status,
        "has_active_filter": has_active_filter,

        "type_counts": type_counts,
        "department_counts": department_counts,
        "location_counts": location_counts,
        "status_counts": status_counts,

        "department_options": department_options,
        "location_options": location_options,

        "api_error": api_error,

        **options,
    }


def get_create_page_data():
    current_user_name = _current_user_name()
    current_user_role = _current_user_role()
    current_user_department = _current_user_department()
    current_user_location = _current_user_location()

    return {
        "current_time": _now_text(),
        "auto_report_id": _generate_preview_report_id(),

        "current_admin_name": current_user_name,
        "current_admin_role": current_user_role,

        "current_user_name": current_user_name,
        "current_user_role": current_user_role,
        "current_user_department": current_user_department,
        "current_user_location": current_user_location,

        "department_options": [],
        "location_options": [],

        **_get_options("Báo hỏng"),
    }


def create_report_from_form(form, uploaded_files=None):
    success, payload, status_code = api_create_report(form, uploaded_files)

    if not success:
        return False, payload.get("message", "Tạo báo cáo không thành công."), None, status_code

    return True, payload.get("message", "Tạo báo cáo thành công."), payload.get("data"), status_code


def get_report_detail_page_data(report_id):
    success, payload, status_code = api_get_report_detail(report_id)

    if not success:
        return None, payload.get("message", "Không tìm thấy báo cáo."), status_code

    report = normalize_report(payload.get("data") or {}, 0)

    return report, None, status_code


def delete_report(report_id):
    success, payload, status_code = api_delete_report(report_id)

    if not success:
        return False, payload.get("message", "Không tìm thấy báo cáo cần xóa."), "warning", status_code

    return True, payload.get("message", "Xóa báo cáo thành công."), "danger", status_code


def approve_report(report_id, data=None):
    success, payload, status_code = api_approve_report(report_id, data)

    if not success:
        return False, payload.get("message", "Duyệt báo cáo không thành công."), payload, status_code

    return True, payload.get("message", "Duyệt báo cáo thành công."), payload, status_code


def cancel_report(report_id, data=None):
    success, payload, status_code = api_cancel_report(report_id, data)

    if not success:
        return False, payload.get("message", "Hủy báo cáo không thành công."), payload, status_code

    return True, payload.get("message", "Hủy báo cáo thành công."), payload, status_code


def delete_file(report_id, file_id):
    success, payload, status_code = api_delete_report_file(report_id, file_id)

    if not success:
        return False, payload.get("message", "Xóa file không thành công."), payload, status_code

    return True, payload.get("message", "Xóa file thành công."), payload, status_code


def search_report_assets(keyword="", report_type="", page=1, limit=10):
    keyword = _clean(keyword)
    report_type = _clean(report_type) or "Báo hỏng"
    page = _safe_int(page, default=1)
    limit = _safe_int(limit, default=10, max_value=50)

    params = {
        "report_type": report_type,
        "page": page,
        "limit": limit,
    }

    if keyword:
        params["search"] = keyword
        params["q"] = keyword

    success, payload, status_code = api_get_my_asset_options(params)

    if not success:
        return {
            "success": False,
            "items": [],
            "assets": [],
            "data": [],
            "pagination": {},
            "message": payload.get("message", "Không lấy được danh sách tài sản."),
            "status_code": status_code,
        }

    results = []
    seen = set()

    for item in _extract_items(payload):
        asset = _normalize_asset(item)
        key = _norm(asset.get("value") or asset.get("id") or asset.get("code") or asset.get("name"))

        if not key or key in seen:
            continue

        if keyword and _norm(keyword) not in _asset_text(asset):
            continue

        seen.add(key)
        results.append(asset)

    pagination = _extract_pagination(payload)

    return {
        "success": True,
        "items": results[:limit],
        "assets": results[:limit],
        "data": results[:limit],
        "pagination": pagination,
        "report_type": report_type,
        "message": payload.get("message", "Lấy danh sách tài sản thành công."),
    }