from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Query
from datetime import datetime
from loguru import logger

from app.models import Computer
from app.dependencies import get_db
from app.helpers import format_traffic, format_uptime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Рендерит главную страницу дашборда.
    
    Args:
        request (Request): Объект запроса FastAPI.
        db (Session): Сессия базы данных.
        
    Returns:
        TemplateResponse: HTML-страница дашборда.
    """
    computers = db.query(Computer).all()
    return templates.TemplateResponse(request, "dashboard.html", {"request": request, "computers": computers})

@router.get("/htmx/terminals", response_class=HTMLResponse)
async def htmx_terminals(
    request: Request, 
    db: Session = Depends(get_db),
    q: str = Query(None),
    status: str = Query("ALL"),
    page: int = Query(1),
    view: str = Query("cli") # <--- Добавляем параметр вида
):
    limit = 18
    offset = (page - 1) * limit
    
    query = db.query(Computer)
    if q:
        query = query.filter(Computer.hostname.contains(q))
    if status and status != "ALL":
        query = query.filter(Computer.status == status)
        
    total_computers = query.count()
    computers = query.offset(offset).limit(limit).all()
    # --- ДОБАВЛЕННАЯ ОБРАБОТКА ---
    # Создаем список словарей с отформатированными данными
    formatted_computers = []
    for pc in computers:
        pc_dict = {
            "id": pc.id,
            "hostname": pc.hostname,
            "ip_address": pc.ip_address,
            "os_name": pc.os_name,
            "current_user": pc.current_user,
            "status": pc.status,
            "last_seen": pc.last_seen,
            "cpu_percent": pc.cpu_percent,
            "ram_percent": pc.ram_percent,
            "disk_percent": pc.disk_percent,
            "disk_total_gb": pc.disk_total_gb,
            "disk_free_gb": pc.disk_free_gb,
            "process_count": pc.process_count,
            "swap_percent": pc.swap_percent,
            # Форматируем сырые данные!
            "uptime_formatted": format_uptime(pc.uptime_seconds),
            "net_down_formatted": format_traffic(pc.bytes_recv_mb),
            "net_up_formatted": format_traffic(pc.bytes_sent_mb),
        }
        formatted_computers.append(pc_dict)

    context = {
        "request": request, 
        "computers": formatted_computers, 
        "page": page, 
        "total_pages": (total_computers + limit - 1) // limit,
        "view_type": view # <--- Передаем в шаблон
    }
    
    return templates.TemplateResponse(request, "partials/terminals.html", context)

@router.get("/htmx/host_card/{hostname}", response_class=HTMLResponse)
async def get_host_card(request: Request, hostname: str, db: Session = Depends(get_db)):
    """Возвращает HTML-карточку детальной информации о хосте для модалки."""
    pc = db.query(Computer).filter(Computer.hostname == hostname).first()
    if not pc:
        return HTMLResponse("<div class='p-4 text-red-500'>Хост не найден</div>")
    
    # Форматируем данные (используем те же хелперы)
    context = {
        "request": request,
        "pc": {
            "hostname": pc.hostname,
            "ip_address": pc.ip_address,
            "os_name": pc.os_name,
            "current_user": pc.current_user,
            "status": pc.status,
            "last_seen": pc.last_seen,
            "cpu_percent": pc.cpu_percent,
            "ram_percent": pc.ram_percent,
            "disk_percent": pc.disk_percent,
            "disk_total_gb": pc.disk_total_gb,
            "disk_free_gb": pc.disk_free_gb,
            "process_count": pc.process_count,
            "swap_percent": pc.swap_percent,
            "uptime_formatted": format_uptime(pc.uptime_seconds),
            "net_down_formatted": format_traffic(pc.bytes_recv_mb),
            "net_up_formatted": format_traffic(pc.bytes_sent_mb),
        }
    }
    logger.info(hostname)
    return templates.TemplateResponse(request, "partials/host_card.html", context)