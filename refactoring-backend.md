# Рефакторинг BackEnd по принципу KISS

> Принцип: **K**eep **I**t **S**imple, **S**tupid — каждая сущность должна делать одно дело и делать его просто.

---

## 1. `dependencies.py` — ящик с инструментами (P1 — архитектура)

Файл делает три разных дела:

| Что | Куда должно |
|---|---|
| `get_db()` — dependency для FastAPI | ✅ OK, оставить |
| `check_network_pulse()` — бизнес-логика | → `app/services.py` или `app/pulse.py` |
| `CSRFMiddleware` — middleware | → `app/main.py` (inline) или `app/middleware.py` |

**KISS**: 1 файл = 1 ответственность.

```python
# app/services.py
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
```

---

## 2. `generate_csrf_token()` — мёртвый код (P1 — хлам)

Определена в `dependencies.py:30`, но **нигде не вызывается**.  
`dashboard.py` использует `secrets.token_urlsafe(32)` напрямую.

**KISS**: удалить.

---

## 3. `app/helpers/` — пакет из одного файла (P2 — избыточность)

```python
app/helpers/__init__.py   # 47 строк, весь код здесь
```

Пакет не нужен — достаточно модуля:

```python
app/helpers.py   # переименовать, убрать __init__.py
```

---

## 4. `format_computer()` — ручное копирование полей (P2 — хрупкость)

```python
def format_computer(pc):
    return {
        "id": pc.id,
        "hostname": pc.hostname,
        # ... ещё 14 полей вручную
    }
```

При добавлении поля в `Computer` нужно не забыть обновить:
- Модель
- Схему `AgentMetrics`
- `format_computer()`

**KISS**: можно авто-сериализовать через Pydantic или SQLAlchemy:

```python
# Вариант A: Pydantic модель для ответа
class ComputerOut(BaseModel):
    id: int
    hostname: str
    ip_address: Optional[str]
    # ... все поля
    uptime_formatted: str = ""
    net_down_formatted: str = ""
    net_up_formatted: str = ""

    @classmethod
    def from_orm(cls, pc):
        return cls(
            **{c.name: getattr(pc, c.name) for c in pc.__table__.columns},
            uptime_formatted=format_uptime(pc.uptime_seconds),
            net_down_formatted=format_traffic(pc.bytes_recv_mb),
            net_up_formatted=format_traffic(pc.bytes_sent_mb),
        )
```

**Или проще (KISS)**: не трогать, пока не начнёт раздражать.

---

## 5. `logger.info(hostname)` — отладка в продакшене (P1 — мусор)

`dashboard.py:116` — единственная строка без контекста:

```python
logger.info(hostname)
```

**KISS**: удалить.

---

## 6. APScheduler для одной задачи (P3 — тяжеловесно)

```python
# main.py
scheduler = BackgroundScheduler()
scheduler.add_job(check_network_pulse, 'interval', seconds=60)
scheduler.start()
```

Ради одного `check_network_pulse` раз в минуту тянется целый планировщик.

**KISS замена** — `asyncio.create_task` в `lifespan`:

```python
import asyncio

async def pulse_loop():
    while True:
        check_network_pulse()
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(pulse_loop())
    yield
    task.cancel()
```

Минус: APScheduler в requirements.txt (`apscheduler`), который сейчас не используется больше ни для чего.  
Вариант: убрать APScheduler из зависимостей.

---

## 7. `last_seen` — таймзона (P2 — неконсистентность)

Модель: `DateTime(timezone=True)` + `server_default=func.now()`  
metrics.py: `datetime.now()` — **naive**

SQLite не хранит таймзону, но семантика сломана:

```python
# Сейчас
"last_seen": datetime.now()       # naive

# KISS — просто datetime.utcnow() или убрать timezone=True из модели
"last_seen": datetime.utcnow()    # явно UTC
```

Или проще: убрать `timezone=True` из модели — KISS.

---

## 8. Константы в двух местах (P3 — размазано)

- `app/constants.py`: `CPU_WARN_THRESHOLD`, `RAM_WARN_THRESHOLD`, `DISK_WARN_THRESHOLD`, `SWAP_WARN_THRESHOLD`
- `app/config.py`: `OFFLINE_THRESHOLD_MINUTES`

**KISS**: всё в `app/config.py` под `Settings`, или всё в `app/constants.py` как plain vars.  
Сейчас два места — нужно помнить где что.

```python
# app/config.py — вариант
class Settings(BaseSettings):
    DB_PATH: str = "monitor.db"
    SECRET_KEY: str = "your-secret-key-here"
    OFFLINE_THRESHOLD_MINUTES: int = 3
    CPU_WARN_THRESHOLD: int = 80
    RAM_WARN_THRESHOLD: int = 80
    DISK_WARN_THRESHOLD: int = 90
    SWAP_WARN_THRESHOLD: int = 80
```

---

## 9. `format_traffic` — магическое число (P3 — читаемость)

```python
# Было
if megabytes >= 1048576:

# KISS
ONE_GB = 1024
ONE_TB = ONE_GB * 1024

if megabytes >= ONE_TB:
```

---

## 10. Резюме изменений

| Файл | Что сделать | Приоритет |
|---|---|---|
| `app/dependencies.py` | Удалить `generate_csrf_token()` | P1 |
| `app/dependencies.py` | Вынести `check_network_pulse()` в `app/services.py` | P1 |
| `app/main.py` | Перенести `CSRFMiddleware` inline (убрать импорт из dependencies) | P1 |
| `app/api/v1/routes/dashboard.py` | Удалить `logger.info(hostname)` | P1 |
| `app/main.py` | Заменить APScheduler на `asyncio.create_task` | P2 |
| `app/helpers/__init__.py` → `helpers.py` | Убрать пакет, оставить модуль | P2 |
| `app/models/computer.py` | Убрать `timezone=True` из `last_seen` | P2 |
| `app/api/v1/routes/metrics.py` | `datetime.now()` → `datetime.utcnow()` | P2 |
| `app/constants.py` | Перенести всё в `app/config.py` или наоборот | P3 |
| `app/helpers.py` | `1048576` → явный `ONE_TB` | P3 |

**Главное**: из 10 пунктов только **4 первых** имеют практический смысл — остальные cosmetic.  
Сервис работает, KISS — не трогать то, что не мешает.
