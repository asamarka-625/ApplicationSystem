# Внешние зависимости
from fastapi import APIRouter, Request
from fastapi.responses import Response, HTMLResponse
from fastapi.templating import Jinja2Templates
# Внутренние модули


router = APIRouter()
templates = Jinja2Templates(directory="web_app/templates")


# Главная страница
@router.get("/create", response_class=HTMLResponse)
async def create_page(request: Request):
    context = {
        'request': request,
    }
        
    return templates.TemplateResponse('create.html', context=context)
    
