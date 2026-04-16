# data.py
from datetime import datetime

# --- 1. KHO HÀNG CHỨA THÔNG SỐ KỸ THUẬT (Giữ nguyên gốc) ---
INVENTORY_LIST = [
    {
        "name": "Laptop Dell XPS 15", 
        "spec": "Core i7-12700H, 16GB RAM, 512GB SSD NVMe, RTX 3050Ti", 
        "warranty": "12 tháng"
    },
    {
        "name": "Laptop MacBook Pro M3", 
        "spec": "Apple M3 8-Core CPU, 10-Core GPU, 8GB RAM, 512GB SSD", 
        "warranty": "24 tháng"
    },
    {
        "name": "Màn hình LG 27 inch", 
        "spec": "27UP850-W, 4K UHD, IPS 400nits, USB-C 96W", 
        "warranty": "36 tháng"
    },
    {
        "name": "Chuột Logitech M331", 
        "spec": "Silent Wireless, 1000 DPI, 2.4GHz Receiver", 
        "warranty": "6 tháng"
    },
    {
        "name": "Bàn phím cơ AKKO 3068", 
        "spec": "Multi-modes (BT5.0/2.4G/Type-C), Gateron Orange Switch", 
        "warranty": "12 tháng"
    },
    {
        "name": "Webcam Logitech C922", 
        "spec": "Full HD 1080p 30fps / 720p 60fps, Stereo Audio", 
        "warranty": "12 tháng"
    },
    {
        "name": "Máy in HP LaserJet", 
        "spec": "In laser trắng đen, 21 trang/phút, Khay giấy 150 tờ", 
        "warranty": "12 tháng"
    },
    {
        "name": "Router Mikrotik RB4011", 
        "spec": "10x Gigabit ports, 1x SFP+ port, Quad-core 1.4GHz CPU", 
        "warranty": "24 tháng"
    }
]

# --- 2. DỮ LIỆU CẤP PHÁT & TRẠNG THÁI ---
# Bước 1: Giữ nguyên 4 dữ liệu mẫu ban đầu của bạn
_BASE_SAMPLES = [
    {
        "id": "ASG-001", 
        "asset_code": "LAP-001",
        "asset": "Laptop Dell XPS 15", 
        "type": "laptop",
        "receiver": "Nguyễn Văn A", 
        "department": "Phòng Kỹ Thuật",
        "location": "Tầng 3",
        "date": "24/03/2026", 
        "warranty": "12/12/2026",
        "status": "Hoàn thành"
    },
    {
        "id": "ASG-002", 
        "asset_code": "PRI-002",
        "asset": "Máy in HP LaserJet", 
        "type": "printer",
        "receiver": "Lê Thị B", 
        "department": "Phòng Hành Chính",
        "location": "Tầng 2",
        "date": "25/03/2026", 
        "warranty": "08/11/2025",
        "status": "Hoàn thành"
    },
    {
        "id": "ASG-003", 
        "asset_code": "NET-004",
        "asset": "Router Mikrotik RB4011", 
        "type": "router",
        "receiver": "Phòng IT", 
        "department": "Hạ tầng mạng",
        "location": "Phòng Server",
        "date": "09/04/2026", 
        "warranty": "15/03/2026",
        "status": "Chờ duyệt"
    },
    {
        "id": "ASG-004", 
        "asset_code": "LAP-005",
        "asset": "Laptop MacBook Pro M3", 
        "type": "laptop",
        "receiver": "Trần Văn C", 
        "department": "Phòng Thiết Kế",
        "location": "Tầng 4",
        "date": "10/04/2026", 
        "warranty": "01/09/2027",
        "status": "Hoàn thành"
    }
]

# Bước 2: Tạo danh sách 128 tài sản tự động dựa trên mẫu của bạn
ASSIGN_DATA = []
for i in range(128):
    # Lấy mẫu xoay vòng từ 4 mẫu gốc để đảm bảo dữ liệu đa dạng
    sample = _BASE_SAMPLES[i % len(_BASE_SAMPLES)].copy()
    
    # Cập nhật lại ID và Asset Code để không bị trùng lặp
    new_id_number = i + 1
    sample["id"] = f"ASG-{str(new_id_number).zfill(3)}"
    
    # Tạo asset_code giả lập dựa trên loại thiết bị
    prefix = sample["type"][:3].upper()
    sample["asset_code"] = f"{prefix}-{str(new_id_number).zfill(3)}"
    
    ASSIGN_DATA.append(sample)

# --- 3. NHẬT KÝ HỆ THỐNG (Giữ nguyên gốc) ---
DATABASE_LOGS = [
    {
        "id": "L001", 
        "user": "Admin", 
        "dept": "IT", 
        "action": "Cấp phát", 
        "asset": "Laptop Dell XPS 15", 
        "time": "2026-04-09 10:00", 
        "type": "Thiết bị"
    },
    {
        "id": "L002", 
        "user": "Admin", 
        "dept": "IT", 
        "action": "Duyệt yêu cầu", 
        "asset": "Máy in HP LaserJet", 
        "time": "2026-04-10 14:30", 
        "type": "Thiết bị"
    }
    {"id": "L001", "asset_name": "Laptop Dell XPS 15", "type": "Bàn giao", "detail": "Cấp mới cho nhân viên mới", "dept": "IT", "user": "Châu Ngọc Đức", "status": "Hoàn thành", "time": "2026-04-15 08:30"},
    {"id": "L002", "asset_name": "MacBook Pro M2", "type": "Bảo trì", "detail": "Thay pin và vệ sinh máy", "dept": "Marketing", "user": "Trần Minh", "status": "Đang xử lý", "time": "2026-04-15 09:15"},
    {"id": "L003", "asset_name": "Màn hình Dell 24 inch", "type": "Bàn giao", "detail": "Cấp cho phòng kế toán", "dept": "Kế toán", "user": "Nguyễn An", "status": "Hoàn thành", "time": "2026-04-15 10:00"},
    {"id": "L004", "asset_name": "Máy in HP Laser", "type": "Bảo trì", "detail": "Sửa lỗi kẹt giấy", "dept": "Nhân sự", "user": "Lê Hoa", "status": "Hoàn thành", "time": "2026-04-14 14:20"},
    {"id": "L005", "asset_name": "iPad Air 5", "type": "Thay đổi", "detail": "Nâng cấp dung lượng iCloud", "dept": "Thiết kế", "user": "Phạm Hùng", "status": "Hoàn thành", "time": "2026-04-14 16:45"},
    {"id": "L006", "asset_name": "Laptop ThinkPad X1", "type": "Bàn giao", "detail": "Cấp cho trưởng phòng IT", "dept": "IT", "user": "Đặng Tuấn", "status": "Hoàn thành", "time": "2026-04-13 08:00"},
    {"id": "L007", "asset_name": "Bàn phím cơ Logi", "type": "Thay đổi", "detail": "Đổi sang mẫu không dây", "dept": "IT", "user": "Châu Ngọc Đức", "status": "Hoàn thành", "time": "2026-04-13 11:30"},
    {"id": "L008", "asset_name": "Projector Sony", "type": "Bảo trì", "detail": "Thay bóng đèn chiếu", "dept": "Hành chính", "user": "Hoàng Nam", "status": "Đang xử lý", "time": "2026-04-12 13:00"},
    {"id": "L009", "asset_name": "Workstation HP", "type": "Bàn giao", "detail": "Lắp đặt cho phòng Server", "dept": "IT", "user": "Admin", "status": "Hoàn thành", "time": "2026-04-12 15:20"},
    {"id": "L010", "asset_name": "iPhone 15 Pro", "type": "Bàn giao", "detail": "Cấp thiết bị test app", "dept": "IT", "user": "Võ Thị Sáu", "status": "Hoàn thành", "time": "2026-04-11 09:45"},
    {"id": "L011", "asset_name": "Máy Scan Canon", "type": "Bảo trì", "detail": "Vệ sinh mặt kính", "dept": "Kế toán", "user": "Bùi Mai", "status": "Hoàn thành", "time": "2026-04-11 10:10"},
    {"id": "L012", "asset_name": "PC Dell Optiplex", "type": "Thay đổi", "detail": "Nâng cấp lên 16GB RAM", "dept": "Kế toán", "user": "Trần Long", "status": "Hoàn thành", "time": "2026-04-10 14:00"},
    {"id": "L013", "asset_name": "Router Cisco", "type": "Bảo trì", "detail": "Cấu hình lại VLAN", "dept": "IT", "user": "Lý Thông", "status": "Đang xử lý", "time": "2026-04-10 16:30"},
    {"id": "L014", "asset_name": "Màn hình LG UltraWide", "type": "Bàn giao", "detail": "Cấp cho Designer", "dept": "Marketing", "user": "Phan Thiết", "status": "Hoàn thành", "time": "2026-04-09 08:15"},
    {"id": "L015", "asset_name": "UPS Santak 2kVA", "type": "Bảo trì", "detail": "Thay bình ắc quy", "dept": "IT", "user": "Châu Ngọc Đức", "status": "Hoàn thành", "time": "2026-04-09 11:00"},
]