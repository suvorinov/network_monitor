from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    DB_PATH: str = "monitor.db"
    SECRET_KEY: str = "your-secret-key-here"
    # Порог времени: если от компьютера нет данных больше 3 минут, он Offline
    OFFLINE_THRESHOLD_MINUTES: int = 3


settings = Settings()
