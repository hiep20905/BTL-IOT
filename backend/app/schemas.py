"""Kiểu dữ liệu vào/ra của API.

Mọi phản hồi bọc trong đối tượng {success, data, message} theo mục 4.3.1 SRS.
"""

from typing import Any

from pydantic import BaseModel, Field


def envelope(data: Any = None, message: str = "", success: bool = True) -> dict:
    return {"success": success, "data": data, "message": message}


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)


class ActionRequest(BaseModel):
    action: str = Field(pattern="^(on|off|ON|OFF)$", description="on hoặc off")
