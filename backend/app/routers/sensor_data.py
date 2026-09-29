from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select, text

from ..deps import CurrentUser, DbSession
from ..models import SENSOR_ID_TO_KEY, SENSOR_MAP, DataSensor, Sensor
from ..schemas import envelope

router = APIRouter(prefix="/api/sensor-data", tags=["sensor-data"])


@router.get("/latest", summary="Giá trị cảm biến mới nhất, dùng khởi tạo Dashboard")
def get_latest(user: CurrentUser, db: DbSession):
    data: dict = {"temp": None, "humid": None, "light": None, "recorded_at": None}
    newest: datetime | None = None

    for key, meta in SENSOR_MAP.items():
        row = db.scalars(
            select(DataSensor)
            .where(DataSensor.sensor_id == meta["sensor_id"])
            .order_by(DataSensor.recorded_at.desc(), DataSensor.data_id.desc())
            .limit(1)
        ).first()
        if row is None:
            continue
        data[key] = row.value
        if newest is None or row.recorded_at > newest:
            newest = row.recorded_at

    data["recorded_at"] = newest.isoformat() if newest else None
    return envelope(data)


@router.get("", summary="Lịch sử dữ liệu cảm biến (lọc + phân trang)")
def list_sensor_data(
    user: CurrentUser,
    db: DbSession,
    type: Literal["temp", "humid", "light"] | None = Query(None, description="Lọc theo loại cảm biến"),
    q: str | None = Query(None, description="Tìm theo tên cảm biến"),
    time: str | None = Query(None, description="Tìm theo thời gian (yyyy/mm/dd-hh:mm:ss)"),
    from_: datetime | None = Query(None, alias="from", description="Thời điểm bắt đầu khoảng lọc"),
    to: datetime | None = Query(None, description="Thời điểm kết thúc khoảng lọc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    sort: Literal["asc", "desc"] = Query("desc"),
):
    if from_ and to and from_ > to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Khoảng thời gian không hợp lệ: 'from' phải trước 'to'",
        )

    filters = []
    if type:
        filters.append(DataSensor.sensor_id == SENSOR_MAP[type]["sensor_id"])
    if q:
        filters.append(Sensor.sensor_name.like(f"%{q}%"))
    if time:
        # Tìm theo chuỗi thời gian dạng yyyy/mm/dd-hh:mm:ss (khớp giao diện mockup)
        filters.append(
            func.date_format(DataSensor.recorded_at, "%Y/%m/%d-%H:%i:%s").like(f"%{time}%")
        )
    if from_:
        filters.append(DataSensor.recorded_at >= from_)
    if to:
        filters.append(DataSensor.recorded_at <= to)

    total = db.scalar(
        select(func.count(DataSensor.data_id)).join(Sensor).where(*filters)
    ) or 0

    order = DataSensor.recorded_at.asc() if sort == "asc" else DataSensor.recorded_at.desc()
    tiebreak = DataSensor.data_id.asc() if sort == "asc" else DataSensor.data_id.desc()

    rows = db.execute(
        select(DataSensor, Sensor)
        .join(Sensor, Sensor.sensor_id == DataSensor.sensor_id)
        .where(*filters)
        .order_by(order, tiebreak)
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    items = []
    for data, sensor in rows:
        key = SENSOR_ID_TO_KEY.get(data.sensor_id, "")
        items.append(
            {
                "id": data.data_id,
                "sensor_name": sensor.sensor_name,
                "type": key,
                "value": data.value,
                "unit": SENSOR_MAP.get(key, {}).get("unit", ""),
                "recorded_at": data.recorded_at.isoformat(),
            }
        )

    return envelope({"items": items, "total": total, "page": page, "limit": limit})
