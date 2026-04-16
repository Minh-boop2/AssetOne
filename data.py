# data.py
from datetime import datetime

# Kho hàng chứa thông số kỹ thuật (Dùng cho List chọn và Xem chi tiết)
INVENTORY_LIST = [
    {"name": "Laptop Dell XPS 15", "spec": "Core i7, 16GB RAM, 512GB SSD", "warranty": "12 tháng"},
    {"name": "Laptop MacBook Pro M3", "spec": "Apple M3 Chip, 8GB RAM, 512GB SSD", "warranty": "24 tháng"},
    {"name": "Màn hình LG 27 inch", "spec": "4K UHD, IPS Panel", "warranty": "36 tháng"},
    {"name": "Chuột Logitech M331", "spec": "Silent Wireless Mouse", "warranty": "6 tháng"},
    {"name": "Bàn phím cơ AKKO 3068", "spec": "Bluetooth 5.0, Cherry Switch", "warranty": "12 tháng"},
    {"name": "Webcam Logitech C922", "spec": "Full HD 1080p, 60fps", "warranty": "12 tháng"}
]

# Dữ liệu cấp phát (Assign)
ASSIGN_DATA = [
    {"id": "ASG-001", "asset": "Laptop Dell XPS 15", "receiver": "Nguyễn Văn A", "date": "24/03/2026", "status": "Hoàn thành"},
    {"id": "ASG-002", "asset": "Màn hình LG 27 inch", "receiver": "Trần Thị B", "date": "25/03/2026", "status": "Chờ duyệt"},
    {"id": "ASG-003", "asset": "Webcam Logitech C922", "receiver": "Nguyễn Văn D", "date": "09/04/2026", "status": "Chờ duyệt"},
]

# Nhật ký cho trang Report
DATABASE_LOGS = [
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