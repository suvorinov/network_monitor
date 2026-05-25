import os
import sys
import socket
import platform
import time
import requests
import psutil
import configparser
import subprocess
from loguru import logger
import ctypes

# === НАСТРОЙКИ ПО УМОЛЧАНИЮ ===
DEFAULT_SERVER_URL = "http://192.168.0.9:8900/api/v1/metrics"
DEFAULT_POLL_INTERVAL = 60
MUTEX_NAME = "Global\\CyberMonitorAgentSingleInstance"

# === РАБОТА С ПУТЯМИ ===
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

# === ЛОГИРОВАНИЕ ===
logger.remove()
if sys.stderr is not None:
    logger.add(sys.stderr, format="<level>{time:YYYY-MM-DD HH:mm:ss}</level> | <level>{level:<8}</level> | <level>{message}</level>", level="INFO")

log_file = os.path.join(APP_DIR, "agent.log")
logger.add(log_file, rotation="1 MB", format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}", level="INFO")


def load_config():
    """Загружает конфигурацию из config.ini или использует дефолтную."""
    config_path = os.path.join(APP_DIR, "config.ini")
    config = configparser.ConfigParser()
    
    server_url = DEFAULT_SERVER_URL
    poll_interval = DEFAULT_POLL_INTERVAL
    
    if os.path.exists(config_path):
        try:
            config.read(config_path, encoding='utf-8')
            if 'Network' in config and 'server_url' in config['Network']:
                server_url = config['Network']['server_url']
            if 'Settings' in config and 'poll_interval' in config['Settings']:
                poll_interval = config.getint('Settings', 'poll_interval')
            logger.info(f"Конфигурация загружена из {config_path}")
        except Exception as e:
            logger.error(f"Ошибка чтения config.ini: {e}. Используются умолчания.")
    else:
        logger.warning(f"Файл config.ini не найден. Используются умолчания.")
        
    return server_url, poll_interval


def check_single_instance():
    """Проверяет, запущена ли уже копия приложения."""
    if platform.system() == 'Windows':
        try:
            kernel32 = ctypes.windll.kernel32
            mutex = kernel32.CreateMutexW(None, True, MUTEX_NAME)
            last_error = kernel32.GetLastError()
            if last_error == 183:
                logger.warning("Обнаружена уже запущенная копия. Завершение.")
                return False
        except Exception as e:
            logger.error(f"Ошибка проверки мьютекса: {e}")
    else:
        pid_file = os.path.join(APP_DIR, "agent.pid")
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                old_pid = f.read().strip()
            if psutil.pid_exists(int(old_pid)):
                try:
                    p = psutil.Process(int(old_pid))
                    if 'agent' in p.name().lower() or 'python' in p.name().lower():
                        return False
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            os.remove(pid_file)
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
    return True


def get_system_metrics():
    """Собирает расширенные метрики системы."""
    try:
        hostname = socket.gethostname().split('.')[0].lower()        
        ip_address = None
        addrs = psutil.net_if_addrs()
        for interface, addr_list in addrs.items():
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
            current_user = os.getenv("USER") or os.getenv("USERNAME") or "Unknown"

        current_os = platform.system()
        disk_path = 'C:\\' if current_os == 'Windows' else '/'

        disk_usage = psutil.disk_usage(disk_path)
        disk_total_gb = round(disk_usage.total / (1024**3), 2)
        disk_free_gb = round(disk_usage.free / (1024**3), 2)

        uptime_seconds = int(time.time() - psutil.boot_time())

        net_io = psutil.net_io_counters()
        bytes_sent_mb = round(net_io.bytes_sent / (1024**2), 2)
        bytes_recv_mb = round(net_io.bytes_recv / (1024**2), 2)

        swap = psutil.swap_memory()

        metrics = {
            "hostname": hostname,
            "ip_address": ip_address,
            "os_name": current_os,
            "current_user": current_user,
            "cpu_percent": psutil.cpu_percent(interval=1),
            "ram_percent": psutil.virtual_memory().percent,
            "disk_percent": disk_usage.percent,
            "disk_total_gb": disk_total_gb,
            "disk_free_gb": disk_free_gb,
            "uptime_seconds": uptime_seconds,
            "process_count": len(psutil.pids()),
            "bytes_sent_mb": bytes_sent_mb,
            "bytes_recv_mb": bytes_recv_mb,
            "swap_percent": swap.percent,
        }
        return metrics
    except Exception as e:
        logger.error(f"Ошибка при сборе метрик: {e}")
        return None


def execute_command(command_raw):
    """Исполняет команду от сервера. Поддерживает префиксы action: и shell:"""
    logger.warning(f"Получена команда: {command_raw}")
    result_text = ""
    
    try:
        # ПРЕФИКС ACTION: Встроенные безопасные действия
        if command_raw.startswith("action:"):
            action = command_raw.split("action:")[1].strip().lower()
            if action == "reboot":
                logger.info("Выполнение программной перезагрузки...")
                result_text = "Reboot initiated successfully."
                # Сохраняем результат ПЕРЕД перезагрузкой
                save_command_result(result_text)
                # Инициируем перезагрузку
                if platform.system() == 'Windows':
                    os.system("shutdown /r /t 5")
                else:
                    os.system("sudo reboot")
                return # Выходим, так как ПК сейчас перезагрузится
                
        # ПРЕФИКС SHELL: Выполнение произвольной команды ОС
        elif command_raw.startswith("shell:"):
            cmd = command_raw.split("shell:")[1].strip()
            logger.info(f"Выполнение shell-команды: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout.strip() if result.stdout else ""
            error = result.stderr.strip() if result.stderr else ""
            
            if output:
                result_text = output
            if error:
                result_text += f"\n[ERROR]: {error}"
            if not output and not error:
                result_text = f"Command executed. Return code: {result.returncode}"
                
        # ЕСЛИ ПРЕФИКСА НЕТ: Считаем, что это shell-команда (для совместимости)
        else:
            logger.info(f"Выполнение команды без префикса (как shell): {command_raw}")
            result = subprocess.run(command_raw, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout.strip() if result.stdout else ""
            error = result.stderr.strip() if result.stderr else ""
            if output: result_text = output
            if error: result_text += f"\n[ERROR]: {error}"
            if not output and not error: result_text = f"Return code: {result.returncode}"

    except subprocess.TimeoutExpired:
        result_text = "Error: Command execution timed out (30 sec limit)."
    except Exception as e:
        result_text = f"Error executing command: {str(e)}"

    save_command_result(result_text)


def send_metrics(metrics, server_url):
    """Отправляет метрики и проверяет наличие команд от сервера."""
    try:
        response = requests.post(server_url, json=metrics, timeout=10)
        if response.status_code == 200:
            logger.info(f"Метрики отправлены: CPU={metrics['cpu_percent']}%")
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Не удалось подключиться к серверу: {e}")


def main():
    """Главная функция цикла агента."""
    if not check_single_instance():
        sys.exit(0)

    server_url, poll_interval = load_config()
    
    current_os = platform.system()
    logger.info(f"Запуск CyberMonitor Агента на {current_os}. Сервер: {server_url}")
    
    while True:
        metrics = get_system_metrics()
        if metrics:
            send_metrics(metrics, server_url)
        time.sleep(poll_interval)


if __name__ == "__main__":
    main()