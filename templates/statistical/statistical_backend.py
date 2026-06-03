# File: statistical_backend.py
# File này gọi API backend thật để lấy dữ liệu thống kê

import os
import requests


BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:5001")


def get_json(url, headers=None, params=None):
    try:
        response = requests.get(
            url,
            headers=headers or {},
            params=params or {},
            timeout=8,
        )

        try:
            payload = response.json()
        except Exception:
            payload = {}

        return payload, response.status_code

    except requests.RequestException as error:
        return {
            "success": False,
            "message": str(error),
        }, 500


def get_default_employees_context():
    return {
        "total_users": 0,
        "active_users": 0,
        "inactive_users": 0,
        "employee_segments": [],
        "role_items": [],
        "dept_items": [],
        "recent_users": [],
        "statistical_error": None,
        "current_user": {},
    }


def get_default_overview_context():
    return {
        "finance_summary": {},
        "finance_months": [],
        "finance_cards": [],
        "finance_segments": [],
        "revenue_sources": [],
        "expense_categories": [],
        "financial_reports": [],
        "total_revenue_text": "0đ",
        "total_cost_text": "0đ",
        "total_profit_text": "0đ",
        "total_loss_text": "0đ",
        "total_orders_text": "0",
        "statistical_error": None,
        "current_user": {},
    }


def get_default_assets_context():
    return {
        "total_assets": 0,
        "type_items": [],
        "status_segments": [],
        "recent_assets": [],
        "damaged_assets": [],
        "total_damaged": 0,
        "total_repair_cost": 0,
        "total_repair_cost_text": "0đ",
        "repair_level_items": [],
        "repair_status_segments": [],
        "statistical_error": None,
        "current_user": {},
    }


def get_default_assign_context():
    return {
        "assign_total": 0,
        "status_segments": [],
        "dept_items": [],
        "location_items": [],
        "statistical_error": None,
        "current_user": {},
    }


def get_default_report_context():
    return {
        "report_total": 0,
        "log_items": [],
        "status_items": [],
        "log_segments": [],
        "recent_logs": [],
        "statistical_error": None,
        "current_user": {},
    }


def build_context_from_api(endpoint, default_context, args=None, current_user=None):
    payload, status_code = get_json(
        f"{BACKEND_API_URL}{endpoint}",
        params=args,
    )

    context = default_context()
    context["current_user"] = current_user or {}

    if status_code != 200 or not payload.get("success"):
        context["statistical_error"] = (
            payload.get("message")
            or "Không thể tải dữ liệu thống kê"
        )

        return context

    data = payload.get("data") or {}

    context.update(data)
    context["statistical_error"] = None

    return context


def get_statistical_overview_context(args, current_user):
    return build_context_from_api(
        endpoint="/api/statistical/overview",
        default_context=get_default_overview_context,
        args=args,
        current_user=current_user,
    )


def get_statistical_employees_context(args, current_user):
    return build_context_from_api(
        endpoint="/api/statistical/employees",
        default_context=get_default_employees_context,
        args=args,
        current_user=current_user,
    )


def get_statistical_assets_context(args, current_user):
    return build_context_from_api(
        endpoint="/api/statistical/assets",
        default_context=get_default_assets_context,
        args=args,
        current_user=current_user,
    )


def get_statistical_assign_context(args, current_user):
    return build_context_from_api(
        endpoint="/api/statistical/assign",
        default_context=get_default_assign_context,
        args=args,
        current_user=current_user,
    )


def get_statistical_report_context(args, current_user):
    return build_context_from_api(
        endpoint="/api/statistical/report",
        default_context=get_default_report_context,
        args=args,
        current_user=current_user,
    )