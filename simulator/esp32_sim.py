"""Trình giả lập ESP32 - dùng để kiểm thử chức năng khi chưa cắm phần cứng.

Hành vi sao chép đúng firmware thật (sketch Arduino):
  - cứ 5 giây publish {"temp","humid","light"} lên topic Data_Sensor
  - subscribe Device_Control, nhận {"device_id","action"}
  - publish lại {"device_id","action","status":"SUCCESS"} lên Device_Response

Chạy:
    backend\\.venv\\Scripts\\python.exe simulator\\esp32_sim.py
Thêm cờ --no-response để thử luồng ngoại lệ TIMEOUT (thiết bị không phản hồi).
"""

import argparse
import json
import random
import time

from paho.mqtt import client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

BROKER_HOST = "192.168.137.1"
BROKER_PORT = 1884
USERNAME = "hiep"
PASSWORD = "123"

TOPIC_SENSOR = "Data_Sensor"
TOPIC_CONTROL = "Device_Control"
TOPIC_RESPONSE = "Device_Response"

state = {1: False, 2: False}   # 1 = Đèn (GPIO2), 2 = Quạt (GPIO22)


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"[SIM] Đã kết nối broker {BROKER_HOST}:{BROKER_PORT}")
        client.subscribe(TOPIC_CONTROL)
    else:
        print(f"[SIM] Kết nối thất bại, reason_code={reason_code}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        return

    device_id = payload.get("device_id")
    action = payload.get("action")
    if device_id not in state or action not in ("on", "off"):
        return

    state[device_id] = action == "on"
    print(f"[SIM] Nhận lệnh device_id={device_id} action={action}")

    if userdata["respond"]:
        time.sleep(0.3)   # mô phỏng độ trễ thực thi của thiết bị
        resp = {"device_id": device_id, "action": action, "status": "SUCCESS"}
        client.publish(TOPIC_RESPONSE, json.dumps(resp))
        print(f"[SIM] Phản hồi {resp}")
    else:
        print("[SIM] --no-response: cố tình không phản hồi để thử TIMEOUT")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-response", action="store_true", help="Không gửi Device_Response")
    parser.add_argument("--host", default=BROKER_HOST)
    parser.add_argument("--port", type=int, default=BROKER_PORT)
    args = parser.parse_args()

    client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="ESP32_SIM")
    client.user_data_set({"respond": not args.no_response})
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.host, args.port, keepalive=60)
    client.loop_start()

    temp, humid, light = 28.0, 75.0, 1800
    try:
        while True:
            temp = round(min(35, max(22, temp + random.uniform(-0.6, 0.6))), 1)
            humid = round(min(95, max(45, humid + random.uniform(-1.5, 1.5))), 1)
            light = min(4095, max(0, light + random.randint(-200, 200)))

            payload = {"temp": temp, "humid": humid, "light": light}
            client.publish(TOPIC_SENSOR, json.dumps(payload))
            print(f"[SIM] Đã gửi: {payload}")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n[SIM] Dừng.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
