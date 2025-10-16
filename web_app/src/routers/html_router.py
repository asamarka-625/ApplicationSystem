# Внешние зависимости
from fastapi import APIRouter, Request, Depends, HTTPException, status
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
        "role": current_user.role.name,
        "role_value": current_user.role.value.capitalize()
    }
        
    return templates.TemplateResponse('create.html', context=context)


# Страница просмотра списков заявок
@router.get("/requests", response_class=HTMLResponse)
async def requests_page(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    context = {
        "request": request,
        "page": "requests",
        "title": "Заявки",
        "full_name": current_user.full_name,
        "role": current_user.role.name,
        "role_value": current_user.role.value.capitalize()
    }

    return templates.TemplateResponse('requests.html', context=context)


# Страница детального просмотра заявки
@router.get("/request/{registration_number}", response_class=HTMLResponse)
async def detail_page(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    context = {
        "request": request,
        "page": "detail",
        "title": "Просмотр заявки",
        "full_name": current_user.full_name,
        "role": current_user.role.name,
        "role_value": current_user.role.value.capitalize()
    }

    return templates.TemplateResponse('detail.html', context=context)


# Страница редактирования заявки
@router.get("/request/{registration_number}/edit", response_class=HTMLResponse)
async def edit_page(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    if not (current_user.is_secretary or current_user.is_judge):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

    context = {
        "request": request,
        "page": "edit",
        "title": "Редактирование заявки",
        "full_name": current_user.full_name,
        "role": current_user.role.name,
        "role_value": current_user.role.value.capitalize()
    }

    return templates.TemplateResponse('edit.html', context=context)


# Страница назначения исполнителя заявки
@router.get("/request/{registration_number}/redirect", response_class=HTMLResponse)
async def redirect_page(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    if not current_user.is_management:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

    context = {
        "request": request,
        "page": "redirect",
        "title": "Назначение исполнителя",
        "full_name": current_user.full_name,
        "role": current_user.role.name,
        "role_value": current_user.role.value.capitalize()
    }

    return templates.TemplateResponse('redirect.html', context=context)


# Страница аутентификации
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    context = {
        "request": request,
        "page": "login",
        "title": "Аутентификации",
        "full_name": '',
        "role": '',
        "role_value": ''
    }

    return templates.TemplateResponse('login.html', context=context)