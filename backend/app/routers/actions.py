from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select, text

from .. import mqtt_client
from ..deps import CurrentUser, DbSession
from ..models import Action, Device
from ..schemas import ActionRequest, envelope

router = APIRouter(prefix="/api/actions", tags=["actions"])


@router.get("", summary="Lịch sử điều khiển (lọc + phân trang)")
def list_actions(
    user: CurrentUser,
    db: DbSession,
    device_id: int | None = Query(None),
    status_: Literal["PENDING", "SUCCESS", "TIMEOUT"] | None = Query(None, alias="status"),
    action: Literal["ON", "OFF"] | None = Query(None),
    q: str | None = Query(None, description="Tìm theo tên thiết bị"),
    time: str | None = Query(None, description="Tìm theo thời gian (yyyy/mm/dd-hh:mm:ss)"),
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None),
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
    if device_id is not None:
        filters.append(Action.device_id == device_id)
    if status_:
        filters.append(Action.status == status_)
    if action:
        filters.append(Action.action_type == action)
    if q:
        filters.append(Device.device_name.like(f"%{q}%"))
    if time:
        filters.append(
            func.date_format(Action.created_at, "%Y/%m/%d-%H:%i:%s").like(f"%{time}%")
        )
    if from_:
        filters.append(Action.created_at >= from_)
    if to:
        filters.append(Action.created_at <= to)

    total = db.scalar(select(func.count(Action.action_id)).join(Device).where(*filters)) or 0

    order = Action.created_at.asc() if sort == "asc" else Action.created_at.desc()
    tiebreak = Action.action_id.asc() if sort == "asc" else Action.action_id.desc()

    rows = db.execute(
        select(Action, Device)
        .join(Device, Device.device_id == Action.device_id)
        .where(*filters)
        .order_by(order, tiebreak)
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    items = [
        {
            "action_id": a.action_id,
            "device_id": a.device_id,
            "device_name": d.device_name,
            "action": a.action_type.lower(),
            "status": a.status,
            "created_at": a.created_at.isoformat(),
        }
        for a, d in rows
    ]

    return envelope({"items": items, "total": total, "page": page, "limit": limit})


@router.post("/{device_id}", status_code=status.HTTP_201_CREATED, summary="Gửi lệnh bật/tắt thiết bị")
def send_action(device_id: int, body: ActionRequest, user: CurrentUser, db: DbSession):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy thiết bị có device_id={device_id}",
        )

    if not mqtt_client.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend đang mất kết nối tới MQTT Broker, chưa gửi được lệnh",
        )

    act = body.action.lower()

    # 1) Ghi log lệnh với trạng thái PENDING
    record = Action(
        user_id=user.user_id,
        device_id=device_id,
        action_type=act.upper(),
        status="PENDING",
        created_at=datetime.now().replace(microsecond=0),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # 2) Publish lệnh xuống ESP32 qua topic Device_Control
    if not mqtt_client.publish_control(device_id, act):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không đẩy được lệnh lên MQTT Broker",
        )

    # 3) Kết quả thực thi sẽ về sau qua WebSocket -> API trả PENDING
    return envelope(
        {
            "action_id": record.action_id,
            "device_id": device_id,
            "action": act,
            "status": "PENDING",
        },
        "Đã gửi lệnh, đang chờ phản hồi từ thiết bị",
    )
