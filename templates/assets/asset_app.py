from flask import render_template, request, redirect, url_for
import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode, quote

BACKEND_ASSETS_API = "http://127.0.0.1:5001/api/assets"


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
            }
        }


def fetch_asset_detail_from_backend(asset_id):
    api_url = f"{BACKEND_ASSETS_API}/{quote(asset_id)}"

    try:
        with urlopen(api_url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
        return None


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

        return render_template(
            'assets/assets.html',
            assets=assets,
            current_page=pagination.get("page", 1),
            total_pages=pagination.get("total_pages", 1),
            search_q=search_q,
            total_count=pagination.get("total_items", 0),
            selected_type=sel_type,
            selected_dept=sel_dept,
            selected_status=sel_status
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