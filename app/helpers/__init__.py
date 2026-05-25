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

def format_traffic(megabytes):
    """Преобразует мегабайты в ГБ или ТБ для читаемости."""
    if not megabytes or megabytes < 0:
        return "0 MB"
    if megabytes >= 1048576: # 1024 * 1024 MB = 1 TB
        return f"{megabytes / 1048576:.2f} TB"
    elif megabytes >= 1024:
        return f"{megabytes / 1024:.2f} GB"
    else:
        return f"{megabytes:.1f} MB"