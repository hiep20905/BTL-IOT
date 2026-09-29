"""Hai tác vụ nền phục vụ các luồng ngoại lệ mô tả trong SRS.

1. action_timeout_watcher - UC "Điều khiển thiết bị", luồng ngoại lệ:
   thiết bị không phản hồi sau khoảng chờ -> Action chuyển TIMEOUT và báo lỗi ra FE.
2. offline_watcher - UC "Xem dữ liệu cảm biến thời gian thực", luồng ngoại lệ:
   không nhận được dữ liệu cảm biến -> phát sự kiện device_offline.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import select

from . import mqtt_client
from .config import settings
from .database import SessionLocal
from .models import Action
from .ws import manager

log = logging.getLogger("watchdog")


async def action_timeout_watcher() -> None:
    while True:
        await asyncio.sleep(2)
        try:
            deadline = datetime.now() - timedelta(seconds=settings.action_timeout_seconds)
            expired = []

            with SessionLocal() as db:
                rows = db.scalars(
                    select(Action).where(Action.status == "PENDING", Action.created_at < deadline)
                ).all()
                for row in rows:
                    row.status = "TIMEOUT"
                    expired.append((row.action_id, row.device_id, row.action_type.lower()))
                if rows:
                    db.commit()

            for action_id, device_id, act in expired:
                log.warning("Action %s (device %s) quá hạn -> TIMEOUT", action_id, device_id)
                await manager.broadcast(
                    "device_status",
                    {
                        "device_id": device_id,
                        "status": act,
                        "action_id": action_id,
                        "result": "timeout",
                    },
                )
        except Exception:
            log.exception("Lỗi trong action_timeout_watcher")


async def offline_watcher() -> None:
    was_offline = False
    while True:
        await asyncio.sleep(5)
        try:
            last = mqtt_client.last_sensor_at
            offline = (
                last is None
                or (datetime.now() - last).total_seconds() > settings.offline_timeout_seconds
            )

            if offline != was_offline:
                was_offline = offline
                await manager.broadcast(
                    "device_offline",
                    {
                        "offline": offline,
                        "last_seen": last.isoformat() if last else None,
                        "message": "Mất kết nối với thiết bị cảm biến" if offline else "Đã kết nối lại",
                    },
                )
        except Exception:
            log.exception("Lỗi trong offline_watcher")
