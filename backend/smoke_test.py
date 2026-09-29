"""Kiểm thử tự động toàn bộ luồng nghiệp vụ (Bài 3 - test chức năng).

Điều kiện: MySQL đã có iot_db, backend đang chạy ở cổng 8000,
và simulator/esp32_sim.py (hoặc ESP32 thật) đang kết nối tới broker.

    backend\\.venv\\Scripts\\python.exe smoke_test.py
"""

import asyncio
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

import websockets

sys.stdout.reconfigure(encoding="utf-8")   # console Windows mặc định cp1252, không in được tiếng Việt

BASE = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/dashboard"
USERNAME, PASSWORD = "hiep", "123456"

passed = failed = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}" + (f" -> {detail}" if detail else ""))


def call(method: str, path: str, token: str | None = None, body: dict | None = None, **params):
    """Trả về (http_status, payload_json)."""
    url = BASE + path
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)

    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if data:
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


# ---------------------------------------------------------------------------
def test_auth() -> str:
    print("\n1. Xác thực (POST /api/auth/login)")

    code, body = call("POST", "/api/auth/login", body={"username": USERNAME, "password": PASSWORD})
    check("Đăng nhập đúng -> 200 + JWT", code == 200 and bool(body.get("data", {}).get("token")), f"{code} {body}")
    token = body.get("data", {}).get("token", "")

    code, body = call("POST", "/api/auth/login", body={"username": USERNAME, "password": "sai-mat-khau"})
    check("Đăng nhập sai -> 401", code == 401, str(code))

    code, _ = call("GET", "/api/users/me")
    check("Thiếu token -> 401", code == 401, str(code))

    code, _ = call("GET", "/api/users/me", token="token.gia.mao")
    check("Token giả -> 401", code == 401, str(code))

    return token


def test_profile(token: str) -> None:
    print("\n2. Profile (GET /api/users/me)")
    code, body = call("GET", "/api/users/me", token)
    data = body.get("data", {})
    check("Trả về 200", code == 200, str(code))
    check("Đủ trường full_name/student_id/class",
          all(data.get(k) for k in ("full_name", "student_id", "class")), str(data))


def test_sensor(token: str) -> None:
    print("\n3. Dữ liệu cảm biến")

    code, body = call("GET", "/api/sensor-data/latest", token)
    data = body.get("data", {})
    check("latest -> 200", code == 200, str(code))
    check("latest có đủ temp/humid/light",
          all(k in data for k in ("temp", "humid", "light")), str(data))

    code, body = call("GET", "/api/sensor-data", token, page=1, limit=8, sort="desc")
    d = body.get("data", {})
    check("Phân trang trả đúng limit", code == 200 and len(d.get("items", [])) <= 8, str(code))
    check("Có trường total", "total" in d, str(d.keys()))

    code, body = call("GET", "/api/sensor-data", token, type="humid", limit=20)
    items = body.get("data", {}).get("items", [])
    check("Lọc type=humid", items and all(i["type"] == "humid" for i in items), f"{len(items)} bản ghi")

    code, body = call("GET", "/api/sensor-data", token, sort="asc", limit=5)
    asc = [i["recorded_at"] for i in body.get("data", {}).get("items", [])]
    check("sort=asc tăng dần theo thời gian", asc == sorted(asc), str(asc[:2]))

    code, body = call("GET", "/api/sensor-data", token, sort="desc", limit=5)
    desc = [i["recorded_at"] for i in body.get("data", {}).get("items", [])]
    check("sort=desc giảm dần theo thời gian", desc == sorted(desc, reverse=True), str(desc[:2]))

    now = datetime.now()
    code, _ = call("GET", "/api/sensor-data", token,
                   **{"from": now.isoformat(), "to": (now - timedelta(days=1)).isoformat()})
    check("from > to -> 400", code == 400, str(code))

    code, _ = call("GET", "/api/sensor-data", token, type="khong-ton-tai")
    check("type không hợp lệ -> 400", code == 400, str(code))

    code, body = call("GET", "/api/sensor-data", token, q="KHONG_CO_CAM_BIEN_NAY")
    check("Tìm kiếm không ra -> total = 0", body.get("data", {}).get("total") == 0, str(body))


def test_devices(token: str) -> list:
    print("\n4. Trạng thái thiết bị (GET /api/devices/status)")
    code, body = call("GET", "/api/devices/status", token)
    devices = body.get("data", [])
    check("Trả về 200", code == 200, str(code))
    check("Có đủ 2 thiết bị", len(devices) == 2, str(devices))
    check("status chỉ nhận on/off", all(d["status"] in ("on", "off") for d in devices), str(devices))
    return devices


def test_actions(token: str, devices: list) -> None:
    print("\n5. Điều khiển thiết bị & lịch sử")

    code, _ = call("POST", "/api/actions/999", token, body={"action": "on"})
    check("device_id không tồn tại -> 404", code == 404, str(code))

    code, _ = call("POST", "/api/actions/1", token, body={"action": "bay-gio"})
    check("action không hợp lệ -> 400", code == 400, str(code))

    device = devices[0]
    target = "off" if device["status"] == "on" else "on"
    code, body = call("POST", f"/api/actions/{device['device_id']}", token, body={"action": target})
    data = body.get("data", {})
    check("Gửi lệnh -> 201", code == 201, f"{code} {body}")
    check("Phản hồi có trạng thái PENDING", data.get("status") == "PENDING", str(data))
    action_id = data.get("action_id")

    print("     ...chờ 4s để ESP32 phản hồi qua topic Device_Response")
    import time
    time.sleep(4)

    code, body = call("GET", "/api/actions", token, limit=50)
    items = body.get("data", {}).get("items", [])
    record = next((i for i in items if i["action_id"] == action_id), None)
    check("Lệnh đã được ghi vào lịch sử", record is not None, f"action_id={action_id}")
    if record:
        check("Trạng thái chuyển PENDING -> SUCCESS", record["status"] == "SUCCESS", record["status"])

    code, body = call("GET", "/api/devices/status", token)
    now_status = next(d["status"] for d in body["data"] if d["device_id"] == device["device_id"])
    check("Trạng thái thiết bị đã đổi theo lệnh", now_status == target, f"mong đợi {target}, nhận {now_status}")

    code, body = call("GET", "/api/actions", token, device_id=device["device_id"], limit=20)
    items = body.get("data", {}).get("items", [])
    check("Lọc theo device_id", all(i["device_id"] == device["device_id"] for i in items), str(len(items)))

    code, body = call("GET", "/api/actions", token, status="SUCCESS", limit=20)
    items = body.get("data", {}).get("items", [])
    check("Lọc theo status=SUCCESS", all(i["status"] == "SUCCESS" for i in items), str(len(items)))

    code, _ = call("GET", "/api/actions", token, status="FAILED")
    check("status ngoài enum SRS -> 400", code == 400, str(code))


async def test_websocket(token: str) -> None:
    print("\n6. Kênh WebSocket /ws/dashboard")

    try:
        async with websockets.connect(f"{WS_URL}?token=sai-token"):
            check("Token sai bị từ chối", False, "kết nối vẫn mở")
    except Exception:
        check("Token sai bị từ chối", True)

    try:
        async with websockets.connect(f"{WS_URL}?token={token}") as ws:
            check("Kết nối bằng token hợp lệ", True)
            print("     ...chờ tối đa 12s để nhận sự kiện sensor_data")
            raw = await asyncio.wait_for(ws.recv(), timeout=12)
            msg = json.loads(raw)
            check("Nhận được sự kiện realtime", msg.get("event") in
                  ("sensor_data", "device_status", "device_offline"), str(msg)[:120])
            if msg.get("event") == "sensor_data":
                check("sensor_data đủ temp/humid/light/at",
                      all(k in msg["data"] for k in ("temp", "humid", "light", "at")), str(msg["data"]))
    except asyncio.TimeoutError:
        check("Nhận được sự kiện realtime", False, "hết 12s không có bản tin - simulator/ESP32 có đang chạy không?")
    except Exception as e:
        check("Kết nối bằng token hợp lệ", False, str(e))


def main() -> None:
    print("=" * 62)
    print(" KIỂM THỬ CHỨC NĂNG HỆ THỐNG IoT")
    print("=" * 62)

    code, body = call("GET", "/api/health")
    if code != 200:
        sys.exit("Backend chưa chạy. Khởi động: uvicorn app.main:app --port 8000")
    if not body["data"]["mqtt_connected"]:
        print("  [CẢNH BÁO] Backend chưa kết nối được MQTT Broker - các test điều khiển sẽ trượt.\n")

    token = test_auth()
    if not token:
        sys.exit("Không lấy được token, dừng.")

    test_profile(token)
    test_sensor(token)
    devices = test_devices(token)
    test_actions(token, devices)
    asyncio.run(test_websocket(token))

    print("\n" + "=" * 62)
    print(f" KẾT QUẢ: {passed} PASS / {failed} FAIL")
    print("=" * 62)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
