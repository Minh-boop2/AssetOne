# data.py
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

# --- 2. DỮ LIỆU CẤP PHÁT & TRẠNG THÁI ---
_BASE_SAMPLES = [
    {"id": "ASG-001", "asset_code": "LAP-001", "asset": "Laptop Dell XPS 15", "type": "Laptop", "receiver": "Nguyễn Văn A", "department": "Phòng Kỹ Thuật", "location": "Tầng 3", "date": "24/03/2026", "warranty": "12/12/2026", "status": "Hoàn thành"},
    {"id": "ASG-002", "asset_code": "PRI-002", "asset": "Máy in HP LaserJet", "type": "Máy in", "receiver": "Lê Thị B", "department": "Phòng Hành Chính", "location": "Tầng 2", "date": "25/03/2026", "warranty": "08/11/2025", "status": "Hoàn thành"},
    {"id": "ASG-003", "asset_code": "NET-004", "asset": "Router Mikrotik RB4011", "type": "Thiết bị mạng", "receiver": "Phòng IT", "department": "Phòng IT", "location": "Phòng Server", "date": "09/04/2026", "warranty": "15/03/2026", "status": "Chờ duyệt"},
    {"id": "ASG-004", "asset_code": "LAP-005", "asset": "Laptop MacBook Pro M3", "type": "Laptop", "receiver": "Trần Văn C", "department": "Phòng Thiết Kế", "location": "Tầng 4", "date": "10/04/2026", "warranty": "01/09/2027", "status": "Hoàn thành"}
]

ASSIGN_DATA = []
for i in range(128):
    sample = _BASE_SAMPLES[i % len(_BASE_SAMPLES)].copy()
    new_id_number = i + 1
    sample["id"] = f"ASG-{str(new_id_number).zfill(3)}"
    
    prefix_map = {"Laptop": "LAP", "Máy in": "PRI", "Thiết bị mạng": "NET", "Màn hình": "MON"}
    prefix = prefix_map.get(sample["type"], "AST")
    sample["asset_code"] = f"{prefix}-{str(new_id_number).zfill(3)}"
    
    if i > 4 and i % 15 == 0:
        sample["status"] = "Chờ duyệt"
    ASSIGN_DATA.append(sample)

# --- 3. NHẬT KÝ HỆ THỐNG ---
DATABASE_LOGS = [
    {"id": "L001", "user": "Admin", "dept": "IT", "action": "Cấp phát", "asset": "Laptop Dell XPS 15", "time": "2026-04-09 10:00", "type": "Thiết bị"},
    # ... (giữ nguyên các logs khác của bạn)
]

# --- 4. DANH MỤC HỖ TRỢ (Dùng cho Filter) ---
DEPARTMENTS = ["Phòng Kỹ Thuật", "Phòng Hành Chính", "Phòng IT", "Phòng Thiết Kế", "Phòng Kế Toán", "Phòng Nhân Sự", "Marketing"]
ASSET_TYPES = ["Laptop", "Máy in", "Thiết bị mạng", "Màn hình", "Phụ kiện"]
STATUS_OPTIONS = ["Hoàn thành", "Chờ duyệt", "Đang xử lý", "Đã hủy"]
# --- 5. DANH SÁCH NHÂN SỰ (Dùng cho Quản lý người dùng) ---
USER_LIST_DATA = [
    {"full_name": "Nguyễn Văn Admin", "email": "admin@hoasen.edu.vn", "department": "Phòng IT", "role": "Admin", "last_active": "Vừa xong", "status": "Active"},
    {"full_name": "Lê Thị Đào Tạo", "email": "daotao@hoasen.edu.vn", "department": "Phòng Đào Tạo", "role": "Staff", "last_active": "2 giờ trước", "status": "Active"},
    {"full_name": "Trần Văn Kỹ Thuật", "email": "kythuat@hoasen.edu.vn", "department": "Phòng Kỹ Thuật", "role": "Manager", "last_active": "1 ngày trước", "status": "Inactive"},
    {"full_name": "Phạm Minh Tài Chính", "email": "taichinh@hoasen.edu.vn", "department": "Phòng Kế Toán", "role": "Staff", "last_active": "3 giờ trước", "status": "Active"},
]