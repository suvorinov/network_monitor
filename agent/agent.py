import os
import sys
import socket
import platform
import time
import atexit
import signal
import requests
import psutil
import configparser
from loguru import logger
import ctypes
from typing import Optional, Tuple


# === КОНСТАНТЫ ===
AGENT_VERSION = "1.0.0"
DEFAULT_SERVER_URL = "http://192.168.0.9:8900/api/v1/metrics"
DEFAULT_POLL_INTERVAL = 60
MUTEX_NAME = "Global\\CyberMonitorAgentSingleInstance"
IS_WINDOWS = platform.system() == "Windows"
USER_AGENT = f"CyberMonitorAgent/{AGENT_VERSION} ({platform.system()}; {platform.machine()})"


# === РАБОТА С ПУТЯМИ (PyInstaller compatible) ===
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

PID_FILE = os.path.join(APP_DIR, "agent.pid")
LOG_FILE = os.path.join(APP_DIR, "agent.log")
CONFIG_PATH = os.path.join(APP_DIR, "config.ini")


# === ЛОГИРОВАНИЕ ===
logger.remove()
if sys.stderr is not None:
    logger.add(sys.stderr, format="<level>{time:YYYY-MM-DD HH:mm:ss}</level> | <level>{level:<8}</level> | <level>{message}</level>", level="INFO")

logger.add(LOG_FILE, rotation="1 MB", format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}", level="INFO")


# === СЧЁТЧИКИ ===
_cpu_initialized: bool = False


def _init_cpu() -> None:
    global _cpu_initialized
    psutil.cpu_percent()
    _cpu_initialized = True


# === PID-ФАЙЛ (только Linux) ===
def _write_pid() -> None:
    if IS_WINDOWS:
        return
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))


def _remove_pid() -> None:
    if IS_WINDOWS:
        return
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except OSError:
        pass


# === SINGLE INSTANCE ===
def check_single_instance() -> bool:
    """Проверяет, запущена ли уже копия приложения."""
    if IS_WINDOWS:
        try:
            kernel32 = ctypes.windll.kernel32
            mutex = kernel32.CreateMutexW(None, True, MUTEX_NAME)
            last_error = kernel32.GetLastError()
            if last_error == 183:
                logger.warning("Обнаружена уже запущенная копия. Завершение.")
                return False
            return True
        except Exception as e:
            logger.error("Ошибка проверки мьютекса: {}", e)
            return True
    else:
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as f:
                    old_pid = int(f.read().strip())
                if psutil.pid_exists(old_pid):
                    p = psutil.Process(old_pid)
                    if 'agent' in p.name().lower() or 'python' in p.name().lower():
                        logger.warning("Обнаружена уже запущенная копия (PID {}). Завершение.", old_pid)
                        return False
            except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
                _remove_pid()
            except Exception as e:
                logger.error("Ошибка проверки PID-файла: {}", e)
        _write_pid()
        return True


# === GRACEFUL SHUTDOWN ===
def _cleanup(signum=None, frame=None) -> None:
    _remove_pid()
    logger.info("Агент остановлен.")
    sys.exit(0)


signal.signal(signal.SIGTERM, _cleanup)
signal.signal(signal.SIGINT, _cleanup)
atexit.register(_remove_pid)


# === КОНФИГ ===
def load_config() -> Tuple[str, int]:
    """Загружает конфигурацию из config.ini или использует дефолтную."""
    if os.path.exists(CONFIG_PATH):
        try:
            config = configparser.ConfigParser()
            config.read(CONFIG_PATH, encoding='utf-8')
            server_url = config.get('Network', 'server_url', fallback=DEFAULT_SERVER_URL)
            poll_interval = config.getint('Settings', 'poll_interval', fallback=DEFAULT_POLL_INTERVAL)
            logger.info("Конфигурация загружена из {}", CONFIG_PATH)
            return server_url, poll_interval
        except Exception as e:
            logger.error("Ошибка чтения config.ini: {}. Используются умолчания.", e)
    else:
        logger.warning("Файл config.ini не найден. Используются умолчания.")

    return DEFAULT_SERVER_URL, DEFAULT_POLL_INTERVAL


# === МЕТРИКИ ===
def get_system_metrics() -> Optional[dict]:
    """Собирает метрики системы."""
    try:
        hostname = socket.gethostname().split('.')[0].lower()

        ip_address = None
        addrs = psutil.net_if_addrs()
        for _, addr_list in addrs.items():
            for addr in addr_list:
                if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                    ip_address = addr.address
                    break
            if ip_address:
                break

        current_user = "Unknown"
        try:
            users = psutil.users()
            if users:
                current_user = users[0].name
        except Exception:
            current_user = os.environ.get("USER") or os.environ.get("USERNAME") or "Unknown"

        disk_path = 'C:\\' if IS_WINDOWS else '/'
        disk_usage = psutil.disk_usage(disk_path)
        swap = psutil.swap_memory()
        uptime_seconds = int(time.time() - psutil.boot_time())
        net_io = psutil.net_io_counters()
        net_sent_mb = round(net_io.bytes_sent / (1024 ** 2), 2)
        net_recv_mb = round(net_io.bytes_recv / (1024 ** 2), 2)

        return {
            "hostname": hostname,
            "ip_address": ip_address,
            "os_name": platform.system(),
            "current_user": current_user,
            "cpu_percent": psutil.cpu_percent(),
            "ram_percent": psutil.virtual_memory().percent,
            "disk_percent": disk_usage.percent,
            "disk_total_gb": round(disk_usage.total / (1024 ** 3), 2),
            "disk_free_gb": round(disk_usage.free / (1024 ** 3), 2),
            "uptime_seconds": uptime_seconds,
            "process_count": len(list(psutil.process_iter())),
            "bytes_sent_mb": net_sent_mb,
            "bytes_recv_mb": net_recv_mb,
            "swap_percent": swap.percent,
        }
    except Exception as e:
        logger.error("Ошибка при сборе метрик: {}", e)
        return None


# === ОТПРАВКА ===
def send_metrics(metrics: dict, server_url: str) -> None:
    """Отправляет метрики на сервер. До 3 попыток с exponential backoff."""
    headers = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}

    for attempt in range(3):
        try:
            response = requests.post(server_url, json=metrics, timeout=10, headers=headers)
            if response.status_code == 200:
                logger.info("Метрики отправлены: CPU={}% RAM={}%", metrics['cpu_percent'], metrics['ram_percent'])
            else:
                logger.warning("Сервер вернул статус {}. Ответ: {}", response.status_code, response.text[:200])
            return
        except requests.exceptions.ConnectionError:
            logger.warning("Не удалось подключиться к серверу (попытка {}/3)", attempt + 1)
            if attempt < 2:
                time.sleep(2 ** attempt)
        except requests.exceptions.Timeout:
            logger.warning("Таймаут соединения с сервером (попытка {}/3)", attempt + 1)
            if attempt < 2:
                time.sleep(2 ** attempt)
        except requests.exceptions.RequestException as e:
            logger.error("Ошибка HTTP-запроса: {}", e)
            return


# === MAIN ===
def main() -> None:
    if not check_single_instance():
        sys.exit(0)

    _init_cpu()
    server_url, poll_interval = load_config()
    logger.info("CyberMonitor Агент v{} запущен на {}. Сервер: {}", AGENT_VERSION, platform.system(), server_url)

    try:
        while True:
            metrics = get_system_metrics()
            if metrics:
                send_metrics(metrics, server_url)
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        _cleanup()


if __name__ == "__main__":
    main()
