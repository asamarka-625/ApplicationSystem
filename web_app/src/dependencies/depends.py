# Внешние зависимости
from typing import Optional, Tuple
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import User, UserRole
from web_app.src.crud import sql_get_user_by_id


async def get_current_user() -> User:
    # Ищем пользователя в базе данных
    user_id = config.test_user_id
    user = await sql_get_user_by_id(user_id=user_id)

    if user.role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

    return user


def get_current_user_with_role(role: Optional[Tuple[UserRole]] = None):
    if role is None:
        role = tuple(UserRole)

    async def role_dependency() -> User:
        user_id = config.test_user_id
        user = await sql_get_user_by_id(user_id=user_id, role=role)

        if user.role is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

        return user

    return role_dependency

