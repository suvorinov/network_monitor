def format_computer(pc):
    """Преобразует Computer ORM-объект в словарь с отформатированными полями."""
    return {
        "id": pc.id,
        "hostname": pc.hostname,
        "ip_address": pc.ip_address,
        "os_name": pc.os_name,
        "current_user": pc.current_user,
        "status": pc.status,
        "last_seen": pc.last_seen,
        "cpu_percent": pc.cpu_percent,
        "ram_percent": pc.ram_percent,
        "ram_total_gb": pc.ram_total_gb,
        "ram_available_gb": pc.ram_available_gb,
        "disk_percent": pc.disk_percent,
        "disk_total_gb": pc.disk_total_gb,
        "disk_free_gb": pc.disk_free_gb,
        "process_count": pc.process_count,
        "swap_percent": pc.swap_percent,
        "uptime_formatted": format_uptime(pc.uptime_seconds),
        "net_down_formatted": format_traffic(pc.bytes_recv_mb),
        "net_up_formatted": format_traffic(pc.bytes_sent_mb),
    }

def format_uptime(seconds):
    """Преобразует секунды в человекочитаемый формат (дни, часы, минуты)."""
    if not seconds or seconds < 0:
        return "N/A"
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    mins = int((seconds % 3600) // 60)
    
    if days > 0:
        return f"{days}d {hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h {mins}m"
    else:
        return f"{mins}m"

ONE_GB = 1024
ONE_TB = ONE_GB * 1024

def format_traffic(megabytes):
    if not megabytes or megabytes < 0:
        return "0 MB"
    if megabytes >= ONE_TB:
        return f"{megabytes / ONE_TB:.2f} TB"
    elif megabytes >= ONE_GB:
        return f"{megabytes / ONE_GB:.2f} GB"
    else:
        return f"{megabytes:.1f} MB"