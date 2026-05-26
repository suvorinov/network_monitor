from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    DB_PATH: str = "monitor.db"
    SECRET_KEY: str = "your-secret-key-here"
    OFFLINE_THRESHOLD_MINUTES: int = 3

    CPU_WARN_THRESHOLD: int = 80
    RAM_WARN_THRESHOLD: int = 80
    DISK_WARN_THRESHOLD: int = 90
    SWAP_WARN_THRESHOLD: int = 80


settings = Settings()
