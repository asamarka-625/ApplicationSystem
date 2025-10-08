# Внешние зависимости
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import User
from web_app.src.core import connection


# Проверяем, существует ли пользователь с таким именем
@connection
async def sql_chek_existing_user_by_name(username: str, session: AsyncSession) -> Optional[int]:
    try:
        user_result = await session.execute(
            sa.select(User.id)
            .where(User.username == username)
        )

        return user_result.scalar_one_or_none()

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading user by username {username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading user by username {username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Проверяем, существует ли пользователь с такой почтой
@connection
async def sql_chek_existing_user_by_email(email: str, session: AsyncSession) -> Optional[int]:
    try:
        user_result = await session.execute(
            sa.select(User.id)
            .where(User.email == email)
        )

        return user_result.scalar_one_or_none()

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading user by email {email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading user by email {email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


"""
# Получаем пользователя по ID
@connection
async def sql_get_user_by_id(user_id: int, session: AsyncSession) -> UserResponse:
    try:
        user_result = await session.execute(
            sa.select(User)
            .where(User.id == user_id)
        )
        user = user_result.scalar_one()

        return UserResponse.model_validate(user)

    except NoResultFound:
        config.logger.info(f"User not found by ID: {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading user by ID {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading user by ID {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Создаем нового пользователя
@connection
async def sql_add_user(name: str, balance: int, session: AsyncSession) -> UserResponse:
    try:
        new_user = User(
            name=name,
            balance=balance
        )
        session.add(new_user)

        await session.commit()
        await session.refresh(new_user)

        return UserResponse.model_validate(new_user)

    except SQLAlchemyError as e:
        config.logger.error(f"Database error create user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error create user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Удаляем пользователя по ID
@connection
async def sql_delete_user_by_id(user_id: int, session: AsyncSession) -> None:
    try:
        result = await session.execute(sa.delete(User).where(User.id == user_id))
        await session.commit()

        if result.rowcount == 0:
            config.logger.info(f"User not found by ID: {user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error delete user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error delete user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")

"""