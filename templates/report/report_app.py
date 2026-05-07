from flask import render_template, request, jsonify
import math
import data


def _norm(value):
    return str(value or '').strip().lower()


def _get_asset_name(log):
    return (
        log.get('asset')
        or log.get('asset_name')
        or log.get('name')
        or ''
    )


def _get_asset_code(log):
    return (
        log.get('asset_code')
        or log.get('code')
        or log.get('id')
        or ''
    )


def _get_user(log):
    return (
        log.get('user')
        or log.get('receiver')
        or log.get('username')
        or ''
    )


def _get_department(log):
    return (
        log.get('dept')
        or log.get('department')
        or ''
    )


def _get_location(log):
    return (
        log.get('location')
        or log.get('place')
        or ''
    )


def _get_action_label(log):
    action = (
        log.get('action')
        or log.get('activity')
        or log.get('event')
        or log.get('type')
        or ''
    )

    action_norm = _norm(action)

    if 'cấp' in action_norm or 'assign' in action_norm:
        return 'Cấp phát'

    if 'bàn giao' in action_norm:
        return 'Bàn giao'

    if 'bảo trì' in action_norm or 'maintenance' in action_norm:
        return 'Bảo trì'

    if 'thu hồi' in action_norm or 'return' in action_norm or 'revoke' in action_norm:
        return 'Thu hồi'

    if 'cập nhật' in action_norm or 'update' in action_norm:
        return 'Cập nhật'

    if 'thay đổi' in action_norm:
        return 'Thay đổi'

    return action


def _get_asset_type(log):
    raw_type = (
        log.get('asset_type')
        or log.get('device_type')
        or log.get('category')
        or ''
    )

    raw_type_norm = _norm(raw_type)

    type_map = {
        'laptop': 'laptop',
        'pc': 'pc',
        'máy tính bàn': 'pc',

        'printer': 'printer',
        'máy in': 'printer',

        'monitor': 'monitor',
        'màn hình': 'monitor',

        'phone': 'phone',
        'điện thoại': 'phone',

        'projector': 'projector',
        'máy chiếu': 'projector',

        'tablet': 'tablet',
        'ipad': 'tablet',
        'máy tính bảng': 'tablet',

        'other': 'other',
        'khác': 'other',
    }

    if raw_type_norm in type_map:
        return type_map[raw_type_norm]

    text = _norm(
        f"{_get_asset_name(log)} {_get_asset_code(log)} {log.get('type', '')}"
    )

    if 'laptop' in text or 'lap' in text:
        return 'laptop'

    if 'pc' in text or 'desktop' in text or 'máy tính bàn' in text:
        return 'pc'

    if 'máy in' in text or 'printer' in text or 'laser' in text:
        return 'printer'

    if 'màn hình' in text or 'monitor' in text or 'dell 24' in text:
        return 'monitor'

    if 'điện thoại' in text or 'phone' in text:
        return 'phone'

    if 'máy chiếu' in text or 'projector' in text:
        return 'projector'

    if 'ipad' in text or 'tablet' in text or 'máy tính bảng' in text:
        return 'tablet'

    return ''


def _get_asset_type_label(log):
    asset_type = _get_asset_type(log)

    labels = {
        'laptop': 'Laptop',
        'pc': 'Máy tính bàn',
        'printer': 'Máy in',
        'monitor': 'Màn hình',
        'phone': 'Điện thoại',
        'projector': 'Máy chiếu',
        'tablet': 'Máy tính bảng',
        'other': 'Khác',
    }

    return labels.get(asset_type, '')


def _get_status_label(log):
    status = log.get('status')
    status_norm = _norm(status)

    status_map = {
        'success': 'Hoàn thành',
        'done': 'Hoàn thành',
        'completed': 'Hoàn thành',
        'hoàn thành': 'Hoàn thành',
        'thành công': 'Hoàn thành',

        'pending': 'Chờ duyệt',
        'chờ duyệt': 'Chờ duyệt',

        'processing': 'Đang xử lý',
        'in_progress': 'Đang xử lý',
        'đang xử lý': 'Đang xử lý',

        'failed': 'Thất bại',
        'fail': 'Thất bại',
        'lỗi': 'Thất bại',
        'thất bại': 'Thất bại',

        'using': 'Đang sử dụng',
        'đang sử dụng': 'Đang sử dụng',

        'available': 'Chưa sử dụng',
        'chưa sử dụng': 'Chưa sử dụng',

        'maintenance': 'Bảo trì',
        'bảo trì': 'Bảo trì',

        'broken': 'Hỏng',
        'hỏng': 'Hỏng',
    }

    return status_map.get(status_norm, status or '')


def _prepare_report_log(log):
    item = dict(log)

    item['display_asset_code'] = _get_asset_code(log)
    item['display_asset_name'] = _get_asset_name(log)
    item['display_asset_type'] = _get_asset_type(log)
    item['display_asset_type_label'] = _get_asset_type_label(log)
    item['display_status'] = _get_status_label(log)
    item['display_user'] = _get_user(log)
    item['display_department'] = _get_department(log)
    item['display_location'] = _get_location(log)
    item['display_action'] = _get_action_label(log)

    return item


def register_report_routes(app):
    @app.route('/report')
    def report_page():
        search_query = request.args.get('search', '').strip()
        search_lower = search_query.lower()

        selected_dept = request.args.get('department', 'Tất cả')
        selected_type = request.args.get('type', 'Tất cả')
        selected_status = request.args.get('status', 'Tất cả')

        page = request.args.get('page', 1, type=int)
        per_page = 10

        filtered = data.DATABASE_LOGS

        if search_lower:
            filtered = [
                log for log in filtered
                if search_lower in _norm(_get_asset_code(log))
                or search_lower in _norm(_get_asset_name(log))
                or search_lower in _norm(_get_user(log))
                or search_lower in _norm(_get_department(log))
                or search_lower in _norm(_get_location(log))
                or search_lower in _norm(_get_action_label(log))
                or search_lower in _norm(_get_status_label(log))
            ]

        if selected_type != 'Tất cả':
            selected_type_norm = _norm(selected_type)

            filtered = [
                log for log in filtered
                if _get_asset_type(log) == selected_type_norm
            ]

        if selected_dept != 'Tất cả':
            selected_dept_norm = _norm(selected_dept)
            filtered = [
                log for log in filtered
                if _norm(_get_department(log)) == selected_dept_norm
            ]

        if selected_status != 'Tất cả':
            selected_status_norm = _norm(selected_status)

            filtered = [
                log for log in filtered
                if _norm(_get_status_label(log)) == selected_status_norm
            ]

        total_logs = len(filtered)
        total_pages = math.ceil(total_logs / per_page) if total_logs > 0 else 1

        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        logs_to_display = filtered[start:start + per_page]
        logs_to_display = [_prepare_report_log(log) for log in logs_to_display]

        return render_template(
            'report/report.html',
            logs=logs_to_display,
            total_logs=total_logs,
            search_query=search_query,
            selected_dept=selected_dept,
            selected_type=selected_type,
            selected_status=selected_status,
            current_page=page,
            total_pages=total_pages,
            per_page=per_page
        )

    @app.route('/report/delete/<log_id>', methods=['POST'])
    def delete_report_log(log_id):
        before_count = len(data.DATABASE_LOGS)

        data.DATABASE_LOGS[:] = [
            log for log in data.DATABASE_LOGS
            if str(log.get('id')) != str(log_id)
        ]

        deleted = len(data.DATABASE_LOGS) < before_count

        if not deleted:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy báo cáo cần xóa.'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Đã xóa báo cáo.'
        })