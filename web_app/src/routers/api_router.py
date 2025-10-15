# Внешние зависимости
from typing import Annotated
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import Field
# Внутренние модули
from web_app.src.crud import sql_get_user_by_id, sql_get_info_user_by_id
from web_app.src.core import config
from web_app.src.schemas import UserResponse


router = APIRouter(
    prefix="/api/v1",
    tags=["API"],
)


@router.get(
    path="/authentication/{user_id}",
    response_class=JSONResponse,
    summary="Авторизация пользователя"
)
async def authentication_user(user_id: Annotated[int, Field(ge=1)]):
    user = await sql_get_user_by_id(user_id=user_id)
    config.test_user_id = user_id

    return {
        "status": "success",
        "user": user
    }


@router.get(
    path="/user/{user_id}",
    response_model=UserResponse,
    summary="Информация о пользователе"
)
async def get_info_user_by_id(user_id: Annotated[int, Field(ge=1)]):
    user = await sql_get_info_user_by_id(user_id=user_id)

    return user