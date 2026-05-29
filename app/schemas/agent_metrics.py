from pydantic import BaseModel
from typing import Optional

class AgentMetrics(BaseModel):
    """Схема валидации входящих метрик от агента."""
    hostname: str
    ip_address: Optional[str] = None
    os_name: Optional[str] = "Unknown"
    current_user: Optional[str] = "Unknown" # <--- НОВОЕ ПОЛЕ
    cpu_percent: float = 0
    ram_percent: float = 0
    ram_total_gb: Optional[float] = 0
    ram_available_gb: Optional[float] = 0
    disk_percent: float = 0
    disk_total_gb: Optional[float] = 0
    disk_free_gb: Optional[float] = 0
    uptime_seconds: Optional[int] = 0
    process_count: Optional[int] = 0
    bytes_sent_mb: Optional[float] = 0
    bytes_recv_mb: Optional[float] = 0
    swap_percent: Optional[float] = 0