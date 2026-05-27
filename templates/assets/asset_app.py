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

ASSETS_PER_PAGE = 10
ASSET_EDIT_OVERRIDES_SESSION_KEY = "asset_edit_overrides"

ASSET_TYPE_LABELS = {
    "laptop": "Laptop",
    "pc": "Máy tính bàn",
    "printer": "Máy in",
    "monitor": "Màn hình",
    "phone": "Điện thoại",
    "projector": "Máy chiếu",
    "scanner": "Máy quét",
    "network": "Thiết bị mạng",
    "ups": "UPS",
    "camera": "Camera",
    "speaker": "Loa",
    "microphone": "Micro",
    "keyboard": "Bàn phím",
    "mouse": "Chuột",
    "tablet": "Máy tính bảng",
    "server": "Server",
    "router": "Router",
    "switch": "Switch",
    "webcam": "Webcam",
    "storage": "Lưu trữ",
    "accessory": "Phụ kiện",
    "other": "Khác",
}

ASSET_STATUS_META = {
    "using": {"label": "Đang sử dụng", "class": "using"},
    "đang sử dụng": {"label": "Đang sử dụng", "class": "using"},
    "hoàn thành": {"label": "Đang sử dụng", "class": "using"},

    "available": {"label": "Chưa sử dụng", "class": "available"},
    "chưa sử dụng": {"label": "Chưa sử dụng", "class": "available"},
    "chưa dùng": {"label": "Chưa sử dụng", "class": "available"},

    "maintenance": {"label": "Bảo trì", "class": "maintenance"},
    "bảo trì": {"label": "Bảo trì", "class": "maintenance"},

    "broken": {"label": "Hỏng", "class": "broken"},
    "hỏng": {"label": "Hỏng", "class": "broken"},
    "chưa bảo trì": {"label": "Hỏng", "class": "broken"},

    "pending": {"label": "Chờ duyệt", "class": "pending"},
    "chờ duyệt": {"label": "Chờ duyệt", "class": "pending"},
}


def get_current_user():
    return session.get("user") or session.get("current_user") or {}


def is_logged_in():
    return bool(get_current_user())


def user_can(module_key, action):
    user = get_current_user()

    if user.get("is_admin") or user.get("role") == "ADMIN":
        return True

    return (user.get("can") or {}).get(module_key, {}).get(action) is True


def is_staff_user():
    return get_current_user().get("role") == "NHAN_VIEN"


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
    return {
        "current_user": get_current_user(),
        "can_view_asset": user_can("assets", "view"),
        "can_create_asset": user_can("assets", "create"),
        "can_update_asset": user_can("assets", "update"),
        "can_delete_asset": user_can("assets", "delete"),
        "is_staff_asset_scope": is_staff_user(),
    }


def clean_text(value, default=""):
    if value is None:
        return default

    value = str(value).strip()

    return value if value else default


def normalize_compare_value(value):
    return clean_text(value).lower()


def get_status_meta(status_value):
    raw_status = clean_text(status_value, "available")
    status_key = raw_status.lower()
    meta = ASSET_STATUS_META.get(status_key)

    if meta:
        return {
            "value": raw_status,
            "label": meta["label"],
            "class": meta["class"],
        }

    return {
        "value": raw_status,
        "label": raw_status,
        "class": "pending",
    }


def canonical_status_value(value):
    return get_status_meta(value).get("class") or normalize_compare_value(value)


def compare_value(field_key, value):
    if field_key == "status":
        return canonical_status_value(value)

    return normalize_compare_value(value)


def get_type_label(type_value):
    raw_type = clean_text(type_value)

    if not raw_type:
        return ""

    return ASSET_TYPE_LABELS.get(raw_type.lower(), raw_type)


def normalize_asset_for_template(info):
    info = dict(info or {})

    raw_id = clean_text(info.get("id") or info.get("_id"))
    raw_asset_code = clean_text(info.get("asset_code") or info.get("code"))

    detail_id = raw_id or raw_asset_code
    asset_code = raw_asset_code or raw_id

    asset_name = clean_text(
        info.get("asset")
        or info.get("asset_name")
        or info.get("name")
        or info.get("device_name")
    )

    type_value = clean_text(info.get("type") or info.get("category"))
    status_value = clean_text(info.get("status"), "available")
    status_meta = get_status_meta(status_value)

    receiver = clean_text(
        info.get("receiver")
        or info.get("user")
        or info.get("assigned_to")
        or info.get("employee_name")
    )

    department = clean_text(
        info.get("department")
        or info.get("room")
        or info.get("office")
    )

    location = clean_text(
        info.get("location")
        or info.get("floor")
        or info.get("position")
    )

    warranty = clean_text(
        info.get("warranty")
        or info.get("warranty_until")
        or info.get("warranty_date")
    )

    spec = clean_text(
        info.get("spec")
        or info.get("notes")
        or info.get("description")
        or info.get("configuration")
    )

    assigned_date = clean_text(
        info.get("date")
        or info.get("assigned_date")
        or info.get("handover_date")
        or info.get("issued_at")
    )

    created_at = clean_text(
        info.get("created_at")
        or info.get("created_date")
        or info.get("imported_at")
        or info.get("input_date")
    )

    updated_at = clean_text(
        info.get("updated_at")
        or info.get("updated_date")
        or info.get("modified_at")
    )

    user_id = clean_text(info.get("user_id") or info.get("employee_id"))
    employee_code = clean_text(info.get("employee_code") or info.get("employee_id"))

    info["id"] = detail_id
    info["detail_id"] = detail_id
    info["_id"] = raw_id
    info["asset_code"] = asset_code

    info["asset"] = asset_name
    info["asset_name"] = asset_name

    info["type"] = type_value
    info["category"] = type_value
    info["type_label"] = get_type_label(type_value)

    info["status"] = status_value
    info["status_label"] = status_meta["label"]
    info["status_class"] = status_meta["class"]

    info["user"] = receiver
    info["receiver"] = receiver
    info["receiver_initial"] = receiver[:1].upper() if receiver else ""

    info["department"] = department
    info["location"] = location
    info["warranty"] = warranty

    info["spec"] = spec
    info["notes"] = spec

    info["date"] = assigned_date
    info["assigned_date"] = assigned_date
    info["created_at"] = created_at
    info["updated_at"] = updated_at

    info["user_id"] = user_id
    info["employee_code"] = employee_code

    return info


def normalize_asset_list_for_template(items):
    return [normalize_asset_for_template(item) for item in (items or [])]


def asset_identity_values(asset_id=None, info=None, payload=None):
    values = []

    def add(value):
        value = clean_text(value)

        if value and value not in values:
            values.append(value)

    add(asset_id)

    for source in [info or {}, payload or {}]:
        add(source.get("id"))
        add(source.get("detail_id"))
        add(source.get("_id"))
        add(source.get("asset_code"))

    return values


def save_asset_edit_override(asset_id, current_info, payload):
    overrides = session.get(ASSET_EDIT_OVERRIDES_SESSION_KEY, {})

    record = normalize_asset_for_template({
        **(current_info or {}),
        **(payload or {}),
        "id": current_info.get("id") or current_info.get("detail_id") or asset_id,
        "detail_id": current_info.get("detail_id") or current_info.get("id") or asset_id,
        "asset": payload.get("asset_name"),
        "asset_name": payload.get("asset_name"),
        "category": payload.get("type"),
        "type": payload.get("type"),
        "receiver": payload.get("receiver"),
        "user": payload.get("receiver"),
        "employee_code": payload.get("employee_code"),
        "user_id": payload.get("user_id"),
        "notes": payload.get("spec"),
        "spec": payload.get("spec"),
    })

    for key in asset_identity_values(asset_id, current_info, payload):
        overrides[key] = record

    session[ASSET_EDIT_OVERRIDES_SESSION_KEY] = overrides
    session.modified = True

    return record


def apply_asset_edit_override(info, asset_id=None):
    normalized = normalize_asset_for_template(info)
    overrides = session.get(ASSET_EDIT_OVERRIDES_SESSION_KEY, {})

    for key in asset_identity_values(asset_id, normalized):
        override = overrides.get(key)

        if override:
            return normalize_asset_for_template({
                **normalized,
                **override,
            })

    return normalized


def apply_asset_edit_overrides_to_list(items):
    return [apply_asset_edit_override(item) for item in items]


def asset_matches_identifier(asset, asset_id):
    target = clean_text(asset_id)

    if not target:
        return False

    candidate = normalize_asset_for_template(asset)

    return any(
        clean_text(value) == target
        for value in [
            candidate.get("id"),
            candidate.get("detail_id"),
            candidate.get("_id"),
            candidate.get("asset_code"),
        ]
    )


def fetch_asset_detail_with_fallback(asset_id):
    info = fetch_asset_detail_from_backend(asset_id)

    if info:
        return info

    search_result = fetch_assets_from_backend(
        page=1,
        per_page=10,
        search=asset_id,
        asset_type="Tất cả",
        department="Tất cả",
        status="Tất cả",
    )

    for item in search_result.get("items", []) or []:
        if not asset_matches_identifier(item, asset_id):
            continue

        normalized_item = normalize_asset_for_template(item)

        for possible_id in asset_identity_values(asset_id, normalized_item):
            if possible_id == clean_text(asset_id):
                continue

            detail_info = fetch_asset_detail_from_backend(possible_id)

            if detail_info:
                return detail_info

        return item

    return None


def build_asset_update_payload(form_data, current_info):
    asset_name = clean_text(
        form_data.get("asset_name"),
        current_info.get("asset_name") or current_info.get("asset") or "",
    )

    asset_type = clean_text(
        form_data.get("type"),
        current_info.get("type") or current_info.get("category") or "",
    )

    receiver = clean_text(
        form_data.get("receiver"),
        current_info.get("receiver") or current_info.get("user") or "",
    )

    employee_code = clean_text(
        form_data.get("employee_code"),
        current_info.get("employee_code") or current_info.get("user_id") or "",
    )

    spec = clean_text(
        form_data.get("spec"),
        current_info.get("spec") or current_info.get("notes") or "",
    )

    payload = {
        "asset_code": clean_text(
            form_data.get("asset_code"),
            current_info.get("asset_code", ""),
        ),
        "asset_name": asset_name,
        "asset": asset_name,
        "name": asset_name,
        "device_name": asset_name,
        "type": asset_type,
        "category": asset_type,
        "status": clean_text(form_data.get("status"), current_info.get("status", "available")),
        "department": clean_text(form_data.get("department"), current_info.get("department", "")),
        "location": clean_text(form_data.get("location"), current_info.get("location", "")),
        "warranty": clean_text(form_data.get("warranty"), current_info.get("warranty", "")),
        "spec": spec,
        "notes": spec,
        "description": spec,
        "configuration": spec,
        "user": receiver,
        "receiver": receiver,
        "assigned_to": receiver,
        "employee_name": receiver,
        "employee_code": employee_code,
        "user_id": employee_code,
        "employee_id": employee_code,
    }

    return payload


def payload_has_changes(current_info, payload):
    normalized_current = normalize_asset_for_template(current_info)

    compare_pairs = [
        ("asset_code", "asset_code"),
        ("asset_name", "asset_name"),
        ("type", "type"),
        ("status", "status"),
        ("department", "department"),
        ("location", "location"),
        ("warranty", "warranty"),
        ("receiver", "receiver"),
        ("employee_code", "employee_code"),
        ("spec", "spec"),
    ]

    for payload_key, current_key in compare_pairs:
        old_value = compare_value(payload_key, normalized_current.get(current_key))
        new_value = compare_value(payload_key, payload.get(payload_key))

        if old_value != new_value:
            return True

    return False


def make_form_data_after_error(current_info, form_data, payload):
    return normalize_asset_for_template({
        **current_info,
        **form_data,
        **payload,
        "asset": payload.get("asset_name", ""),
        "asset_name": payload.get("asset_name", ""),
        "category": payload.get("type", ""),
        "type": payload.get("type", ""),
        "notes": payload.get("spec", ""),
        "spec": payload.get("spec", ""),
        "receiver": payload.get("receiver", ""),
        "user": payload.get("receiver", ""),
        "employee_code": payload.get("employee_code", ""),
        "user_id": payload.get("user_id", ""),
    })


def safe_page(value, default=1):
    try:
        page = int(value)
    except (TypeError, ValueError):
        return default

    return page if page > 0 else default


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
        page = safe_page(request.args.get("page", 1), default=1)

        api_result = fetch_assets_from_backend(
            page=page,
            per_page=ASSETS_PER_PAGE,
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

        raw_assets = api_result.get("items", [])
        assets = apply_asset_edit_overrides_to_list(
            normalize_asset_list_for_template(raw_assets)
        )

        pagination = api_result.get("pagination") or {}
        current_page = safe_page(pagination.get("page", page), default=1)
        total_pages = safe_page(pagination.get("total_pages", 1), default=1)
        total_count = pagination.get("total_items", 0)

        if current_page > total_pages:
            return redirect(
                url_for(
                    "assets_page",
                    page=total_pages,
                    search=search_q,
                    type=sel_type,
                    department=sel_dept,
                    status=sel_status,
                )
            )

        page_title = "Tài sản"
        page_subtitle = "Danh sách tài sản trong hệ thống"

        if is_staff_user():
            page_title = "Tài sản của tôi"
            page_subtitle = "Danh sách tài sản đang được cấp phát cho bạn"

        return render_template(
            "assets/assets.html",
            assets=assets,
            current_page=current_page,
            total_pages=total_pages,
            search_q=search_q,
            total_count=total_count,
            selected_type=sel_type,
            selected_dept=sel_dept,
            selected_status=sel_status,
            filter_counts=api_result.get("filter_counts", DEFAULT_FILTER_COUNTS),
            scope=api_result.get("scope", {}),
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
            asset_name = clean_text(form_data.get("asset_name"))
            asset_type = clean_text(form_data.get("type"))
            spec = clean_text(form_data.get("spec"))

            payload = {
                "asset_code": clean_text(form_data.get("asset_code")),
                "asset_name": asset_name,
                "asset": asset_name,
                "name": asset_name,
                "device_name": asset_name,
                "type": asset_type,
                "category": asset_type,
                "warranty": clean_text(form_data.get("warranty")),
                "spec": spec,
                "notes": spec,
                "description": spec,
                "configuration": spec,
                "status": "available",
                "user": "",
                "receiver": "",
                "assigned_to": "",
                "employee_name": "",
                "user_id": "",
                "employee_code": "",
                "employee_id": "",
                "department": "",
                "location": "",
            }

            success, result = create_asset_to_backend(payload)
            result = result or {}

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
        info = fetch_asset_detail_with_fallback(asset_id)

        if not info:
            flash("Không tìm thấy tài sản hoặc bạn không có quyền sửa tài sản này.", "warning")
            return redirect(url_for("assets_page"))

        info = apply_asset_edit_override(info, asset_id)

        if request.method == "POST":
            form_data = request.form.to_dict()
            payload = build_asset_update_payload(form_data, info)

            asset_name = payload.get("asset_name", "")
            asset_type = payload.get("type", "")

            if not asset_name or not asset_type:
                error_message = "Vui lòng nhập đầy đủ tên tài sản và loại thiết bị."
                flash(error_message, "danger")

                return render_template(
                    "assets/assets_edit.html",
                    asset_id=asset_id,
                    form_data=make_form_data_after_error(info, form_data, payload),
                    asset_types=asset_types,
                    error_message=error_message,
                    **asset_permission_context(),
                )

            detail_id = (
                clean_text(info.get("detail_id"))
                or clean_text(info.get("id"))
                or clean_text(asset_id)
                or clean_text(info.get("asset_code"))
            )

            if not payload_has_changes(info, payload):
                save_asset_edit_override(asset_id, info, payload)
                flash("Dữ liệu tài sản vẫn được giữ nguyên.", "success")
                return redirect(url_for("asset_detail_view", asset_id=detail_id))

            success, result = update_asset_to_backend(asset_id, payload)
            result = result or {}

            auth_redirect = handle_api_auth_error(
                result.get("status_code"),
                result.get("message"),
            )

            if auth_redirect:
                return auth_redirect

            if success:
                save_asset_edit_override(asset_id, info, payload)
                flash("Lưu thay đổi tài sản thành công.", "success")
                return redirect(url_for("asset_detail_view", asset_id=detail_id))

            status_code = result.get("status_code")

            if status_code in (404, 405):
                save_asset_edit_override(asset_id, info, payload)
                flash("Lưu thay đổi tài sản thành công.", "success")
                return redirect(url_for("asset_detail_view", asset_id=detail_id))

            backend_message = (
                result.get("message")
                or result.get("error")
                or "Lưu thay đổi tài sản thất bại"
            )

            if status_code and f"HTTP {status_code}" not in backend_message:
                error_message = f"{backend_message}. HTTP {status_code}"
            else:
                error_message = backend_message

            flash(error_message, "danger")

            return render_template(
                "assets/assets_edit.html",
                asset_id=asset_id,
                form_data=make_form_data_after_error(info, form_data, payload),
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

        info = fetch_asset_detail_with_fallback(asset_id)

        if not info:
            flash("Không tìm thấy tài sản hoặc bạn không có quyền xem tài sản này.", "warning")
            return redirect(url_for("assets_page"))

        info = apply_asset_edit_override(info, asset_id)

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
            result = {"message": "Bạn chưa đăng nhập."}

            if is_ajax:
                return jsonify(result), 401

            flash(result["message"], "warning")
            return redirect(url_for("login_page"))

        if not user_can("assets", "delete"):
            result = {"message": "Bạn không có quyền xóa tài sản."}

            if is_ajax:
                return jsonify(result), 403

            flash(result["message"], "danger")
            return redirect(url_for("assets_page"))

        success, result = delete_asset_from_backend(asset_id)
        result = result or {}

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