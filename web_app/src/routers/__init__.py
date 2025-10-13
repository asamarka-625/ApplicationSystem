# Внешние зависимости
from fastapi import APIRouter
# Внутренние модули
from web_app.src.routers.create_router import router as create_router
from web_app.src.routers.view_router import router as view_router
from web_app.src.routers.html_router import router as html_router
from web_app.src.routers.api_router import router as api_router

router = APIRouter()
router.include_router(create_router)
router.include_router(view_router)
router.include_router(html_router)
router.include_router(api_router)