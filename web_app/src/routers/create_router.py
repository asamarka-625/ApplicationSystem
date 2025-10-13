# Внешние зависимости
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import Field
# Внутренние модули
from web_app.src.crud import sql_get_all_departament, sql_search_items, sql_create_request
from web_app.src.models import TYPE_ID_MAPPING, User
from web_app.src.schemas import CreateRequest
from web_app.src.dependencies import get_current_user


router = APIRouter(
    prefix="/api/v1/request/create",
    tags=["API"],
)


@router.get(
    path="/info",
    response_class=JSONResponse,
    summary="Данные для создания заявки"
)
async def get_info_for_create():
    departament = await sql_get_all_departament()

    return {
        "request_type": TYPE_ID_MAPPING,
        "departament": departament
    }    
    
@router.get(
    path="/item/",
    response_class=JSONResponse,
    summary="Поиск предмета"
)
async def search_item(
        search: Annotated[
            str,
            Field(strict=True, max_length=50, strip_whitespace=True)
        ]
):
    items = await sql_search_items(search=search)

    return items


@router.post(
    path="/",
    response_class=JSONResponse,
    summary="Создание новой заявки"
)
async def create_request(
        data: CreateRequest,
        current_user: User = Depends(get_current_user)
):
    request_id = await sql_create_request(data=data, creator_id=current_user.id)

    return {"status": "success", "request_id": request_id}