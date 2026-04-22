from flask import render_template, request, redirect, url_for, jsonify
import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode, quote

BACKEND_ASSETS_API = "http://127.0.0.1:5001/api/assets"

DEFAULT_FILTER_COUNTS = {
    "type": {
        "all": 0,
        "laptop": 0,
        "pc": 0,
        "printer": 0
    },
    "status": {
        "all": 0,
        "using": 0,
        "available": 0,
        "maintenance": 0,
        "pending": 0
    }
}


def fetch_assets_from_backend(page=1, per_page=10, search="", asset_type="Tất cả", department="Tất cả", status="Tất cả"):
    params = {
        "page": page,
        "per_page": per_page,
        "search": search,
        "type": asset_type,
        "department": department,
        "status": status
    }

    api_url = f"{BACKEND_ASSETS_API}?{urlencode(params)}"

    try:
        with urlopen(api_url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
        return {
            "items": [],
            "pagination": {
                "page": 1,
                "per_page": per_page,
                "total_items": 0,
                "total_pages": 1
            },
            "filter_counts": DEFAULT_FILTER_COUNTS
        }


def fetch_asset_detail_from_backend(asset_id):
    api_url = f"{BACKEND_ASSETS_API}/{quote(asset_id)}"

    try:
        with urlopen(api_url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
        return None


def delete_asset_from_backend(asset_id):
    api_url = f"{BACKEND_ASSETS_API}/{quote(asset_id)}"
    req = Request(api_url, method="DELETE")

    try:
        with urlopen(req, timeout=5) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
        return True, payload

    except HTTPError as e:
        try:
            raw = e.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
        except Exception:
            payload = {}

        return False, {
            "message": payload.get("message", f"Xóa tài sản thất bại. HTTP {e.code}")
        }

    except (URLError, TimeoutError, json.JSONDecodeError):
        return False, {
            "message": "Không thể kết nối đến backend để xóa tài sản."
        }


def register_assets_routes(app):
    @app.route('/assets')
    def assets_page():
        search_q = request.args.get('search', '').strip()
        sel_type = request.args.get('type', 'Tất cả')
        sel_dept = request.args.get('department', 'Tất cả')
        sel_status = request.args.get('status', 'Tất cả')
        page = request.args.get('page', 1, type=int)
        per_page = 10

        api_result = fetch_assets_from_backend(
            page=page,
            per_page=per_page,
            search=search_q,
            asset_type=sel_type,
            department=sel_dept,
            status=sel_status
        )

        assets = api_result.get("items", [])
        pagination = api_result.get("pagination", {})
        filter_counts = api_result.get("filter_counts", DEFAULT_FILTER_COUNTS)

        return render_template(
            'assets/assets.html',
            assets=assets,
            current_page=pagination.get("page", 1),
            total_pages=pagination.get("total_pages", 1),
            search_q=search_q,
            total_count=pagination.get("total_items", 0),
            selected_type=sel_type,
            selected_dept=sel_dept,
            selected_status=sel_status,
            filter_counts=filter_counts
        )

    @app.route('/assets/create', methods=['GET', 'POST'])
    def asset_create():
        if request.method == 'POST':
            return redirect(url_for('assets_page'))
        return render_template('assets/asset_create.html')

    @app.route('/assets/detail/<string:asset_id>')
    def asset_detail_view(asset_id):
        info = fetch_asset_detail_from_backend(asset_id)

        if not info:
            return redirect(url_for('assets_page'))

        info["asset"] = info.get("asset") or info.get("asset_name") or ""
        info["asset_name"] = info.get("asset_name") or info.get("asset") or ""

        specs = {
            "spec": "Thông số kỹ thuật đang được cập nhật",
            "warranty": info.get("warranty") or "N/A"
        }

        return render_template('assets/asset_detail.html', info=info, specs=specs)

    @app.route('/assets/delete/<string:asset_id>', methods=['POST'])
    def asset_delete_view(asset_id):
        success, result = delete_asset_from_backend(asset_id)

        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if is_ajax:
            return jsonify(result), 200 if success else 400

        return redirect(url_for('assets_page'))