"""Ánh xạ ORM đúng theo CHƯƠNG 3 - Thiết kế cơ sở dữ liệu của SRS."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "User"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100))
    student_id: Mapped[str | None] = mapped_column(String(20))
    class_name: Mapped[str | None] = mapped_column("class", String(50))

    actions: Mapped[list["Action"]] = relationship(back_populates="user")


class Device(Base):
    __tablename__ = "Device"

    device_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_active: Mapped[datetime | None] = mapped_column(DateTime)

    actions: Mapped[list["Action"]] = relationship(back_populates="device")


class Action(Base):
    __tablename__ = "Action"

    action_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("User.user_id"), nullable=False)
    device_id: Mapped[int] = mapped_column(ForeignKey("Device.device_id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="actions")
    device: Mapped["Device"] = relationship(back_populates="actions")


class Sensor(Base):
    __tablename__ = "Sensor"

    sensor_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sensor_type: Mapped[str] = mapped_column(String(50), nullable=False)

    data: Mapped[list["DataSensor"]] = relationship(back_populates="sensor")


class DataSensor(Base):
    __tablename__ = "Data_sensor"

    data_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_id: Mapped[int] = mapped_column(ForeignKey("Sensor.sensor_id"), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    sensor: Mapped["Sensor"] = relationship(back_populates="data")


# Ánh xạ giữa khoá trong payload MQTT / tham số `type` của API và bản ghi Sensor.
# sensor_id được cố định trong db/schema.sql.
SENSOR_MAP: dict[str, dict] = {
    "temp":  {"sensor_id": 1, "sensor_type": "Nhiệt độ", "unit": "°C"},
    "humid": {"sensor_id": 2, "sensor_type": "Độ ẩm",    "unit": "%"},
    "light": {"sensor_id": 3, "sensor_type": "Ánh sáng", "unit": "Lux"},
}

SENSOR_ID_TO_KEY: dict[int, str] = {v["sensor_id"]: k for k, v in SENSOR_MAP.items()}
