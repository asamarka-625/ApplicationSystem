# Внешние зависимости
from typing import Annotated
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import Field
# Внутренние модули


router = APIRouter(
    prefix="/api/v1",
    tags=["API"],
)
"""
@router.get(
    path="/users",
    response_class=JSONResponse,
    summary="Получить всех пользователей",
)
async def get_all_users():
    result = await sql_get_all_users()

    return {
        "count": len(result),
        "users": result
    }


@router.get(
    path="/user/{user_id}",
    response_model=UserResponse,
    summary="Получить пользователя по ID",
)
async def get_user_by_id(user_id: Annotated[int, Field(ge=1)]):
    result = await sql_get_user_by_id(user_id=user_id)

    return result


@router.post(
    path="/user/add/",
    response_model=UserResponse,
    summary="Создать нового пользователя",
)
async def add_user(data: AddUserRequest):
    result = await sql_add_user(**data.model_dump())

    return result


@router.delete(
    path="/user/delete/{user_id}",
    response_class=JSONResponse,
    summary="Удалить пользователя по ID",
)
async def delete_user_by_id(user_id: Annotated[int, Field(ge=1)]):
    await sql_delete_user_by_id(user_id=user_id)

    return {
        "status": "success",
        "ID user delete": user_id
    }

@router.get(
    path="/admins",
    response_class=JSONResponse,
    summary="Получить всех админов",
)
async def get_all_admins():
    result = await sql_get_all_admins()

    return {
        "count": len(result),
        "admins": result
    }


@router.get(
    path="/admin/{id_admin}",
    response_model=AdminResponse,
    summary="Получить админа по ID",
)
async def get_admin_by_id(id_admin: Annotated[int, Field(ge=1)]):
    result = await sql_get_admin_by_id(id_admin=id_admin)

    return result


@router.post(
    path="/admin/add/",
    response_model=AdminResponse,
    summary="Создать нового админа",
)
async def add_admin(data: AddAdminRequest):
    result = await sql_add_admin(user_id=data.user_id)

    return result


@router.delete(
    path="/admin/delete/{admin_id}",
    response_class=JSONResponse,
    summary="Удалить админа по ID",
)
async def delete_admin_by_id(admin_id: Annotated[int, Field(ge=1)]):
    await sql_delete_admin_by_id(admin_id=admin_id)

    return {
        "status": "success",
        "ID user delete": admin_id
    }
"""
