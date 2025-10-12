# Внешние зависимости
from typing import Annotated
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import Field
# Внутренние модули
# from web_app.src.crud import sql_get_all_departament, sql_search_items
from web_app.src.models import TYPE_MAPPING, STATUS_MAPPING


ITEMS = ["Предмет 1", "Предмет 2", "Предмет 3", "Предмет 4", "Предмет 5", "Предмет 6", "Предмет 7", "Предмет 8", "Предмет 9", "Предмет 10", "Предмет 11", "Предмет 12"]

router = APIRouter(
    prefix="/api/v1/request/create",
    tags=["API"],
)

@router.get(
    path="/info",
    response_class=JSONResponse,
    summary="",
)
async def get_info_for_create():
    departament = [{"name": "отделение 1"}, {"name": "отделение 2"}, {"name": "отделение 3"}] # await sql_get_all_departament()

    return {
        "request_type": (r_type.capitalize() for r_type in TYPE_MAPPING.keys()),
        "departament": departament
    }    
    
@router.get(
    path="/item/",
    response_class=JSONResponse,
    summary="",
)
async def search_item(search: str):
    # await sql_search_items(search=search)

    return ITEMS