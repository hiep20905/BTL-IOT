"""Kênh WebSocket /ws/dashboard - mục 4.3.4 SRS.

Sự kiện đẩy về Frontend: sensor_data | device_status | device_offline
Khung bản tin: {"event": "<tên sự kiện>", "data": {...}}
"""

import asyncio
import logging

from fastapi import WebSocket

log = logging.getLogger("ws")


class ConnectionManager:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Ghi nhớ event loop chính để thread của paho-mqtt có thể đẩy sự kiện vào."""
        self._loop = loop

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)
        log.info("WebSocket connected (%d client)", len(self._clients))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(websocket)
        log.info("WebSocket disconnected (%d client)", len(self._clients))

    async def broadcast(self, event: str, data: dict) -> None:
        message = {"event": event, "data": data}
        async with self._lock:
            targets = list(self._clients)

        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._clients.discard(ws)

    def broadcast_threadsafe(self, event: str, data: dict) -> None:
        """Gọi được từ thread khác (callback của paho-mqtt)."""
        if self._loop is None or self._loop.is_closed():
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(event, data), self._loop)


manager = ConnectionManager()
