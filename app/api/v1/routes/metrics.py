from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Query
from datetime import datetime, timezone
from loguru import logger

from app.dependencies import get_db
from app.models import Computer
from app.schemas import AgentMetrics
from app.config import settings

router = APIRouter()

@router.post("/metrics")
def receive_metrics(metrics: AgentMetrics, db: Session = Depends(get_db)):
    """Принимает метрики от агента и обновляет статус в БД."""
    db_computer = db.query(Computer).filter(Computer.hostname == metrics.hostname).first()
    
    # Логика алертов
    if metrics.cpu_percent > settings.CPU_WARN_THRESHOLD:
        logger.warning(f"ALERT [{metrics.hostname}]: Высокая загрузка CPU - {metrics.cpu_percent}%")
    if metrics.disk_percent > settings.DISK_WARN_THRESHOLD:
        logger.warning(f"ALERT [{metrics.hostname}]: Заканчивается место на диске - {metrics.disk_percent}%")
    
    # Общий словарь данных для обновления
    update_data = {
        "ip_address": metrics.ip_address,
        "os_name": metrics.os_name,
        "current_user": metrics.current_user,
        "cpu_percent": metrics.cpu_percent,
        "ram_percent": metrics.ram_percent,
        "ram_total_gb": metrics.ram_total_gb,
        "ram_available_gb": metrics.ram_available_gb,
        "disk_percent": metrics.disk_percent,
        "disk_total_gb": metrics.disk_total_gb,
        "disk_free_gb": metrics.disk_free_gb,
        "uptime_seconds": metrics.uptime_seconds,
        "process_count": metrics.process_count,
        "bytes_sent_mb": metrics.bytes_sent_mb,
        "bytes_recv_mb": metrics.bytes_recv_mb,
        "swap_percent": metrics.swap_percent,
        "status": "ONLINE",
        "last_seen": datetime.now()
    }

    if db_computer:
        # Обновляем существующий ПК
        for key, value in update_data.items():
            setattr(db_computer, key, value)
        logger.info(f"Метрики обновлены: {metrics.hostname} (User: {metrics.current_user})")
    else:
        # Регистрируем новый узел
        db_computer = Computer(hostname=metrics.hostname, **update_data)
        db.add(db_computer)
        logger.success(f"Обнаружен новый узел: {metrics.hostname}")
    
    db.commit()
