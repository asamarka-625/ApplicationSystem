# Внешние зависимости
from typing import Optional
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import User, UserRole
from web_app.src.crud import sql_get_user_by_id


async def get_current_user() -> User:
    # Ищем пользователя в базе данных
    user_id = config.test_user_id
    user = await sql_get_user_by_id(user_id=user_id)

    return user


def get_current_user_with_role(role: Optional[UserRole] = None):
    async def role_dependency() -> User:
        user_id = config.test_user_id
        user = await sql_get_user_by_id(user_id=user_id, role=role)
        return user

    return role_dependency

