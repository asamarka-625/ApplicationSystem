# Внешние зависимости
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import User, UserRole
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


# Проверяем, существует ли судья с таким user_id
@connection
async def sql_chek_update_role_by_user_id(
        user_id: int,
        role: UserRole,
        session: AsyncSession
) -> bool:
    try:
        user_result = await session.execute(
            sa.select(User)
            .where(User.id == user_id)
        )

        user = user_result.scalar_one()

        if user.role is not None:
            return True

        user.role = role

        await session.commit()

        return False

    except NoResultFound:
        config.logger.info(f"User not user found by ID: {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading user by user_id {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading user by user_id {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем пользователя по id
@connection
async def sql_get_user_by_id(
        user_id: int,
        session: AsyncSession,
        role: Optional[UserRole] = None
) -> User:
    try:
        query = sa.select(User)
        query = query.where(User.id == user_id)

        if role == role.SECRETARY:
            query = query.options(so.joinedload(User.secretary_profile))

        user_result = await session.execute(query)
        user = user_result.scalar_one()

        return user

    except NoResultFound:
        config.logger.info(f"User not user found by ID: {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading user by ID {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading user by ID {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


