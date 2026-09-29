# Hệ thống IoT giám sát & điều khiển qua MQTT

Bài 3 — Code giao diện và test chức năng. Hiện thực theo tài liệu
**SRS mô tả các công việc IOT** (ESP32 → Mosquitto → Backend → MySQL → Web Dashboard).

| Khối | Công nghệ | Thư mục |
|---|---|---|
| Backend | Python 3.13 + FastAPI + SQLAlchemy + paho-mqtt | `backend/` |
| Database | MySQL 8.0 | `db/` |
| Frontend | React 18 + Vite + Chart.js | `frontend/` |
| Giả lập phần cứng | paho-mqtt | `simulator/` |

---

## 1. Kiến trúc & luồng dữ liệu

```
              Data_Sensor                 WebSocket /ws/dashboard
ESP32  ────────────────────►  Mosquitto  ────►  FastAPI  ────────────────►  React
  ▲          Device_Response                       │                        Dashboard
  └──────────────────────────  Broker  ◄───────────┘   REST /api/...   ◄────────┘
              Device_Control                      │
                                                  ▼
                                              MySQL iot_db
```

- **Luồng cảm biến:** ESP32 publish `Data_Sensor` mỗi 5s → backend lưu 3 bản ghi `Data_sensor`
  → phát sự kiện WebSocket `sensor_data` → Dashboard cập nhật thẻ số liệu + biểu đồ.
- **Luồng điều khiển:** FE gọi `POST /api/actions/{device_id}` → backend ghi `Action` trạng thái
  `PENDING` + publish `Device_Control` → ESP32 thực thi, publish `Device_Response` → backend cập nhật
  `Action` thành `SUCCESS`, cập nhật `Device.is_active` → phát sự kiện `device_status` → FE lật công tắc.

Công tắc trên giao diện **không lật ngay khi bấm** mà chờ phản hồi thật từ thiết bị, đúng như
mục 4.3.5 SRS: *"giao diện luôn phản ánh trạng thái vật lý thật của thiết bị"*.

---

## 2. Cài đặt

### 2.1. Cơ sở dữ liệu

```bash
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p < db\schema.sql
```

Script tạo database `iot_db`, 5 bảng theo chương 3 SRS và dữ liệu khởi tạo
(tài khoản `hiep` / `123456`, 2 thiết bị, 3 cảm biến).

### 2.2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env          # sửa DB_PASSWORD và MQTT_HOST cho đúng máy
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

- API: <http://localhost:8000/api/...>
- Swagger UI: <http://localhost:8000/docs>

Sinh thêm dữ liệu mẫu cho hai trang lịch sử (tùy chọn):

```bash
cd backend && .venv\Scripts\python seed.py
```

### 2.3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Giao diện: <http://localhost:5173> (Vite proxy `/api` và `/ws` sang cổng 8000).

### 2.4. MQTT Broker

Mosquitto phải bật listener cổng **1884** và có tài khoản `hiep` / `123` khớp firmware.
Trong `mosquitto.conf`:

```conf
listener 1884
allow_anonymous false
password_file C:\Program Files\mosquitto\passwd
```

Tạo tài khoản:

```bash
"C:\Program Files\mosquitto\mosquitto_passwd.exe" -c "C:\Program Files\mosquitto\passwd" hiep
```

### 2.5. Giả lập ESP32 (khi chưa cắm phần cứng)

```bash
backend\.venv\Scripts\python simulator\esp32_sim.py
backend\.venv\Scripts\python simulator\esp32_sim.py --no-response   # để thử luồng TIMEOUT
```

---

## 3. Đặc tả API đã hiện thực

| Phương thức | Endpoint | Chức năng |
|---|---|---|
| POST | `/api/auth/login` | Xác thực, trả về JWT |
| GET | `/api/users/me` | Thông tin tài khoản đang đăng nhập |
| GET | `/api/sensor-data/latest` | Giá trị cảm biến mới nhất |
| GET | `/api/sensor-data` | Lịch sử cảm biến — `type,q,from,to,page,limit,sort` |
| GET | `/api/devices/status` | Trạng thái hiện tại của thiết bị |
| POST | `/api/actions/{device_id}` | Gửi lệnh bật/tắt, tạo bản ghi Action |
| GET | `/api/actions` | Lịch sử điều khiển — `device_id,status,action,q,from,to,page,limit,sort` |
| WS | `/ws/dashboard?token=<jwt>` | `sensor_data` \| `device_status` \| `device_offline` |

Mọi phản hồi có dạng `{ "success": bool, "data": ..., "message": str }`.
Mã lỗi dùng đúng Bảng 6 SRS: `200 / 201 / 400 / 401 / 404 / 503`.

---

## 4. Kịch bản kiểm thử chức năng

| # | Kịch bản | Cách thực hiện | Kết quả mong đợi |
|---|---|---|---|
| 1 | Đăng nhập đúng | `hiep` / `123456` | Vào Dashboard, nhận JWT |
| 2 | Đăng nhập sai | mật khẩu bất kỳ | `401`, hiện "Tên đăng nhập hoặc mật khẩu không đúng" |
| 3 | Token hết hạn/sai | xoá `iot_token` trong localStorage rồi F5 | Tự quay về màn hình đăng nhập |
| 4 | Cảm biến realtime | chạy simulator / cắm ESP32 | 3 thẻ số liệu và biểu đồ tự cập nhật mỗi 5s, không cần F5 |
| 5 | Điều khiển thiết bị | bấm công tắc Đèn | Công tắc khoá + "Đang chờ phản hồi…", sau đó lật sang BẬT |
| 6 | Ghi vết điều khiển | mở tab Action History | Có bản ghi mới, trạng thái `SUCCESS` |
| 7 | Thiết bị không phản hồi | chạy simulator với `--no-response`, bấm công tắc | Sau 10s: banner cảnh báo, Action chuyển `TIMEOUT`, công tắc giữ nguyên trạng thái cũ |
| 8 | Mất kết nối cảm biến | tắt simulator, chờ > 20s | Banner "Mất kết nối với thiết bị cảm biến", số liệu giữ nguyên giá trị cuối |
| 9 | Mất kết nối Broker | dừng service mosquitto rồi bấm công tắc | `503`, banner báo lỗi |
| 10 | Lọc theo loại cảm biến | Sensor Data → Loại = Độ ẩm | Chỉ còn dòng DHT11 / Độ ẩm, `total` giảm tương ứng |
| 11 | Lọc theo khoảng thời gian | đặt `Từ` > `Đến` | `400`, hiện "Khoảng thời gian không hợp lệ" |
| 12 | Tìm kiếm không ra dữ liệu | gõ tên cảm biến không tồn tại | Hiện "Không tìm thấy dữ liệu" |
| 13 | Phân trang | đổi Số dòng 8 → 20, bấm ‹ › | Số bản ghi/trang đúng, nút mờ ở đầu/cuối |
| 14 | Sắp xếp | đổi Mới nhất ↔ Cũ nhất | Thứ tự cột THỜI GIAN đảo lại |
| 15 | Xem profile | tab Profile | Hiển thị đúng họ tên, MSSV, lớp lấy từ `api/users/me` |

---

## 5. Ghi chú về khác biệt giữa SRS và hiện thực

Ba điểm dưới đây **tài liệu SRS cần cập nhật lại** cho khớp với hệ thống thật:

1. **Payload topic 2 & 3.** SRS (mục 4.2.2, 4.2.3) ghi `{"led":"ON","fan":"OFF"}`, tức gửi trạng thái
   của cả hai thiết bị trong một bản tin. Nhưng firmware ESP32 thực tế và API
   `POST api/actions/{device_id}` đều làm việc trên **một thiết bị mỗi lệnh**, dùng khoá
   `{"device_id":1,"action":"on"}`. Mã nguồn bám theo firmware. Đề nghị sửa lại payload mẫu trong SRS.

2. **`Device_Response` không có `action_id`.** Firmware chỉ trả `{device_id, action, status}` nên
   backend phải đối chiếu với bản ghi `Action` `PENDING` gần nhất của đúng thiết bị + đúng hành động
   (xem `backend/app/mqtt_client.py`, hàm `_handle_device_response`). Nếu muốn đối chiếu chắc chắn,
   nên bổ sung `action_id` vào payload topic 2 và cho ESP32 gửi ngược lại ở topic 3.

3. **Bảng `User` thiếu cột.** Bảng 1 SRS chỉ có `user_id, username, password`, trong khi endpoint
   `GET api/users/me` (mục 4.3.3.g) trả về `full_name`, `student_id`, `class`.
   `db/schema.sql` đã thêm 3 cột này — cần bổ sung vào Bảng 1 trong tài liệu.

Ngoài ra, hai điểm nhỏ nên thêm vào tài liệu cho khớp bản thiết kế giao diện (Hình 9, Hình 11):

- **Bảng 8** chưa có tham số `q` (tìm theo tên cảm biến) dù mục 5.2.3 có nêu "hỗ trợ tìm kiếm".
- Mục 4.3.3.f chưa liệt kê tham số `action`, `q`, `from`, `to` của `GET api/actions`,
  dù mục 5.2.4 và giao diện Action History đều dùng đến.

Một điểm cần thống nhất về **enum trạng thái**: SRS dùng `PENDING, SUCCESS, TIMEOUT`, nhưng bản
thiết kế giao diện Action History lại hiện nhãn "Thất bại" (`FAILED`). Mã nguồn theo SRS
(`TIMEOUT`, hiển thị "Quá hạn"), không có `FAILED`.
