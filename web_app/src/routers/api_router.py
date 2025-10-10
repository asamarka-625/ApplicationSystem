# Внешние зависимости
from typing import Annotated
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import Field
# Внутренние модули
from web_app.src.crud import sql_get_all_departament, sql_search_items
from web_app.src.models import TYPE_MAPPING


router = APIRouter(
    prefix="/api/v1",
    tags=["API"],
)

@router.get(
    path="/request/info",
    response_class=JSONResponse,
    summary="",
)
async def get_info_for_request():
    departament = await sql_get_all_departament()

    return {
        "request_type": list(TYPE_MAPPING.keys()),
        "departament": departament
    }


@router.get(
    path="/item/",
    response_class=JSONResponse,
    summary="",
)
async def search_item(search: str):
    result = await sql_search_items(search=search)

    return result