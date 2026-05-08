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


def _get_report_type(log):
    raw = (
        log.get('report_type')
        or log.get('action')
        or log.get('activity')
        or log.get('event')
        or log.get('type')
        or ''
    )

    raw_norm = _norm(raw)

    if 'cấp' in raw_norm or 'assign' in raw_norm:
        return 'Cấp phát'

    if 'bàn giao' in raw_norm:
        return 'Bàn giao'

    if 'bảo trì' in raw_norm or 'maintenance' in raw_norm:
        return 'Bảo trì'

    if 'thu hồi' in raw_norm or 'return' in raw_norm or 'revoke' in raw_norm:
        return 'Thu hồi'

    if 'cập nhật' in raw_norm or 'update' in raw_norm:
        return 'Cập nhật'

    if 'thay đổi' in raw_norm:
        return 'Thay đổi'

    if 'thiết' in raw_norm:
        return 'Thiết bị'

    if raw:
        return raw

    return 'Khác'


def _get_report_status(log):
    raw = log.get('report_status') or log.get('status') or ''
    raw_norm = _norm(raw)

    viewed_values = [
        'đã xem',
        'da xem',
        'hoàn thành',
        'thành công',
        'success',
        'done',
        'completed',
    ]

    if raw_norm in viewed_values:
        return 'Đã xem'

    return 'Chờ'


def _get_report_name(log):
    report_type = _get_report_type(log)
    asset_name = _get_asset_name(log)

    if log.get('report_name'):
        return log.get('report_name')

    if asset_name:
        return f"Báo cáo {report_type} - {asset_name}"

    return f"Báo cáo {report_type}"


def _prepare_report_log(row_index, log):
    item = dict(log)

    item['_row_index'] = row_index
    item['display_report_code'] = log.get('id') or _get_asset_code(log)
    item['display_report_name'] = _get_report_name(log)
    item['display_report_type'] = _get_report_type(log)
    item['display_report_status'] = _get_report_status(log)
    item['display_reporter'] = _get_user(log)
    item['display_department'] = _get_department(log)
    item['display_location'] = _get_location(log)

    return item


def register_report_routes(app):
    @app.route('/report')
    def report_page():
        search_query = request.args.get('search', '').strip()
        search_lower = search_query.lower()

        selected_type = request.args.get('type', 'Tất cả')
        selected_dept = request.args.get('department', 'Tất cả')
        selected_location = request.args.get('location', 'Tất cả')
        selected_status = request.args.get('status', 'Tất cả')

        page = request.args.get('page', 1, type=int)

        # 1 trang có 10 data.
        # CSS hiển thị khoảng 5 data, 5 data còn lại cuộn trong bảng.
        per_page = 10

        source_logs = list(enumerate(data.DATABASE_LOGS))
        filtered = source_logs

        if search_lower:
            filtered = [
                (idx, log) for idx, log in filtered
                if search_lower in _norm(log.get('id'))
                or search_lower in _norm(_get_report_name(log))
                or search_lower in _norm(_get_report_type(log))
                or search_lower in _norm(_get_report_status(log))
                or search_lower in _norm(_get_user(log))
                or search_lower in _norm(_get_department(log))
                or search_lower in _norm(_get_location(log))
                or search_lower in _norm(_get_asset_name(log))
                or search_lower in _norm(_get_asset_code(log))
            ]

        if selected_type != 'Tất cả':
            selected_type_norm = _norm(selected_type)
            filtered = [
                (idx, log) for idx, log in filtered
                if _norm(_get_report_type(log)) == selected_type_norm
            ]

        if selected_dept != 'Tất cả':
            selected_dept_norm = _norm(selected_dept)
            filtered = [
                (idx, log) for idx, log in filtered
                if _norm(_get_department(log)) == selected_dept_norm
            ]

        if selected_location != 'Tất cả':
            selected_location_norm = _norm(selected_location)
            filtered = [
                (idx, log) for idx, log in filtered
                if _norm(_get_location(log)) == selected_location_norm
            ]

        if selected_status != 'Tất cả':
            selected_status_norm = _norm(selected_status)
            filtered = [
                (idx, log) for idx, log in filtered
                if _norm(_get_report_status(log)) == selected_status_norm
            ]

        total_logs = len(filtered)
        total_pages = math.ceil(total_logs / per_page) if total_logs > 0 else 1

        page = max(1, min(page, total_pages))

        start = (page - 1) * per_page
        end = start + per_page

        logs_to_display = filtered[start:end]
        logs_to_display = [
            _prepare_report_log(idx, log)
            for idx, log in logs_to_display
        ]

        return render_template(
            'report/report.html',
            logs=logs_to_display,
            total_logs=total_logs,
            search_query=search_query,
            selected_type=selected_type,
            selected_dept=selected_dept,
            selected_location=selected_location,
            selected_status=selected_status,
            current_page=page,
            total_pages=total_pages,
            per_page=per_page
        )

    @app.route('/report/delete/<int:row_index>', methods=['POST'])
    def delete_report_log(row_index):
        if row_index < 0 or row_index >= len(data.DATABASE_LOGS):
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy báo cáo cần xóa.'
            }), 404

        del data.DATABASE_LOGS[row_index]

        return jsonify({
            'success': True,
            'message': 'Đã xóa báo cáo.'
        })