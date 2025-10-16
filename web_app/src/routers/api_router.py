# Внешние зависимости
from typing import Annotated
from fastapi import APIRouter
from pydantic import Field
# Внутренние модули
from web_app.src.crud import sql_get_info_user_by_id
from web_app.src.schemas import UserInfoResponse


router = APIRouter(
    prefix="/api/v1",
    tags=["API"],
)


@router.get(
    path="/user/{user_id}",
    response_model=UserInfoResponse,
    summary="Информация о пользователе"
)
async def get_info_user_by_id(user_id: Annotated[int, Field(ge=1)]):
    user = await sql_get_info_user_by_id(user_id=user_id)

    return user