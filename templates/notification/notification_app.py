from flask import jsonify, render_template, request, session

from templates.notification.notification_backend import (
    get_backend_api_url,
    get_current_user_id,
    get_my_notifications,
    get_my_unread_count,
    mark_notification_read,
    mark_all_notifications_read,
    delete_notification,
)


def _get_bool(value):
    if value is None:
        return False

    return str(value).lower() in ["true", "1", "yes", "y"]


def _get_limit():
    try:
        limit = int(request.args.get("limit", 20))
    except Exception:
        limit = 20

    if limit < 1:
        limit = 1

    if limit > 100:
        limit = 100

    return limit


def _extract_notifications(response):
    if not isinstance(response, dict):
        return []

    data = response.get("data")

    if isinstance(data, list):
        return data

    return []


def _extract_unread_count(response):
    if not isinstance(response, dict):
        return 0

    try:
        return int(response.get("unread_count", 0))
    except Exception:
        return 0


def register_notification_routes(app):

    @app.context_processor
    def inject_notification_context():
        current_user = session.get("user") or {}

        notification_user_id = str(
            current_user.get("id")
            or current_user.get("_id")
            or current_user.get("user_id")
            or ""
        )

        return {
            "notification_backend_url": get_backend_api_url(),
            "notification_user_id": notification_user_id,
        }

    @app.route("/notifications/data", methods=["GET"])
    def notifications_data():
        user_id = get_current_user_id()

        if not user_id:
            return jsonify({
                "success": False,
                "message": "Chưa đăng nhập"
            }), 401

        limit = _get_limit()
        unread = _get_bool(request.args.get("unread"))

        notifications_response, notifications_status = get_my_notifications(
            limit=limit,
            unread=unread,
        )

        unread_response, _ = get_my_unread_count()

        if not notifications_response.get("success"):
            return jsonify(notifications_response), notifications_status

        return jsonify({
            "success": True,
            "data": _extract_notifications(notifications_response),
            "unread_count": _extract_unread_count(unread_response),
        }), 200

    @app.route("/notifications/popover", methods=["GET"])
    def notifications_popover():
        user_id = get_current_user_id()

        if not user_id:
            return render_template(
                "notification/notification_popover.html",
                notifications=[],
                unread_count=0,
            )

        limit = _get_limit()

        notifications_response, _ = get_my_notifications(limit=limit)
        unread_response, _ = get_my_unread_count()

        return render_template(
            "notification/notification_popover.html",
            notifications=_extract_notifications(notifications_response),
            unread_count=_extract_unread_count(unread_response),
        )

    @app.route("/notifications/<notification_id>/read", methods=["PATCH", "POST"])
    def notification_mark_read(notification_id):
        user_id = get_current_user_id()

        if not user_id:
            return jsonify({
                "success": False,
                "message": "Chưa đăng nhập"
            }), 401

        response, status_code = mark_notification_read(notification_id)

        return jsonify(response), status_code

    @app.route("/notifications/read-all", methods=["PATCH", "POST"])
    def notifications_mark_all_read():
        user_id = get_current_user_id()

        if not user_id:
            return jsonify({
                "success": False,
                "message": "Chưa đăng nhập"
            }), 401

        response, status_code = mark_all_notifications_read()

        return jsonify(response), status_code

    @app.route("/notifications/<notification_id>", methods=["DELETE", "POST"])
    def notification_delete(notification_id):
        user_id = get_current_user_id()

        if not user_id:
            return jsonify({
                "success": False,
                "message": "Chưa đăng nhập"
            }), 401

        response, status_code = delete_notification(notification_id)

        return jsonify(response), status_code