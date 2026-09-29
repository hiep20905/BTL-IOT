"""Sinh dữ liệu mẫu để demo phân trang / lọc / sắp xếp trên hai trang lịch sử.

    backend\\.venv\\Scripts\\python.exe seed.py
"""

import random
import sys
from datetime import datetime, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models import SENSOR_MAP, Action, DataSensor, Device, User

sys.stdout.reconfigure(encoding="utf-8")   # console Windows mặc định cp1252, không in được tiếng Việt

BATCHES = 60        # số lần ESP32 gửi dữ liệu, cách nhau 5 giây
ACTIONS = 38        # số bản ghi lịch sử điều khiển


def main() -> None:
    now = datetime.now().replace(microsecond=0)

    with SessionLocal() as db:
        user = db.scalars(select(User).order_by(User.user_id)).first()
        devices = db.scalars(select(Device).order_by(Device.device_id)).all()
        if user is None or not devices:
            sys.exit("Chưa có dữ liệu khởi tạo. Hãy chạy db/schema.sql trước.")

        for k in range(BATCHES):
            ts = now - timedelta(seconds=5 * k)
            values = {
                "temp": round(random.uniform(24, 33), 1),
                "humid": round(random.uniform(55, 90), 1),
                "light": float(random.randint(500, 3500)),
            }
            for key, value in values.items():
                db.add(DataSensor(sensor_id=SENSOR_MAP[key]["sensor_id"], value=value, recorded_at=ts))

        statuses = ["SUCCESS", "SUCCESS", "SUCCESS", "SUCCESS", "TIMEOUT", "PENDING"]
        for i in range(ACTIONS):
            device = devices[i % len(devices)]
            db.add(
                Action(
                    user_id=user.user_id,
                    device_id=device.device_id,
                    action_type=random.choice(["ON", "OFF"]),
                    status=random.choice(statuses),
                    created_at=now - timedelta(seconds=20 * i),
                )
            )

        db.commit()

    print(f"Đã thêm {BATCHES * 3} bản ghi Data_sensor và {ACTIONS} bản ghi Action.")


if __name__ == "__main__":
    main()
