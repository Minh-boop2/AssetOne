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
    {"id": "L001", "user": "Admin", "dept": "IT", "action": "Cấp phát", "asset": "Laptop Dell", "time": "2026-04-09 10:00", "type": "Thiết bị"},
]