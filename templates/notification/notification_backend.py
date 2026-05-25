import os
import requests
from flask import session


DEFAULT_BACKEND_API_URL = "http://localhost:5001"
DEFAULT_TIMEOUT = 8


def get_backend_api_url():
    return os.getenv("BACKEND_API_URL", DEFAULT_BACKEND_API_URL).rstrip("/")


def get_current_session_user():
    return session.get("user") or {}


def get_current_user_id():
    current_user = get_current_session_user()

    return str(
        current_user.get("id")
        or current_user.get("_id")
        or current_user.get("user_id")
        or ""
    )


def _build_headers(user_id=None):
    resolved_user_id = user_id or get_current_user_id()

    headers = {
        "Content-Type": "application/json",
    }

    if resolved_user_id:
        headers["X-User-Id"] = str(resolved_user_id)

    return headers


def _safe_json_response(response):
    try:
        return response.json()
    except Exception:
        return {
            "success": False,
            "message": response.text or "Backend response is not JSON"
        }


def _backend_request(method, path, payload=None, user_id=None):
    url = f"{get_backend_api_url()}{path}"

    try:
        response = requests.request(
            method=method,
            url=url,
            json=payload,
            headers=_build_headers(user_id=user_id),
            timeout=DEFAULT_TIMEOUT,
        )

        return _safe_json_response(response), response.status_code

    except requests.RequestException as error:
        return {
            "success": False,
            "message": f"Không kết nối được backend notification: {error}"
        }, 503


def get_my_notifications(limit=20, unread=False):
    query = f"?limit={limit}"

    if unread:
        query += "&unread=true"

    return _backend_request(
        method="GET",
        path=f"/api/notifications/me{query}",
    )


def get_my_unread_count():
    return _backend_request(
        method="GET",
        path="/api/notifications/me/unread-count",
    )


def mark_notification_read(notification_id):
    user_id = get_current_user_id()

    return _backend_request(
        method="PATCH",
        path=f"/api/notifications/{notification_id}/read",
        payload={
            "user_id": user_id
        },
    )


def mark_all_notifications_read():
    user_id = get_current_user_id()

    return _backend_request(
        method="PATCH",
        path="/api/notifications/read-all",
        payload={
            "user_id": user_id
        },
    )


def delete_notification(notification_id):
    user_id = get_current_user_id()

    return _backend_request(
        method="DELETE",
        path=f"/api/notifications/{notification_id}",
        payload={
            "user_id": user_id
        },
    )