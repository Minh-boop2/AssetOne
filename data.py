from datetime import datetime, timedelta
import random

random.seed(2026)

# --- 1. KHO HÀNG CHỨA THÔNG SỐ KỸ THUẬT ---
INVENTORY_LIST = [
    {"name": "Laptop Dell XPS 15", "type": "Laptop", "spec": "Core i7-12700H, 16GB RAM, 512GB SSD NVMe, RTX 3050Ti", "warranty": "12 tháng"},
    {"name": "Laptop MacBook Pro M3", "type": "Laptop", "spec": "Apple M3 8-Core CPU, 10-Core GPU, 8GB RAM, 512GB SSD", "warranty": "24 tháng"},
    {"name": "Laptop ThinkPad X1 Carbon", "type": "Laptop", "spec": "Core i7-1355U, 32GB RAM, 1TB SSD, 14 inch 2.8K OLED", "warranty": "36 tháng"},
    {"name": "Màn hình LG 27 inch", "type": "Màn hình", "spec": "27UP850-W, 4K UHD, IPS 400nits, USB-C 96W", "warranty": "36 tháng"},
    {"name": "Màn hình Dell UltraSharp 24", "type": "Màn hình", "spec": "U2422H, Full HD, IPS, 100% sRGB", "warranty": "36 tháng"},
    {"name": "Chuột Logitech M331", "type": "Phụ kiện", "spec": "Silent Wireless, 1000 DPI, 2.4GHz Receiver", "warranty": "6 tháng"},
    {"name": "Bàn phím cơ AKKO 3068", "type": "Phụ kiện", "spec": "Multi-modes (BT5.0/2.4G/Type-C), Gateron Orange Switch", "warranty": "12 tháng"},
    {"name": "Webcam Logitech C922", "type": "Phụ kiện", "spec": "Full HD 1080p 30fps / 720p 60fps, Stereo Audio", "warranty": "12 tháng"},
    {"name": "Máy in HP LaserJet", "type": "Máy in", "spec": "In laser trắng đen, 21 trang/phút, Khay giấy 150 tờ", "warranty": "12 tháng"},
    {"name": "Máy in Canon LBP226dw", "type": "Máy in", "spec": "In 2 mặt tự động, Wifi, 38 trang/phút", "warranty": "12 tháng"},
    {"name": "Router Mikrotik RB4011", "type": "Thiết bị mạng", "spec": "10x Gigabit ports, 1x SFP+ port, Quad-core 1.4GHz CPU", "warranty": "24 tháng"},
    {"name": "Switch Cisco Business 250", "type": "Thiết bị mạng", "spec": "24-Port GE, 4x10G SFP+, Smart Switch", "warranty": "60 tháng"},
    {"name": "iPad Air 5 M1", "type": "Phụ kiện", "spec": "10.9 inch, Liquid Retina, 64GB, Wi-Fi 6", "warranty": "12 tháng"},
    {"name": "Loa Jabra Speak 710", "type": "Phụ kiện", "spec": "Bluetooth, USB, Hội nghị 6-12 người", "warranty": "24 tháng"}
]

# --- 2. DANH MỤC HỖ TRỢ ---
DEPARTMENTS = [
    "Phòng Kỹ Thuật",
    "Phòng Hành Chính",
    "Phòng IT",
    "Phòng Thiết Kế",
    "Phòng Kế Toán",
    "Phòng Nhân Sự",
    "Marketing",
    "Phòng Đào Tạo"
]

ASSET_TYPES = ["Laptop", "Máy in", "Thiết bị mạng", "Màn hình", "Phụ kiện"]
STATUS_OPTIONS = ["Hoàn thành", "Chờ duyệt", "Đang xử lý", "Đã từ chối"]
LOCATIONS = ["Tầng 1", "Tầng 2", "Tầng 3", "Tầng 4", "Tầng 5", "Tầng 6", "Phòng Server", "Kho A"]
ROLES = ["Admin", "Manager", "Staff"]
USER_STATUS_OPTIONS = ["Hoạt động", "Ngưng hoạt động"]

# --- 3. DANH SÁCH NHÂN SỰ ---
FULL_NAMES = [
    "Nguyễn Văn A", "Lê Thị B", "Bành Thị C", "Dương Minh D", "Trần Hoàng Nam",
    "Phạm Gia Bảo", "Vũ Tuyết Mai", "Đỗ Minh Quân", "Hoàng Anh Thư", "Ngô Đình Trọng",
    "Lý Thanh Thảo", "Trịnh Xuân Bắc", "Đặng Thu Thảo", "Bùi Tiến Dũng", "Hồ Ngọc Hà",
    "Phan Thanh Bình", "Võ Minh Trí", "Cao Thái Sơn", "Mai Phương Thúy", "Lương Bằng Quang",
    "Đỗ Mỹ Linh", "Nguyễn Thúc Thùy Tiên", "Trần Tiểu Vy", "H'Hen Niê", "Nguyễn Cao Kỳ Duyên",
    "Phan Mạnh Quỳnh", "Sơn Tùng MTP", "Đen Vâu", "Hoàng Thùy Linh", "Nguyễn Thanh Tùng",
    "Lê Xuân Tiền", "Trương Mỹ Nhân", "Nguyễn Lâm Thảo Tâm", "Vũ Cát Tường", "Isaac Phạm",
    "Ninh Dương Lan Ngọc", "Ngô Kiến Huy", "Trấn Thành", "Hari Won", "Trường Giang",
    "Nhã Phương", "Lê Dương Bảo Lâm", "Hồ Quang Hiếu", "Bảo Anh", "Noo Phước Thịnh",
    "Đông Nhi", "Ông Cao Thắng", "Tóc Tiên", "Hoàng Touliver", "Binz Lê Nguyễn",
    "Soobin Hoàng Sơn", "RPT MCK", "Tlinh Nguyễn", "HieuThuHai", "Trần Minh Hiếu",
    "Phan Lê Vy", "Nguyễn Trọng Hiếu", "Lê Hiếu", "Thùy Chi", "Trung Quân Idol",
    "Erik Lê", "Đức Phúc", "Hòa Minzy", "Văn Mai Hương", "Uyên Linh"
]

# --- 4. TẠO DỮ LIỆU CẤP PHÁT (128 MẪU) ---
ASSIGN_DATA = []
prefix_map = {
    "Laptop": "LAP",
    "Máy in": "PRI",
    "Thiết bị mạng": "NET",
    "Màn hình": "MON",
    "Phụ kiện": "ACC"
}

for i in range(128):
    inventory_item = random.choice(INVENTORY_LIST)
    asset_name = inventory_item["name"]
    current_type = inventory_item["type"]

    new_id_number = i + 1
    prefix = prefix_map.get(current_type, "AST")

    day = (i % 28) + 1
    month = 3 if i < 60 else 4
    date_str = f"{day:02d}/{month:02d}/2026"

    if i % 7 == 0:
        status = "Chờ duyệt"
    elif i % 12 == 0:
        status = "Đang xử lý"
    elif i % 25 == 0:
        status = "Đã từ chối"
    else:
        status = "Hoàn thành"

    ASSIGN_DATA.append({
        "id": f"ASG-{str(new_id_number).zfill(3)}",
        "asset_code": f"{prefix}-{str(new_id_number).zfill(3)}",
        "asset": asset_name,
        "type": current_type,
        "receiver": FULL_NAMES[i % len(FULL_NAMES)],
        "department": DEPARTMENTS[i % len(DEPARTMENTS)],
        "location": LOCATIONS[i % len(LOCATIONS)],
        "date": date_str,
        "warranty": f"{day:02d}/{month:02d}/2027",
        "status": status
    })

# --- 5. NHẬT KÝ HỆ THỐNG (Logs) ---
DATABASE_LOGS = [
<<<<<<< HEAD
    {"id": "L001", "user": "Admin", "dept": "IT", "action": "Cấp phát", "asset": "Laptop Dell XPS 15", "time": "2026-04-09 10:00", "type": "Thiết bị"},
    {"id": "L002", "user": "Admin", "dept": "IT", "action": "Cập nhật nhân sự", "asset": "Trần Văn Nam", "time": "2026-04-10 08:30", "type": "Nhân sự"},
=======
    {
        "id": "L001", 
        "asset_name": "Laptop Dell XPS 15", 
        "type": "Thiết bị", 
        "user": "Admin", 
        "dept": "IT", 
        "status": "Hoàn thành", 
        "time": "2026-04-09 10:00"
    },
    {
        "id": "L002", 
        "asset_name": "MacBook Pro M2", 
        "type": "Thiết bị", 
        "user": "Admin", 
        "dept": "IT", 
        "status": "Hoàn thành", 
        "time": "2026-04-10 14:30"
    },
    # ... Các dòng tiếp theo Đức giữ nguyên ...
>>>>>>> 736f430df8947121b2144058b51d2f7666884c93
    {"id": "L003", "asset_name": "Màn hình Dell 24 inch", "type": "Bàn giao", "detail": "Cấp cho phòng kế toán", "dept": "Kế toán", "user": "Nguyễn An", "status": "Hoàn thành", "time": "2026-04-15 10:00"},
    {"id": "L004", "asset_name": "Máy in HP Laser", "type": "Bảo trì", "detail": "Sửa lỗi kẹt giấy", "dept": "Nhân sự", "user": "Lê Hoa", "status": "Hoàn thành", "time": "2026-04-14 14:20"},
    {"id": "L005", "asset_name": "iPad Air 5", "type": "Thay đổi", "detail": "Nâng cấp dung lượng iCloud", "dept": "Thiết kế", "user": "Phạm Hùng", "status": "Hoàn thành", "time": "2026-04-14 16:45"},
]

# Thêm log ảo để trang báo cáo có dữ liệu đẹp hơn
LOG_TYPES = ["Cấp phát", "Thu hồi", "Bảo trì", "Báo hỏng", "Cập nhật", "Kiểm kê"]
LOG_ACTIONS = {
    "Cấp phát": ["Cấp phát tài sản", "Bàn giao thiết bị", "Xác nhận cấp phát"],
    "Thu hồi": ["Thu hồi tài sản", "Kiểm tra thiết bị thu hồi", "Cập nhật kho sau thu hồi"],
    "Bảo trì": ["Bảo trì định kỳ", "Sửa chữa thiết bị", "Thay linh kiện"],
    "Báo hỏng": ["Ghi nhận báo hỏng", "Tạo phiếu xử lý", "Chuyển IT kiểm tra"],
    "Cập nhật": ["Cập nhật thông tin", "Cập nhật trạng thái", "Cập nhật người sử dụng"],
    "Kiểm kê": ["Kiểm kê kho", "Đối chiếu tài sản", "Xác nhận tồn kho"]
}

for i in range(35):
    log_type = LOG_TYPES[i % len(LOG_TYPES)]
    inventory_item = INVENTORY_LIST[i % len(INVENTORY_LIST)]
    day = (i % 25) + 1
    hour = 8 + (i % 9)
    minute = (i * 7) % 60

    DATABASE_LOGS.append({
        "id": f"L{str(i + 6).zfill(3)}",
        "user": FULL_NAMES[i % len(FULL_NAMES)],
        "dept": DEPARTMENTS[i % len(DEPARTMENTS)],
        "action": random.choice(LOG_ACTIONS[log_type]),
        "asset": inventory_item["name"],
        "asset_name": inventory_item["name"],
        "type": log_type,
        "detail": f"{log_type} cho {inventory_item['name']}",
        "status": "Hoàn thành" if i % 5 != 0 else "Đang xử lý",
        "time": f"2026-04-{day:02d} {hour:02d}:{minute:02d}"
    })

# --- 6. DANH SÁCH NHÂN SỰ CHI TIẾT (USER_LIST_DATA) ---
USER_LIST_DATA = []

def generate_fake_phone():
    prefixes = ["090", "091", "098", "035", "038", "077", "086"]
    return f"{random.choice(prefixes)}{random.randint(1000000, 9999999)}"

def generate_join_date():
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2026, 4, 1)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    return random_date.strftime("%d/%m/%Y")

# Tạo khoảng 60 nhân sự để test phân trang và đếm số lượng
for i in range(60):
    role_choice = "Admin" if i < 5 else ("Manager" if i < 15 else "Staff")
    dept_choice = DEPARTMENTS[i % len(DEPARTMENTS)]
    loc_choice = f"Tầng {random.randint(1, 6)}"

    USER_LIST_DATA.append({
        "id": f"HSU-{str(i + 1).zfill(3)}",
        "name": FULL_NAMES[i % len(FULL_NAMES)],
        "email": f"user{i + 1}@hoasen.edu.vn",
        "phone": generate_fake_phone(),
        "created_at": generate_join_date(),
        "dept": dept_choice,
        "position": loc_choice,
        "role": role_choice,
        "status": "Hoạt động" if i % 10 != 0 else "Ngưng hoạt động"
    })

# --- 7. HÀM HỖ TRỢ ---
def get_filter_counts():
    """Trả về số lượng cho từng mục để hiển thị trong select filter"""
    counts = {
        "categories": {cat: len([d for d in ASSIGN_DATA if d["type"] == cat]) for cat in ASSET_TYPES},
        "departments": {dept: len([d for d in ASSIGN_DATA if d["department"] == dept]) for dept in DEPARTMENTS},
        "locations": {loc: len([d for d in ASSIGN_DATA if d["location"] == loc]) for loc in LOCATIONS},
        "status": {stat: len([d for d in ASSIGN_DATA if d["status"] == stat]) for stat in STATUS_OPTIONS},
        "total": len(ASSIGN_DATA)
    }
    return counts

# --- 8. DỮ LIỆU ẢO CHO TRANG THỐNG KÊ DOANH THU ---
# Dùng cho statistical_overview.html: doanh thu, chi phí, lời, lỗ theo tháng.
FINANCE_MONTHLY_DATA = [
    {
        "month": "T1",
        "revenue": 125000000,
        "cost": 82000000,
        "loss": 6000000,
        "orders": 126,
        "maintenance_cost": 14500000,
        "asset_recovery": 18000000
    },
    {
        "month": "T2",
        "revenue": 148000000,
        "cost": 91000000,
        "loss": 4500000,
        "orders": 144,
        "maintenance_cost": 13200000,
        "asset_recovery": 22000000
    },
    {
        "month": "T3",
        "revenue": 132000000,
        "cost": 89000000,
        "loss": 7200000,
        "orders": 132,
        "maintenance_cost": 15800000,
        "asset_recovery": 16500000
    },
    {
        "month": "T4",
        "revenue": 176000000,
        "cost": 104000000,
        "loss": 5200000,
        "orders": 168,
        "maintenance_cost": 17200000,
        "asset_recovery": 26000000
    },
    {
        "month": "T5",
        "revenue": 194000000,
        "cost": 116000000,
        "loss": 6800000,
        "orders": 192,
        "maintenance_cost": 18100000,
        "asset_recovery": 28500000
    },
    {
        "month": "T6",
        "revenue": 218000000,
        "cost": 128000000,
        "loss": 7500000,
        "orders": 218,
        "maintenance_cost": 19600000,
        "asset_recovery": 31000000
    },
    {
        "month": "T7",
        "revenue": 236000000,
        "cost": 138000000,
        "loss": 6200000,
        "orders": 235,
        "maintenance_cost": 21000000,
        "asset_recovery": 33400000
    },
    {
        "month": "T8",
        "revenue": 229000000,
        "cost": 134000000,
        "loss": 8800000,
        "orders": 228,
        "maintenance_cost": 22600000,
        "asset_recovery": 29800000
    },
    {
        "month": "T9",
        "revenue": 251000000,
        "cost": 145000000,
        "loss": 7300000,
        "orders": 249,
        "maintenance_cost": 24100000,
        "asset_recovery": 36200000
    },
    {
        "month": "T10",
        "revenue": 268000000,
        "cost": 153000000,
        "loss": 9100000,
        "orders": 263,
        "maintenance_cost": 25500000,
        "asset_recovery": 38900000
    },
    {
        "month": "T11",
        "revenue": 286000000,
        "cost": 162000000,
        "loss": 8400000,
        "orders": 281,
        "maintenance_cost": 27200000,
        "asset_recovery": 41500000
    },
    {
        "month": "T12",
        "revenue": 312000000,
        "cost": 174000000,
        "loss": 9700000,
        "orders": 306,
        "maintenance_cost": 28800000,
        "asset_recovery": 46200000
    },
]

for item in FINANCE_MONTHLY_DATA:
    item["profit"] = item["revenue"] - item["cost"] - item["loss"]

# --- 9. DỮ LIỆU NGUỒN DOANH THU ---
REVENUE_SOURCE_DATA = [
    {"name": "Phí cấp phát thiết bị", "value": 820000000, "color": "#8b5cf6"},
    {"name": "Bảo trì thiết bị", "value": 426000000, "color": "#06b6d4"},
    {"name": "Thanh lý tài sản cũ", "value": 318000000, "color": "#22c55e"},
    {"name": "Hỗ trợ kỹ thuật", "value": 244000000, "color": "#f97316"},
    {"name": "Dịch vụ nội bộ khác", "value": 174000000, "color": "#ef4444"},
]

# --- 10. DỮ LIỆU CHI PHÍ ---
EXPENSE_CATEGORY_DATA = [
    {"name": "Mua thiết bị mới", "value": 685000000, "color": "#06b6d4"},
    {"name": "Bảo trì / sửa chữa", "value": 246000000, "color": "#f97316"},
    {"name": "Phụ kiện thay thế", "value": 128000000, "color": "#8b5cf6"},
    {"name": "Vận hành kho", "value": 94000000, "color": "#22c55e"},
    {"name": "Tổn thất / thất thoát", "value": 82000000, "color": "#ef4444"},
]

# --- 11. DỮ LIỆU BÁO CÁO TÀI CHÍNH CHI TIẾT ---
FINANCIAL_REPORT_DATA = []

for index, item in enumerate(FINANCE_MONTHLY_DATA):
    FINANCIAL_REPORT_DATA.append({
        "id": f"FIN-{str(index + 1).zfill(3)}",
        "month": item["month"],
        "revenue": item["revenue"],
        "cost": item["cost"],
        "profit": item["profit"],
        "loss": item["loss"],
        "orders": item["orders"],
        "maintenance_cost": item["maintenance_cost"],
        "asset_recovery": item["asset_recovery"],
        "status": "Tăng trưởng" if item["profit"] >= 70000000 else "Ổn định",
        "note": "Doanh thu tốt" if item["profit"] >= 70000000 else "Cần tối ưu chi phí"
    })

# --- 12. HÀM HỖ TRỢ CHO TRANG THỐNG KÊ ---
def format_currency(value):
    """Định dạng tiền Việt Nam."""
    return f"{value:,.0f}".replace(",", ".") + "đ"

def get_finance_summary():
    """Trả về tổng doanh thu, chi phí, lời, lỗ cho trang thống kê doanh thu."""
    total_revenue = sum(item["revenue"] for item in FINANCE_MONTHLY_DATA)
    total_cost = sum(item["cost"] for item in FINANCE_MONTHLY_DATA)
    total_profit = sum(item["profit"] for item in FINANCE_MONTHLY_DATA)
    total_loss = sum(item["loss"] for item in FINANCE_MONTHLY_DATA)
    total_orders = sum(item["orders"] for item in FINANCE_MONTHLY_DATA)

    return {
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "total_loss": total_loss,
        "total_orders": total_orders,
        "total_revenue_text": format_currency(total_revenue),
        "total_cost_text": format_currency(total_cost),
        "total_profit_text": format_currency(total_profit),
        "total_loss_text": format_currency(total_loss),
        "total_orders_text": f"{total_orders:,}".replace(",", ".")
    }

def get_finance_monthly_data():
    """Trả về dữ liệu tài chính theo tháng có định dạng tiền để render lên HTML."""
    max_money = max(
        max(item["revenue"], item["cost"], item["profit"], item["loss"])
        for item in FINANCE_MONTHLY_DATA
    )

    result = []

    for item in FINANCE_MONTHLY_DATA:
        result.append({
            **item,
            "revenue_text": format_currency(item["revenue"]),
            "cost_text": format_currency(item["cost"]),
            "profit_text": format_currency(item["profit"]),
            "loss_text": format_currency(item["loss"]),
            "revenue_height": max(round((item["revenue"] / max_money) * 100, 1), 6),
            "cost_height": max(round((item["cost"] / max_money) * 100, 1), 6),
            "profit_height": max(round((item["profit"] / max_money) * 100, 1), 6),
            "loss_height": max(round((item["loss"] / max_money) * 100, 1), 6),
        })

    return result

def get_finance_segments():
    """Trả về dữ liệu biểu đồ tròn cho doanh thu, chi phí, lời, lỗ."""
    summary = get_finance_summary()

    segments = [
        {
            "label": "Doanh thu",
            "value": summary["total_revenue"],
            "value_text": summary["total_revenue_text"],
            "color": "#8b5cf6",
            "class": "purple",
        },
        {
            "label": "Chi phí",
            "value": summary["total_cost"],
            "value_text": summary["total_cost_text"],
            "color": "#06b6d4",
            "class": "cyan",
        },
        {
            "label": "Tiền lời",
            "value": summary["total_profit"],
            "value_text": summary["total_profit_text"],
            "color": "#22c55e",
            "class": "green",
        },
        {
            "label": "Tiền lỗ",
            "value": summary["total_loss"],
            "value_text": summary["total_loss_text"],
            "color": "#f97316",
            "class": "orange",
        },
    ]

    total = sum(item["value"] for item in segments)
    current_degree = 0

    for item in segments:
        degree = (item["value"] / total) * 360 if total else 0
        item["percent"] = round((item["value"] / total) * 100, 1) if total else 0
        item["from_deg"] = round(current_degree, 2)
        item["to_deg"] = round(current_degree + degree, 2)
        current_degree += degree

    return segments

def get_revenue_source_data():
    """Dữ liệu nguồn doanh thu cho biểu đồ phụ."""
    total = sum(item["value"] for item in REVENUE_SOURCE_DATA)

    result = []
    for item in REVENUE_SOURCE_DATA:
        result.append({
            **item,
            "value_text": format_currency(item["value"]),
            "percent": round((item["value"] / total) * 100, 1) if total else 0
        })

    return result

def get_expense_category_data():
    """Dữ liệu nhóm chi phí cho biểu đồ phụ."""
    total = sum(item["value"] for item in EXPENSE_CATEGORY_DATA)

    result = []
    for item in EXPENSE_CATEGORY_DATA:
        result.append({
            **item,
            "value_text": format_currency(item["value"]),
            "percent": round((item["value"] / total) * 100, 1) if total else 0
        })

    return result

def get_statistical_fake_data():
    """Hàm gom dữ liệu tài chính để statistical_app.py có thể gọi trực tiếp."""
    summary = get_finance_summary()

    return {
        "finance_summary": summary,
        "finance_months": get_finance_monthly_data(),
        "finance_segments": get_finance_segments(),
        "revenue_sources": get_revenue_source_data(),
        "expense_categories": get_expense_category_data(),
        "financial_reports": FINANCIAL_REPORT_DATA,
    }