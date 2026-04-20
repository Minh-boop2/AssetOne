from datetime import datetime

# --- 1. KHO HÀNG CHỨA THÔNG SỐ KỸ THUẬT ---
INVENTORY_LIST = [
    {"name": "Laptop Dell XPS 15", "spec": "Core i7-12700H, 16GB RAM, 512GB SSD NVMe, RTX 3050Ti", "warranty": "12 tháng"},
    {"name": "Laptop MacBook Pro M3", "spec": "Apple M3 8-Core CPU, 10-Core GPU, 8GB RAM, 512GB SSD", "warranty": "24 tháng"},
    {"name": "Màn hình LG 27 inch", "spec": "27UP850-W, 4K UHD, IPS 400nits, USB-C 96W", "warranty": "36 tháng"},
    {"name": "Chuột Logitech M331", "spec": "Silent Wireless, 1000 DPI, 2.4GHz Receiver", "warranty": "6 tháng"},
    {"name": "Bàn phím cơ AKKO 3068", "spec": "Multi-modes (BT5.0/2.4G/Type-C), Gateron Orange Switch", "warranty": "12 tháng"},
    {"name": "Webcam Logitech C922", "spec": "Full HD 1080p 30fps / 720p 60fps, Stereo Audio", "warranty": "12 tháng"},
    {"name": "Máy in HP LaserJet", "spec": "In laser trắng đen, 21 trang/phút, Khay giấy 150 tờ", "warranty": "12 tháng"},
    {"name": "Router Mikrotik RB4011", "spec": "10x Gigabit ports, 1x SFP+ port, Quad-core 1.4GHz CPU", "warranty": "24 tháng"}
]

# --- 2. DANH MỤC HỖ TRỢ (Dùng cho các ô lọc và Select) ---
DEPARTMENTS = ["Phòng Kỹ Thuật", "Phòng Hành Chính", "Phòng IT", "Phòng Thiết Kế", "Phòng Kế Toán", "Phòng Nhân Sự", "Marketing", "Phòng Đào Tạo"]
ASSET_TYPES = ["Laptop", "Máy in", "Thiết bị mạng", "Màn hình", "Phụ kiện"]
STATUS_OPTIONS = ["Hoàn thành", "Chờ duyệt", "Đang xử lý", "Đã hủy"]
ROLES = ["Admin", "Manager", "Staff"]
USER_STATUS_OPTIONS = ["Hoạt động", "Ngưng hoạt động"]

# --- 3. DỮ LIỆU CẤP PHÁT & TRẠNG THÁI (Tạo tự động 128 mẫu) ---
_BASE_SAMPLES = [
    {"id": "ASG-001", "asset_code": "LAP-001", "asset": "Laptop Dell XPS 15", "type": "Laptop", "receiver": "Nguyễn Văn A", "department": "Phòng Kỹ Thuật", "location": "Tầng 3", "date": "24/03/2026", "warranty": "12/12/2026", "status": "Hoàn thành"},
    {"id": "ASG-002", "asset_code": "PRI-002", "asset": "Máy in HP LaserJet", "type": "Máy in", "receiver": "Lê Thị B", "department": "Phòng Hành Chính", "location": "Tầng 2", "date": "25/03/2026", "warranty": "08/11/2025", "status": "Hoàn thành"},
    {"id": "ASG-003", "asset_code": "NET-004", "asset": "Router Mikrotik RB4011", "type": "Thiết bị mạng", "receiver": "Phạm Gia Bảo", "department": "Phòng IT", "location": "Phòng Server", "date": "09/04/2026", "warranty": "15/03/2026", "status": "Chờ duyệt"},
    {"id": "ASG-004", "asset_code": "LAP-005", "asset": "Laptop MacBook Pro M3", "type": "Laptop", "receiver": "Trần Văn C", "department": "Phòng Thiết Kế", "location": "Tầng 4", "date": "10/04/2026", "warranty": "01/09/2027", "status": "Hoàn thành"}
]

ASSIGN_DATA = []
prefix_map = {"Laptop": "LAP", "Máy in": "PRI", "Thiết bị mạng": "NET", "Màn hình": "MON", "Phụ kiện": "ACC"}

for i in range(128):
    sample = _BASE_SAMPLES[i % len(_BASE_SAMPLES)].copy()
    new_id_number = i + 1
    sample["id"] = f"ASG-{str(new_id_number).zfill(3)}"
    
    # Tạo mã tài sản chuyên nghiệp
    prefix = prefix_map.get(sample["type"], "AST")
    sample["asset_code"] = f"{prefix}-{str(new_id_number).zfill(3)}"
    
    # Tạo ngẫu nhiên một số trạng thái Chờ duyệt để test chức năng duyệt
    if i > 4 and i % 15 == 0:
        sample["status"] = "Chờ duyệt"
        
    ASSIGN_DATA.append(sample)

# --- 4. NHẬT KÝ HỆ THỐNG (Logs hiển thị ở Dashboard) ---
DATABASE_LOGS = [
    {"id": "L001", "user": "Admin", "dept": "IT", "action": "Cấp phát", "asset": "Laptop Dell XPS 15", "time": "2026-04-09 10:00", "type": "Thiết bị"},
    {"id": "L002", "user": "Admin", "dept": "IT", "action": "Cập nhật nhân sự", "asset": "Trần Văn Nam", "time": "2026-04-10 08:30", "type": "Nhân sự"},
    {"id": "L003", "asset_name": "Màn hình Dell 24 inch", "type": "Bàn giao", "detail": "Cấp cho phòng kế toán", "dept": "Kế toán", "user": "Nguyễn An", "status": "Hoàn thành", "time": "2026-04-15 10:00"},
    {"id": "L004", "asset_name": "Máy in HP Laser", "type": "Bảo trì", "detail": "Sửa lỗi kẹt giấy", "dept": "Nhân sự", "user": "Lê Hoa", "status": "Hoàn thành", "time": "2026-04-14 14:20"},
    {"id": "L005", "asset_name": "iPad Air 5", "type": "Thay đổi", "detail": "Nâng cấp dung lượng iCloud", "dept": "Thiết kế", "user": "Phạm Hùng", "status": "Hoàn thành", "time": "2026-04-14 16:45"},
    {"id": "L006", "asset_name": "Laptop ThinkPad X1", "type": "Bàn giao", "detail": "Cấp cho trưởng phòng IT", "dept": "IT", "user": "Đặng Tuấn", "status": "Hoàn thành", "time": "2026-04-13 08:00"},
    {"id": "L007", "asset_name": "Bàn phím cơ Logi", "type": "Thay đổi", "detail": "Đổi sang mẫu không dây", "dept": "IT", "user": "Châu Ngọc Đức", "status": "Hoàn thành", "time": "2026-04-13 11:30"},
    {"id": "L008", "asset_name": "Projector Sony", "type": "Bảo trì", "detail": "Thay bóng đèn chiếu", "dept": "Hành chính", "user": "Hoàng Nam", "status": "Đang xử lý", "time": "2026-04-12 13:00"},
    {"id": "L009", "asset_name": "Workstation HP", "type": "Bàn giao", "detail": "Lắp đặt cho phòng Server", "dept": "IT", "user": "Admin", "status": "Hoàn thành", "time": "2026-04-12 15:20"},
    {"id": "L010", "asset_name": "iPhone 15 Pro", "type": "Bàn giao", "detail": "Cấp thiết bị test app", "dept": "IT", "user": "Võ Thị Sáu", "status": "Hoàn thành", "time": "2026-04-11 09:45"},
]

# --- 5. DANH SÁCH NHÂN SỰ ---
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

USER_LIST_DATA = []
name_index = 0

# Tạo Admin và Manager cho từng phòng ban (16 người đầu tiên)
for idx, dept in enumerate(DEPARTMENTS):
    # Mỗi phòng ban 1 Admin
    USER_LIST_DATA.append({
        "id": f"HSU-A{idx+1:03d}",
        "name": FULL_NAMES[name_index],
        "email": f"admin.{idx+1}@hoasen.edu.vn",
        "dept": dept,
        "role": "Admin",
        "status": "Hoạt động"
    })
    name_index += 1
    
    # Mỗi phòng ban 1 Manager
    USER_LIST_DATA.append({
        "id": f"HSU-M{idx+1:03d}",
        "name": FULL_NAMES[name_index],
        "email": f"manager.{idx+1}@hoasen.edu.vn",
        "dept": dept,
        "role": "Manager",
        "status": "Hoạt động"
    })
    name_index += 1

# Thêm các nhân viên còn lại cho đủ số lượng 65 người
for i in range(len(USER_LIST_DATA), 65):
    dept = DEPARTMENTS[i % len(DEPARTMENTS)]
    USER_LIST_DATA.append({
        "id": f"HSU-{i+1:03d}",
        "name": FULL_NAMES[name_index],
        "email": f"staff.{i+1}@hoasen.edu.vn",
        "dept": dept,
        "role": "Staff",
        "status": "Hoạt động"
    })
    name_index += 1