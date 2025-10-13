# Внутренние модули
from web_app.src.core import config
from web_app.src.models import User
from web_app.src.crud import sql_get_user_by_id


async def get_current_user() -> User:
    # Ищем пользователя в базе данных
    user_id = config.test_user_id
    user = await sql_get_user_by_id(user_id=user_id)

    return user


