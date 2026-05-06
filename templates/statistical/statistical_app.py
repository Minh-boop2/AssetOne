from collections import Counter
from flask import render_template

from data import (
    ASSIGN_DATA,
    USER_LIST_DATA,
    DATABASE_LOGS,
    get_statistical_fake_data,
)


def format_number(value):
    return f"{value:,}".replace(",", ".")


def format_money(value):
    return f"{value:,.0f}".replace(",", ".") + "đ"


def percent(value, total):
    if total == 0:
        return 0
    return round((value / total) * 100, 1)


def safe_bar_percent(value, max_value):
    if max_value == 0:
        return 0

    result = round((value / max_value) * 100, 1)
    return max(result, 6)


def build_segments(items):
    total = sum(item["value"] for item in items)
    current_degree = 0

    for item in items:
        degree = (item["value"] / total) * 360 if total else 0
        item["percent"] = percent(item["value"], total)
        item["from_deg"] = round(current_degree, 2)
        item["to_deg"] = round(current_degree + degree, 2)
        current_degree += degree

    return items


def get_status_class(status):
    status_map = {
        "Hoàn thành": "success",
        "Chờ duyệt": "warning",
        "Đang xử lý": "info",
        "Đã từ chối": "danger",
        "Hoạt động": "success",
        "Ngưng hoạt động": "danger",
    }

    return status_map.get(status, "info")


def build_money_data():
    statistical_data = get_statistical_fake_data()

    finance_summary = statistical_data["finance_summary"]
    finance_months = statistical_data["finance_months"]
    finance_segments = statistical_data["finance_segments"]
    revenue_sources = statistical_data["revenue_sources"]
    expense_categories = statistical_data["expense_categories"]
    financial_reports = statistical_data["financial_reports"]

    finance_cards = [
        {
            "title": "Doanh thu",
            "value": finance_summary["total_revenue_text"],
            "icon": "💰",
            "class": "purple",
            "desc": "Tổng tiền thu được trong hệ thống",
        },
        {
            "title": "Chi phí",
            "value": finance_summary["total_cost_text"],
            "icon": "💳",
            "class": "cyan",
            "desc": "Tổng chi phí vận hành và xử lý",
        },
        {
            "title": "Tiền lời",
            "value": finance_summary["total_profit_text"],
            "icon": "📈",
            "class": "green",
            "desc": "Lợi nhuận sau khi trừ chi phí",
        },
        {
            "title": "Tiền lỗ",
            "value": finance_summary["total_loss_text"],
            "icon": "📉",
            "class": "orange",
            "desc": "Tổn thất phát sinh trong hệ thống",
        },
    ]

    return {
        "finance_summary": finance_summary,
        "finance_months": finance_months,
        "finance_cards": finance_cards,
        "finance_segments": finance_segments,
        "revenue_sources": revenue_sources,
        "expense_categories": expense_categories,
        "financial_reports": financial_reports,
        "total_revenue_text": finance_summary["total_revenue_text"],
        "total_cost_text": finance_summary["total_cost_text"],
        "total_profit_text": finance_summary["total_profit_text"],
        "total_loss_text": finance_summary["total_loss_text"],
        "total_orders_text": finance_summary["total_orders_text"],
    }


def build_employees_data():
    total_users = len(USER_LIST_DATA)

    active_users = len([
        user for user in USER_LIST_DATA
        if user.get("status") == "Hoạt động"
    ])

    inactive_users = total_users - active_users

    role_counter = Counter(
        user.get("role", "Khác")
        for user in USER_LIST_DATA
    )

    dept_counter = Counter(
        user.get("dept", "Khác")
        for user in USER_LIST_DATA
    )

    role_max = max(role_counter.values()) if role_counter else 1
    dept_max = max(dept_counter.values()) if dept_counter else 1

    role_items = [
        {
            "label": key,
            "value": value,
            "value_text": format_number(value),
            "percent": safe_bar_percent(value, role_max),
        }
        for key, value in role_counter.items()
    ]

    dept_items = [
        {
            "label": key,
            "value": value,
            "value_text": format_number(value),
            "percent": safe_bar_percent(value, dept_max),
        }
        for key, value in list(dept_counter.items())[:6]
    ]

    employee_segments = build_segments([
        {
            "label": "Đang làm",
            "value": active_users,
            "value_text": format_number(active_users),
            "color": "#22c55e",
            "class": "green",
        },
        {
            "label": "Đã nghỉ",
            "value": inactive_users,
            "value_text": format_number(inactive_users),
            "color": "#ef4444",
            "class": "red",
        },
    ])

    recent_users = []
    for user in USER_LIST_DATA[-8:][::-1]:
        user_item = user.copy()
        user_item["status_class"] = get_status_class(user_item.get("status"))
        recent_users.append(user_item)

    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "employee_segments": employee_segments,
        "role_items": role_items,
        "dept_items": dept_items,
        "recent_users": recent_users,
    }


def build_assets_data():
    total_assets = len(ASSIGN_DATA)

    type_counter = Counter(
        item.get("type", "Khác")
        for item in ASSIGN_DATA
    )

    status_counter = Counter(
        item.get("status", "Khác")
        for item in ASSIGN_DATA
    )

    type_max = max(type_counter.values()) if type_counter else 1

    type_items = [
        {
            "label": key,
            "value": value,
            "value_text": format_number(value),
            "percent": safe_bar_percent(value, type_max),
        }
        for key, value in type_counter.items()
    ]

    colors = ["#22c55e", "#f97316", "#8b5cf6", "#ef4444", "#06b6d4"]
    classes = ["green", "orange", "purple", "red", "cyan"]

    status_segments = []

    for index, (key, value) in enumerate(status_counter.items()):
        status_segments.append({
            "label": key,
            "value": value,
            "value_text": format_number(value),
            "color": colors[index % len(colors)],
            "class": classes[index % len(classes)],
        })

    status_segments = build_segments(status_segments)

    recent_assets = []

    for item in ASSIGN_DATA[-8:][::-1]:
        asset = item.copy()
        asset["status_class"] = get_status_class(asset.get("status"))
        recent_assets.append(asset)

    # -------------------------------
    # THIẾT BỊ HƯ HỎNG / CẦN SỬA CHỮA
    # -------------------------------
    repair_issues = [
        "Không lên nguồn",
        "Màn hình bị sọc",
        "Lỗi kết nối mạng",
        "Kẹt giấy / lỗi in",
        "Pin chai nhanh",
        "Bàn phím không nhận",
        "Ổ cứng có dấu hiệu lỗi",
        "Thiết bị quá nhiệt",
    ]

    repair_levels = [
        {"name": "Nhẹ", "class": "light"},
        {"name": "Trung bình", "class": "medium"},
        {"name": "Nặng", "class": "heavy"},
    ]

    repair_statuses = [
        {"name": "Chờ kiểm tra", "class": "orange"},
        {"name": "Đang sửa chữa", "class": "purple"},
        {"name": "Chờ linh kiện", "class": "cyan"},
        {"name": "Hoàn tất sửa", "class": "green"},
    ]

    repair_source = [
        item for item in ASSIGN_DATA
        if item.get("status") in ["Đang xử lý", "Đã từ chối", "Chờ duyệt"]
    ]

    damaged_assets = []

    for index, item in enumerate(repair_source[:10]):
        repair_cost = 350000 + (index * 175000)
        level = repair_levels[index % len(repair_levels)]
        repair_status = repair_statuses[index % len(repair_statuses)]

        damaged_assets.append({
            "asset_code": item.get("asset_code"),
            "asset": item.get("asset"),
            "type": item.get("type"),
            "department": item.get("department"),
            "receiver": item.get("receiver"),
            "issue": repair_issues[index % len(repair_issues)],
            "level": level["name"],
            "level_class": level["class"],
            "repair_status": repair_status["name"],
            "repair_status_class": repair_status["class"],
            "repair_cost": repair_cost,
            "repair_cost_text": format_money(repair_cost),
        })

    total_damaged = len(damaged_assets)
    total_repair_cost = sum(item["repair_cost"] for item in damaged_assets)

    repair_level_counter = Counter(
        item["level"]
        for item in damaged_assets
    )

    repair_status_counter = Counter(
        item["repair_status"]
        for item in damaged_assets
    )

    repair_level_max = max(repair_level_counter.values()) if repair_level_counter else 1

    repair_level_items = [
        {
            "label": key,
            "value": value,
            "value_text": format_number(value),
            "percent": safe_bar_percent(value, repair_level_max),
        }
        for key, value in repair_level_counter.items()
    ]

    repair_status_colors = ["#f97316", "#8b5cf6", "#06b6d4", "#22c55e"]
    repair_status_classes = ["orange", "purple", "cyan", "green"]

    repair_status_segments = []

    for index, (key, value) in enumerate(repair_status_counter.items()):
        repair_status_segments.append({
            "label": key,
            "value": value,
            "value_text": format_number(value),
            "color": repair_status_colors[index % len(repair_status_colors)],
            "class": repair_status_classes[index % len(repair_status_classes)],
        })

    repair_status_segments = build_segments(repair_status_segments)

    return {
        "total_assets": total_assets,
        "type_items": type_items,
        "status_segments": status_segments,
        "recent_assets": recent_assets,

        "damaged_assets": damaged_assets,
        "total_damaged": total_damaged,
        "total_repair_cost": total_repair_cost,
        "total_repair_cost_text": format_money(total_repair_cost),
        "repair_level_items": repair_level_items,
        "repair_status_segments": repair_status_segments,
    }


def build_assign_data():
    total_assign = len(ASSIGN_DATA)

    status_counter = Counter(
        item.get("status", "Khác")
        for item in ASSIGN_DATA
    )

    dept_counter = Counter(
        item.get("department", "Khác")
        for item in ASSIGN_DATA
    )

    location_counter = Counter(
        item.get("location", "Khác")
        for item in ASSIGN_DATA
    )

    dept_max = max(dept_counter.values()) if dept_counter else 1
    location_max = max(location_counter.values()) if location_counter else 1

    colors = ["#22c55e", "#f97316", "#8b5cf6", "#ef4444", "#06b6d4"]
    classes = ["green", "orange", "purple", "red", "cyan"]

    status_segments = []

    for index, (key, value) in enumerate(status_counter.items()):
        status_segments.append({
            "label": key,
            "value": value,
            "value_text": format_number(value),
            "color": colors[index % len(colors)],
            "class": classes[index % len(classes)],
        })

    status_segments = build_segments(status_segments)

    dept_items = [
        {
            "label": key,
            "value": value,
            "value_text": format_number(value),
            "percent": safe_bar_percent(value, dept_max),
        }
        for key, value in list(dept_counter.items())[:7]
    ]

    location_items = [
        {
            "label": key,
            "value": value,
            "value_text": format_number(value),
            "percent": safe_bar_percent(value, location_max),
        }
        for key, value in list(location_counter.items())[:7]
    ]

    return {
        "assign_total": total_assign,
        "status_segments": status_segments,
        "dept_items": dept_items,
        "location_items": location_items,
    }


def build_report_data():
    total_logs = len(DATABASE_LOGS)

    log_counter = Counter(
        log.get("type", "Khác")
        for log in DATABASE_LOGS
    )

    status_counter = Counter(
        log.get("status", "Hoàn thành")
        for log in DATABASE_LOGS
    )

    log_max = max(log_counter.values()) if log_counter else 1
    status_max = max(status_counter.values()) if status_counter else 1

    log_items = [
        {
            "label": key,
            "value": value,
            "value_text": format_number(value),
            "percent": safe_bar_percent(value, log_max),
        }
        for key, value in log_counter.items()
    ]

    status_items = [
        {
            "label": key,
            "value": value,
            "value_text": format_number(value),
            "percent": safe_bar_percent(value, status_max),
        }
        for key, value in status_counter.items()
    ]

    colors = ["#8b5cf6", "#06b6d4", "#22c55e", "#f97316", "#ef4444"]
    classes = ["purple", "cyan", "green", "orange", "red"]

    log_segments = []

    for index, (key, value) in enumerate(log_counter.items()):
        log_segments.append({
            "label": key,
            "value": value,
            "value_text": format_number(value),
            "color": colors[index % len(colors)],
            "class": classes[index % len(classes)],
        })

    log_segments = build_segments(log_segments)

    recent_logs = []
    for log in DATABASE_LOGS[-8:][::-1]:
        recent_logs.append({
            "id": log.get("id", ""),
            "user": log.get("user", "Hệ thống"),
            "dept": log.get("dept", "Không rõ"),
            "action": log.get("action", log.get("type", "Cập nhật")),
            "asset": log.get("asset", log.get("asset_name", "Không rõ")),
            "type": log.get("type", "Khác"),
            "status": log.get("status", "Hoàn thành"),
            "time": log.get("time", ""),
        })

    return {
        "report_total": total_logs,
        "log_items": log_items,
        "status_items": status_items,
        "log_segments": log_segments,
        "recent_logs": recent_logs,
    }


def register_statistical_routes(app):
    @app.route("/statistical")
    def statistics_page():
        return render_template(
            "statistical/statistical.html",
            **build_money_data()
        )

    @app.route("/statistical/overview")
    def statistical_overview():
        return render_template(
            "statistical/statistical.html",
            **build_money_data()
        )

    @app.route("/statistical/employees")
    def statistical_employees():
        return render_template(
            "statistical/statistical_employees.html",
            **build_employees_data()
        )

    @app.route("/statistical/assets")
    def statistical_assets():
        return render_template(
            "statistical/statistical_assets.html",
            **build_assets_data()
        )

    @app.route("/statistical/assign")
    def statistical_assign():
        return render_template(
            "statistical/statistical_assign.html",
            **build_assign_data()
        )

    @app.route("/statistical/report")
    def statistical_report():
        return render_template(
            "statistical/statistical_report.html",
            **build_report_data()
        )