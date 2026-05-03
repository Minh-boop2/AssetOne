from datetime import datetime, timedelta
import random

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
DEPARTMENTS = ["Phòng Kỹ Thuật", "Phòng Hành Chính", "Phòng IT", "Phòng Thiết Kế", "Phòng Kế Toán", "Phòng Nhân Sự", "Marketing", "Phòng Đào Tạo"]
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
prefix_map = {"Laptop": "LAP", "Máy in": "PRI", "Thiết bị mạng": "NET", "Màn hình": "MON", "Phụ kiện": "ACC"}

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
    {"id": "L001", "user": "Admin", "dept": "IT", "action": "Cấp phát", "asset": "Laptop Dell XPS 15", "time": "2026-04-09 10:00", "type": "Thiết thiết bị"},
    {"id": "L002", "user": "Admin", "dept": "IT", "action": "Cập nhật nhân sự", "asset": "Trần Văn Nam", "time": "2026-04-10 08:30", "type": "Nhân sự"},
    {"id": "L003", "asset_name": "Màn hình Dell 24 inch", "type": "Bàn giao", "detail": "Cấp cho phòng kế toán", "dept": "Kế toán", "user": "Nguyễn An", "status": "Hoàn thành", "time": "2026-04-15 10:00"},
    {"id": "L004", "asset_name": "Máy in HP Laser", "type": "Bảo trì", "detail": "Sửa lỗi kẹt giấy", "dept": "Nhân sự", "user": "Lê Hoa", "status": "Hoàn thành", "time": "2026-04-14 14:20"},
    {"id": "L005", "asset_name": "iPad Air 5", "type": "Thay đổi", "detail": "Nâng cấp dung lượng iCloud", "dept": "Thiết kế", "user": "Phạm Hùng", "status": "Hoàn thành", "time": "2026-04-14 16:45"},
]

# --- 6. DANH SÁCH NHÂN SỰ CHI TIẾT (USER_LIST_DATA) ---
USER_LIST_DATA = []

# Hàm hỗ trợ tạo số điện thoại ngẫu nhiên
def generate_fake_phone():
    prefixes = ["090", "091", "098", "035", "038", "077", "086"]
    return f"{random.choice(prefixes)}{random.randint(1000000, 9999999)}"

# Hàm hỗ trợ tạo ngày gia nhập ngẫu nhiên (trong vòng 5 năm qua)
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
        "id": f"HSU-{str(i+1).zfill(3)}",
        "name": FULL_NAMES[i % len(FULL_NAMES)],
        "email": f"user{i+1}@hoasen.edu.vn",
        "phone": generate_fake_phone(),          # CẬP NHẬT: SỐ ĐIỆN THOẠI
        "created_at": generate_join_date(),       # CẬP NHẬT: NGÀY GIA NHẬP
        "dept": dept_choice,
        "position": loc_choice, 
        "role": role_choice,
        "status": "Hoạt động" if i % 10 != 0 else "Ngưng hoạt động"
    })

# --- 7. HÀM HỖ TRỢ ---
def get_filter_counts():
    """Trả về số lượng cho từng mục để hiển thị trong select filter"""
    counts = {
        "categories": {cat: len([d for d in ASSIGN_DATA if d['type'] == cat]) for cat in ASSET_TYPES},
        "departments": {dept: len([d for d in ASSIGN_DATA if d['department'] == dept]) for dept in DEPARTMENTS},
        "locations": {loc: len([d for d in ASSIGN_DATA if d['location'] == loc]) for loc in LOCATIONS},
        "status": {stat: len([d for d in ASSIGN_DATA if d['status'] == stat]) for stat in STATUS_OPTIONS},
        "total": len(ASSIGN_DATA)
    }
    return counts