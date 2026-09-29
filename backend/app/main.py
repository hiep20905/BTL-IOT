import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import mqtt_client
from .routers import actions, auth, devices, sensor_data
from .schemas import envelope
from .security import decode_access_token
from .watchdog import action_timeout_watcher, offline_watcher
from .ws import manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    manager.bind_loop(asyncio.get_running_loop())
    mqtt_client.start()
    tasks = [
        asyncio.create_task(action_timeout_watcher()),
        asyncio.create_task(offline_watcher()),
    ]
    log.info("Backend sẵn sàng - docs tại http://localhost:8000/docs")
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        mqtt_client.stop()


app = FastAPI(
    title="IoT Dashboard API",
    description="RESTful API + WebSocket cho hệ thống ESP32/MQTT (theo SRS chương 4).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Bọc mọi lỗi vào khung {success, data, message} theo mục 4.3.1 SRS ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=envelope(None, str(exc.detail), success=False),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first.get("loc", [])[1:]) or "tham số"
    return JSONResponse(
        status_code=400,
        content=envelope(None, f"Tham số không hợp lệ: {field} - {first.get('msg', '')}", success=False),
    )


app.include_router(auth.router)
app.include_router(sensor_data.router)
app.include_router(devices.router)
app.include_router(actions.router)

from .routers import users  # noqa: E402  (đặt sau để giữ thứ tự hiển thị trong docs)

app.include_router(users.router)


@app.get("/api/health", tags=["system"], summary="Kiểm tra tình trạng backend")
def health():
    return envelope({"mqtt_connected": mqtt_client.is_connected()})


@app.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket, token: str = Query(...)):
    """Kênh realtime, mục 4.3.4 SRS. Sự kiện: sensor_data | device_status | device_offline."""
    if decode_access_token(token) is None:
        await websocket.close(code=1008, reason="Token không hợp lệ hoặc đã hết hạn")
        return

    await manager.connect(websocket)
    try:
        while True:
            # FE không gửi lệnh qua WS; receive giữ kết nối và bắt sự kiện đóng.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)
