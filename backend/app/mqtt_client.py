"""Cầu nối MQTT <-> Database <-> WebSocket (CHƯƠNG 4 SRS).

    Data_Sensor      HW -> BE : {"temp":28.5,"humid":75.0,"light":1024}
    Device_Control   BE -> HW : {"device_id":1,"action":"on"}
    Device_Response  HW -> BE : {"device_id":1,"action":"on","status":"SUCCESS"}

Payload topic 2/3 theo đúng firmware ESP32 hiện tại (xem ghi chú trong README).
paho-mqtt chạy loop riêng trên thread nền, nên mọi thao tác DB ở đây dùng
SessionLocal riêng và đẩy sự kiện WebSocket qua manager.broadcast_threadsafe().
"""

import json
import logging
from datetime import datetime

from paho.mqtt import client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from sqlalchemy import select

from .config import settings
from .database import SessionLocal
from .models import SENSOR_MAP, Action, DataSensor, Device
from .ws import manager

log = logging.getLogger("mqtt")

_client: mqtt.Client | None = None
last_sensor_at: datetime | None = None  # phục vụ watchdog device_offline


def is_connected() -> bool:
    return _client is not None and _client.is_connected()


# ---------------------------------------------------------------- callbacks
def _on_connect(client: mqtt.Client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        log.info("Đã kết nối MQTT Broker %s:%s", settings.mqtt_host, settings.mqtt_port)
        client.subscribe([(settings.topic_sensor, 0), (settings.topic_response, 0)])
    else:
        log.error("Kết nối MQTT thất bại, reason_code=%s", reason_code)


def _on_disconnect(client, userdata, flags, reason_code, properties=None):
    log.warning("Mất kết nối MQTT Broker (reason_code=%s), đang thử kết nối lại...", reason_code)


def _on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        log.warning("Payload không phải JSON hợp lệ trên topic %s: %r", msg.topic, msg.payload)
        return

    try:
        if msg.topic == settings.topic_sensor:
            _handle_sensor_data(payload)
        elif msg.topic == settings.topic_response:
            _handle_device_response(payload)
    except Exception:
        log.exception("Lỗi khi xử lý message trên topic %s", msg.topic)


# ---------------------------------------------------------------- topic 1
def _handle_sensor_data(payload: dict) -> None:
    """Lưu 3 bản ghi Data_sensor rồi phát sự kiện WebSocket `sensor_data`."""
    global last_sensor_at

    now = datetime.now().replace(microsecond=0)
    values: dict[str, float] = {}

    with SessionLocal() as db:
        for key, meta in SENSOR_MAP.items():
            if key not in payload:
                continue
            value = float(payload[key])
            values[key] = value
            db.add(DataSensor(sensor_id=meta["sensor_id"], value=value, recorded_at=now))
        db.commit()

    if not values:
        log.warning("Payload Data_Sensor không chứa trường nào hợp lệ: %s", payload)
        return

    last_sensor_at = now
    manager.broadcast_threadsafe("sensor_data", {**values, "at": now.isoformat()})
    log.info("Data_Sensor %s", values)


# ---------------------------------------------------------------- topic 3
def _handle_device_response(payload: dict) -> None:
    """Chốt kết quả thực thi: cập nhật Action + Device rồi phát `device_status`."""
    device_id = payload.get("device_id")
    action = str(payload.get("action", "")).lower()
    result = str(payload.get("status", "")).upper()

    if device_id is None or action not in ("on", "off"):
        log.warning("Payload Device_Response thiếu device_id/action: %s", payload)
        return

    now = datetime.now().replace(microsecond=0)
    action_id = None

    with SessionLocal() as db:
        device = db.get(Device, int(device_id))
        if device is None:
            log.warning("Device_Response trỏ tới device_id không tồn tại: %s", device_id)
            return

        # Firmware không gửi kèm action_id nên đối chiếu với lệnh PENDING gần nhất
        # của đúng thiết bị và đúng loại hành động.
        pending = db.scalars(
            select(Action)
            .where(
                Action.device_id == device.device_id,
                Action.status == "PENDING",
                Action.action_type == action.upper(),
            )
            .order_by(Action.created_at.desc(), Action.action_id.desc())
            .limit(1)
        ).first()

        if pending is not None and result == "SUCCESS":
            pending.status = "SUCCESS"
            action_id = pending.action_id

        device.is_active = action == "on"
        device.last_active = now
        db.commit()

    manager.broadcast_threadsafe(
        "device_status",
        {
            "device_id": int(device_id),
            "status": action,
            "action_id": action_id,
            "result": result.lower() or "success",
        },
    )
    log.info("Device_Response device_id=%s action=%s status=%s", device_id, action, result)


# ---------------------------------------------------------------- publish
def publish_control(device_id: int, action: str) -> bool:
    """Gửi lệnh xuống ESP32 qua topic Device_Control. Trả về True nếu đã đẩy được."""
    if not is_connected():
        return False
    payload = json.dumps({"device_id": device_id, "action": action}, ensure_ascii=False)
    info = _client.publish(settings.topic_control, payload, qos=1)
    log.info("Device_Control -> %s", payload)
    return info.rc == mqtt.MQTT_ERR_SUCCESS


# ---------------------------------------------------------------- lifecycle
def start() -> None:
    global _client
    _client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=settings.mqtt_client_id)
    if settings.mqtt_username:
        _client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    _client.on_connect = _on_connect
    _client.on_disconnect = _on_disconnect
    _client.on_message = _on_message
    _client.reconnect_delay_set(min_delay=1, max_delay=30)

    try:
        _client.connect_async(settings.mqtt_host, settings.mqtt_port, keepalive=60)
        _client.loop_start()
    except Exception:
        log.exception("Không khởi động được MQTT client")


def stop() -> None:
    if _client is not None:
        _client.loop_stop()
        _client.disconnect()
