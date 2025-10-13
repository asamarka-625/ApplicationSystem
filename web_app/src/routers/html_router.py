# Внешние зависимости
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
# Внутренние модули
from web_app.src.dependencies import get_current_user
from web_app.src.models import User


router = APIRouter()
templates = Jinja2Templates(directory="web_app/templates")


# Страница создания заявки
@router.get("/create", response_class=HTMLResponse)
async def create_page(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    context = {
        "request": request,
        "page": "create",
        "title": "Создание заявки",
        "full_name": current_user.full_name,
        "role": current_user.role.value.capitalize()
    }
        
    return templates.TemplateResponse('create.html', context=context)


# Страница просмотра списков заявок пользователя
@router.get("/requests", response_class=HTMLResponse)
async def requests_page(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    context = {
        "request": request,
        "page": "requests",
        "title": "Мои заявки",
        "full_name": current_user.full_name,
        "role": current_user.role.value.capitalize()
    }

    return templates.TemplateResponse('requests.html', context=context)


# Страница просмотра списков заявок пользователя
@router.get("/requests/all", response_class=HTMLResponse)
async def requests_page(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    context = {
        "request": request,
        "page": "requests_all",
        "title": "Все заявки",
        "full_name": current_user.full_name,
        "role": current_user.role.value.capitalize()
    }

    return templates.TemplateResponse('requests_all.html', context=context)


# Страница детального просмотра заявки
@router.get("/request/{registration_number}", response_class=HTMLResponse)
async def requests_page(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    context = {
        "request": request,
        "page": "request_detail",
        "title": "Просмотр заявки",
        "full_name": current_user.full_name,
        "role": current_user.role.value.capitalize()
    }

    return templates.TemplateResponse('request_detail.html', context=context)