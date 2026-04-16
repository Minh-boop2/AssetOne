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
]