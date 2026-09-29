from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- MySQL ---
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "iot_db"

    # --- MQTT Broker (Mosquitto) ---
    mqtt_host: str = "192.168.137.1"
    mqtt_port: int = 1884
    mqtt_username: str = "hiep"
    mqtt_password: str = "123"
    mqtt_client_id: str = "iot_backend"
    topic_sensor: str = "Data_Sensor"
    topic_control: str = "Device_Control"
    topic_response: str = "Device_Response"

    # --- JWT ---
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720

    # --- Nghiệp vụ ---
    action_timeout_seconds: int = 10   # quá hạn -> Action chuyển TIMEOUT
    offline_timeout_seconds: int = 20  # không có dữ liệu cảm biến -> phát device_offline

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{quote_plus(self.db_password)}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


settings = Settings()
