# Внешние зависимости
from typing import Annotated, List
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import Field
# Внутренние модули
from web_app.src.crud import sql_get_info_user_by_id, sql_get_all_judges, sql_check_exists_username
from web_app.src.schemas import UserInfoResponse, JudgeResponse, CheckUsernameRequest


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


@router.get(
    path="/judges",
    response_model=List[JudgeResponse],
    summary="Список всех судей"
)
async def get_all_judges():
    judges = await sql_get_all_judges()

    return judges


@router.post(
    path="/check/username",
    response_class=JSONResponse,
    summary="Проверка существования имени пользователя"
)
async def check_exists_username(
    data: CheckUsernameRequest
):
    exists_orm = await sql_check_exists_username(
        username=data.username
    )
    exists_cache = False

    if not exists_orm:
        # проверка из redis
        exists_cache = False

    return {
        "exists": exists_orm or exists_cache
    }