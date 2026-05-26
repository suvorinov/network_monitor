from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import Computer
from app.config import settings
from loguru import logger


def check_network_pulse():
    db = SessionLocal()
    try:
        threshold = datetime.now() - timedelta(minutes=settings.OFFLINE_THRESHOLD_MINUTES)
        stale = db.query(Computer).filter(
            Computer.status == "ONLINE",
            Computer.last_seen < threshold
        ).all()
        for pc in stale:
            pc.status = "OFFLINE"
            logger.warning("Узел {} не отвечает. Статус -> OFFLINE", pc.hostname)
        if stale:
            db.commit()
    except Exception as e:
        logger.error("Ошибка при проверке пульса сети: {}", e)
    finally:
        db.close()
