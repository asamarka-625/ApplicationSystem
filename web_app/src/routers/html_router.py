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
@router.get("/", response_class=HTMLResponse)
@router.get("/requests", response_class=HTMLResponse)
async def requests_page(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    context = {
        "request": request,
        "full_name": current_user.full_name,
        "role": current_user.role.name,
        "role_value": current_user.role.value.capitalize()
    }

    if current_user.is_executor or current_user.is_executor_organization:
        html_template = "requests_executors.html"
        context.update({
            "page": "requests_executors",
            "title": "Заявки на исполнения"
        })

    else:
        html_template = "requests.html"
        context.update({
            "page": "requests",
            "title": "Заявки"
        })

    return templates.TemplateResponse(html_template, context=context)


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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    context = {
        "request": request,
        "page": "edit",
        "title": "Редактирование заявки",
        "full_name": current_user.full_name,
        "role": current_user.role.name,
        "role_value": current_user.role.value.capitalize()
    }

    return templates.TemplateResponse('edit.html', context=context)


# Страница назначение сотрудника управления отдела для заявки
@router.get("/request/{registration_number}/redirect/management", response_class=HTMLResponse)
async def redirect_management_page(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    if not current_user.is_management:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    context = {
        "request": request,
        "page": "redirect_management",
        "title": "Назначение сотрудника управления отдела",
        "full_name": current_user.full_name,
        "role": current_user.role.name,
        "role_value": current_user.role.value.capitalize()
    }

    return templates.TemplateResponse('redirect_management.html', context=context)


# Страница просмотра планирования
@router.get("/planning", response_class=HTMLResponse)
async def planning_page(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    if not (current_user.is_management or current_user.is_management_department or
            current_user.is_executor or current_user.is_executor_organization):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    context = {
        "request": request,
        "page": "planning",
        "title": "Планирование",
        "full_name": current_user.full_name,
        "role": current_user.role.name,
        "role_value": current_user.role.value.capitalize()
    }

    return templates.TemplateResponse('planning.html', context=context)


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