import secrets
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Query

from app.models import Computer
from app.dependencies import get_db
from app.middleware import CSRF_COOKIE_NAME
from app.helpers import format_computer
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["CPU_WARN"] = settings.CPU_WARN_THRESHOLD
templates.env.globals["RAM_WARN"] = settings.RAM_WARN_THRESHOLD
templates.env.globals["DISK_WARN"] = settings.DISK_WARN_THRESHOLD
templates.env.globals["SWAP_WARN"] = settings.SWAP_WARN_THRESHOLD

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Рендерит главную страницу дашборда."""
    computers = db.query(Computer).all()
    csrf_token = secrets.token_urlsafe(32)
    resp = templates.TemplateResponse(request, "dashboard.html", {
        "request": request,
        "computers": computers,
        "csrf_token": csrf_token
    })
    resp.set_cookie(key=CSRF_COOKIE_NAME, value=csrf_token, httponly=True, samesite="lax")
    return resp

@router.get("/htmx/terminals", response_class=HTMLResponse)
async def htmx_terminals(
    request: Request, 
    db: Session = Depends(get_db),
    q: str = Query(None),
    status: str = Query("ALL"),
    page: int = Query(1),
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
    formatted_computers = [format_computer(pc) for pc in computers]

    context = {
        "request": request, 
        "computers": formatted_computers, 
        "page": page, 
        "total_pages": (total_computers + limit - 1) // limit,
    }
    
    return templates.TemplateResponse(request, "partials/terminals.html", context)

@router.get("/htmx/host_card/{hostname}", response_class=HTMLResponse)
async def get_host_card(request: Request, hostname: str, db: Session = Depends(get_db)):
    """Возвращает HTML-карточку детальной информации о хосте для модалки."""
    hostname = hostname.lower()
    pc = db.query(Computer).filter(Computer.hostname == hostname).first()

    if not pc:
        return HTMLResponse("<div class='p-4 text-red-500'>Хост не найден</div>")
    
    context = {
        "request": request,
        "pc": format_computer(pc),
    }
    return templates.TemplateResponse(request, "partials/_card.html", context)