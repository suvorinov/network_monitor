from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Computer
from loguru import logger

from app.config import settings

def get_db():
    """Генератор сессий подключения к базе данных.
    
    Yields:
        Session: Сессия SQLAlchemy.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_network_pulse():
    """Фоновая задача для проверки активности узлов в сети.
    
    Сравнивает время последнего обновления (last_seen) с текущим временем.
    Если разница превышает OFFLINE_THRESHOLD_MINUTES, меняет статус на OFFLINE.
    """
    db: Session = SessionLocal()
    try:
        # Текущее время
        now = datetime.now()
        # Пороговое время
        threshold = now - timedelta(minutes=settings.OFFLINE_THRESHOLD_MINUTES)
        
        # Ищем все компьютеры, которые ONLINE, но не обновлялись дольше порога
        stale_computers = db.query(Computer).filter(
            Computer.status == "ONLINE",
            Computer.last_seen < threshold
        ).all()
        
        for pc in stale_computers:
            pc.status = "OFFLINE"
            logger.warning(f"Узел {pc.hostname} не отвечает. Статус -> OFFLINE")
            
        if stale_computers:
            db.commit()
            
    except Exception as e:
        logger.error(f"Ошибка при проверке пульса сети: {e}")
    finally:
        db.close()