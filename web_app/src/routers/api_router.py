# Внешние зависимости
from typing import Annotated
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import Field
# Внутренние модули
from web_app.src.crud import sql_get_user_by_id
from web_app.src.core import config


router = APIRouter(
    prefix="/api/v1",
    tags=["API"],
)


@router.get(
    path="/authentication/{user_id}",
    response_class=JSONResponse,
    summary="Авторизация пользорвателя"
)
async def authentication_user(user_id: Annotated[int, Field(ge=1)]):
    user = await sql_get_user_by_id(user_id=user_id)
    config.test_user_id = user_id

    return {
        "status": "success",
        "user": user
    }