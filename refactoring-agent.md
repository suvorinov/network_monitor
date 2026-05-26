# План рефакторинга agent/agent.py

## Статус

`execute_command()` удалена. Остальной код — 188 строк, 4 функции, цикл в `main()`.

---

## Приоритет 1 (High) — Баги и crashes

### 1.1. Retry при недоступности сервера

**Сейчас**: При ошибке сети агент логирует и ждёт следующий цикл (до 60 секунд).

**Надо**: Exponential backoff — 3 попытки с паузой 1, 2, 4 секунды.

```python
def send_metrics(metrics, server_url):
    for attempt in range(3):
        try:
            response = requests.post(server_url, json=metrics, timeout=10)
            if response.status_code == 200:
                logger.info(f"Метрики отправлены: CPU={metrics['cpu_percent']}%")
            return
        except requests.exceptions.RequestException as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"Сервер недоступен после 3 попыток: {e}")
```

### 1.2. Graceful shutdown (PID-файл + сигналы)

**Сейчас**: PID-файл не удаляется при остановке агента. Повторный запуск видит старый PID и может отказаться стартовать.

**Надо**: Обработчики SIGTERM/SIGINT/atexit для очистки.

```python
import atexit
import signal

def cleanup():
    pid_file = os.path.join(APP_DIR, "agent.pid")
    if os.path.exists(pid_file):
        os.remove(pid_file)

signal.signal(signal.SIGTERM, lambda *_: (cleanup(), sys.exit(0)))
signal.signal(signal.SIGINT, lambda *_: (cleanup(), sys.exit(0)))
atexit.register(cleanup)
```

### 1.3. Вынести `execute_command()` − уже сделано

Функция была мёртвым кодом:
- Нигде не вызывалась
- Использовала несуществующую `save_command_result()`
- `subprocess.run(..., shell=True)` — дыра безопасности

---

## Приоритет 2 (Medium) — Производительность

### 2.1. `psutil.cpu_percent(interval=1)` — блокировка на 1 сек

**Сейчас**: Каждый цикл сбора метрик ждёт 1 секунду внутри `get_system_metrics()`.

**Надо**: Вызывать без `interval`, предварительно инициализировав:

```python
# Один раз при запуске
psutil.cpu_percent()  # инициализация (вернёт 0.0)

# В цикле — без блокировки
cpu_percent = psutil.cpu_percent()
```

### 2.2. `platform.system()` вызывается 3 раза

Закешировать в константу модуля:

```python
IS_WINDOWS = platform.system() == 'Windows'
```

### 2.3. `len(psutil.pids())` на системах с 1000+ процессов

Может быть медленным. Альтернативы:
- `len(psutil.process_iter())` — чуть быстрее
- Или удалить процесс-каунт, если не используется в UI

---

## Приоритет 3 (Low) — Качество кода

### 3.1. Traffic counters — разница за период

**Сейчас**: `net_io_counters()` возвращает сумму байт с момента загрузки ОС.

**Надо**: Сохранять предыдущее значение и вычислять разницу:

```python
_net_last_sent = 0
_net_last_recv = 0

def get_net_delta():
    global _net_last_sent, _net_last_recv
    net = psutil.net_io_counters()
    sent = net.bytes_sent - _net_last_sent
    recv = net.bytes_recv - _net_last_recv
    _net_last_sent = net.bytes_sent
    _net_last_recv = net.bytes_recv
    return round(sent / 1024**2, 2), round(recv / 1024**2, 2)
```

### 3.2. Явный User-Agent в HTTP-запросе

```python
headers = {"User-Agent": f"CyberMonitorAgent/1.0 ({platform.system()}; {platform.machine()})"}
response = requests.post(server_url, json=metrics, timeout=10, headers=headers)
```

### 3.3. Типизировать возвращаемые значения

```python
from typing import Optional, Tuple

def load_config() -> Tuple[str, int]: ...
def get_system_metrics() -> Optional[dict]: ...
def send_metrics(metrics: dict, server_url: str) -> None: ...
```

### 3.4. Избавиться от `os.system(sudo reboot)`

Заменить на `subprocess.run()`:

```python
subprocess.run(["shutdown", "/r", "/t", "5"] if IS_WINDOWS else ["systemctl", "reboot"])
```

### 3.5. Логирование — не использовать f-string

Loguru поддерживает lazy formatting:

```python
logger.info("Метрики отправлены: CPU={}%", metrics['cpu_percent'])
# вместо
logger.info(f"Метрики отправлены: CPU={metrics['cpu_percent']}%")
```

---

## Приоритет 4 (Future) — Функциональные улучшения

### 4.1. Мониторинг нескольких дисков

Собирать метрики со всех физических дисков, а не только системного:

```python
disk_paths = ['C:\\', 'D:\\'] if IS_WINDOWS else ['/', '/home', '/var']
for path in disk_paths:
    try:
        usage = psutil.disk_usage(path)
    except PermissionError:
        continue
```

### 4.2. Структурированный конфиг

Заменить `configparser` на Pydantic или dataclass:

```python
from dataclasses import dataclass

@dataclass
class AgentConfig:
    server_url: str = "http://192.168.0.9:8900/api/v1/metrics"
    poll_interval: int = 60
    log_level: str = "INFO"
```

### 4.3. Версионирование

Добавить `__version__ = "1.0.0"`, передавать в метриках и User-Agent.

---

## Резюме изменений

| Файл | Изменение |
|---|---|
| `agent/agent.py` | Удалить `execute_command()` ✓ |
| `agent/agent.py` | Добавить retry + backoff в `send_metrics()` |
| `agent/agent.py` | Graceful shutdown (PID cleanup) |
| `agent/agent.py` | Убрать `interval=1` из `cpu_percent()` |
| `agent/agent.py` | Закешировать `IS_WINDOWS` |
| `agent/agent.py` | Traffic delta вместо абсолютных значений |
| `agent/agent.py` | User-Agent, type hints |
