from fastapi import APIRouter
from sqlalchemy import select

from ..deps import CurrentUser, DbSession
from ..models import Device
from ..schemas import envelope

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("/status", summary="Trạng thái hiện tại của các thiết bị")
def get_status(user: CurrentUser, db: DbSession):
    devices = db.scalars(select(Device).order_by(Device.device_id)).all()
    return envelope(
        [
            {
                "device_id": d.device_id,
                "device_name": d.device_name,
                "status": "on" if d.is_active else "off",
            }
            for d in devices
        ]
    )
