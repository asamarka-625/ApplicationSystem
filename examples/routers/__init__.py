"""""""""""""""""""""""""""Служебные библиотеки"""""""""""""""""""""""""""
from fastapi import APIRouter
"""""""""""""""""""""""""""Внутренние библиотеки"""""""""""""""""""""""""""
from web_app.src.routers.ApiRouter import router as api_router
from web_app.src.routers.HtmlRouter import router as html_router
from web_app.src.routers.DoublerRouter import router as doubler_router
from web_app.src.routers.TapRouter import router as tap_router

main_router = APIRouter()

main_router.include_router(api_router)
main_router.include_router(html_router)
main_router.include_router(doubler_router)
main_router.include_router(tap_router)