from flask import render_template, request, redirect, url_for
from datetime import datetime
import math
import data


def register_assets_routes(app):
    @app.route('/assets')
    def assets_page():
        search_q = request.args.get('search', '').strip().lower()
        sel_type = request.args.get('type', 'Tất cả')
        sel_dept = request.args.get('department', 'Tất cả')
        sel_status = request.args.get('status', 'Tất cả')

        filtered = data.ASSIGN_DATA
        if search_q:
            filtered = [
                i for i in filtered if
                search_q in i.get('asset', '').lower() or
                search_q in i.get('asset_code', '').lower() or
                search_q in i.get('id', '').lower()
            ]
        if sel_type != 'Tất cả':
            filtered = [i for i in filtered if i.get('type') == sel_type]
        if sel_dept != 'Tất cả':
            filtered = [i for i in filtered if i.get('department') == sel_dept]
        if sel_status != 'Tất cả':
            if sel_status == 'using':
                filtered = [i for i in filtered if i.get('status') in ['using', 'Hoàn thành']]
            else:
                filtered = [i for i in filtered if i.get('status') == sel_status]

        page = request.args.get('page', 1, type=int)
        per_page = 10
        total_assets = len(filtered)
        total_pages = math.ceil(total_assets / per_page) if total_assets > 0 else 1
        page = max(1, min(page, total_pages))

        start = (page - 1) * per_page
        end = start + per_page
        paginated_assets = filtered[start:end]

        return render_template(
            'assets/assets.html',
            assets=paginated_assets,
            current_page=page,
            total_pages=total_pages,
            search_q=search_q,
            total_count=total_assets,
            selected_type=sel_type,
            selected_dept=sel_dept,
            selected_status=sel_status
        )

    @app.route('/assets/create', methods=['GET', 'POST'])
    def asset_create():
        if request.method == 'POST':
            asset_name = request.form.get('asset_name')
            new_id = f"ASG-{str(len(data.ASSIGN_DATA) + 1).zfill(3)}"
            new_asset = {
                "id": new_id,
                "asset_code": request.form.get('asset_code'),
                "asset": asset_name,
                "type": request.form.get('type'),
                "receiver": request.form.get('receiver'),
                "department": request.form.get('department'),
                "location": request.form.get('location'),
                "date": datetime.now().strftime("%d/%m/%Y"),
                "warranty": request.form.get('warranty'),
                "status": request.form.get('status')
            }
            data.ASSIGN_DATA.insert(0, new_asset)
            data.INVENTORY_LIST.append({
                "name": asset_name,
                "spec": request.form.get('spec') or "Thông số đang cập nhật",
                "warranty": request.form.get('warranty')
            })
            return redirect(url_for('assets_page'))
        return render_template('assets/asset_create.html')

    @app.route('/assets/detail/<string:asset_id>')
    def asset_detail_view(asset_id):
        info = next((item for item in data.ASSIGN_DATA if item["id"] == asset_id), None)
        if not info:
            return redirect(url_for('assets_page'))

        specs = next((item for item in data.INVENTORY_LIST if item["name"] == info.get('asset')), {
            "spec": "Thông số kỹ thuật đang được cập nhật",
            "warranty": "N/A"
        })
        return render_template('assets/asset_detail.html', info=info, specs=specs)