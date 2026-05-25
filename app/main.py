import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import engine, Base
from app.dependencies import check_network_pulse
from app.api.v1.routes import dashboard, metrics

# Настройка логирования Loguru (убираем дефолтный хэндлер и добавляем в stderr с нужным форматом)
logger.remove()
logger.add(sys.stderr, format="<level>{time:YYYY-MM-DD HH:mm:ss}</level> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>", level="INFO")

# Инициализируем планировщик
scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения (запуск и выключение)."""
    # === ЗАПУСК ===
    logger.info("Инициализация ядра CyberMonitor...")
    Base.metadata.create_all(bind=engine)
    logger.success("Синхронизация базы данных завершена. Система в сети.")

    # Настраиваем фоновые задачи
    # Запускаем проверку пульса каждые 60 секунд
    scheduler.add_job(check_network_pulse, 'interval', seconds=60, id='pulse_check')
    scheduler.start()
    logger.info("Планировщик задач запущен. Мониторинг пульса активен.")

    yield  # Приложение работает
    
    # === ВЫКЛЮЧЕНИЕ ===
    scheduler.shutdown(wait=False)
    logger.warning("Планировщик остановлен. Завершение работы NetworkMonitor...")

# Инициализация приложения
app = FastAPI(title="CyberMonitor", lifespan=lifespan)

# Подключение маршрутов
app.include_router(dashboard.router, prefix="", tags=["dashboard"])
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])

# Раздаем статические файлы (css, js, fonts)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
