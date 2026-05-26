import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.database import engine, Base
from app.services import check_network_pulse
from app.middleware import CSRFMiddleware
from app.api.v1.routes import dashboard, metrics

logger.remove()
logger.add(sys.stderr, format="<level>{time:YYYY-MM-DD HH:mm:ss}</level> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>", level="INFO")


async def pulse_loop():
    while True:
        check_network_pulse()
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Инициализация ядра CyberMonitor...")
    Base.metadata.create_all(bind=engine)
    logger.success("Синхронизация базы данных завершена. Система в сети.")

    task = asyncio.create_task(pulse_loop())
    logger.info("Мониторинг пульса активен.")

    yield

    task.cancel()
    logger.warning("Завершение работы NetworkMonitor...")


app = FastAPI(title="CyberMonitor", lifespan=lifespan)

app.add_middleware(CSRFMiddleware)

app.include_router(dashboard.router, prefix="", tags=["dashboard"])
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])

app.mount("/static", StaticFiles(directory="app/static"), name="static")
