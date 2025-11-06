# Внешние зависимости
from typing import Optional, Tuple, Sequence
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import User, UserRole
from web_app.src.core import connection
from web_app.src.schemas import UserInfoResponse


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


# Проверяем, существует ли пользователь по user_id с ролью, и обновляем роль
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
        config.logger.info(f"User not found by ID: {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading user by user_id {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading user by user_id {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Обновляем роль пользователю
@connection
async def sql_update_role_by_user_id(
        user_id: int,
        role: UserRole,
        session: AsyncSession
) -> None:
    try:
        user_result = await session.execute(
            sa.select(User)
            .where(User.id == user_id)
        )

        user = user_result.scalar_one()
        user.role = role

        await session.commit()

    except NoResultFound:
        config.logger.info(f"User not found by ID: {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error update role by user_id {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error update role by user_id {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем пользователя по id
@connection
async def sql_get_user_by_id(
        user_id: int,
        session: AsyncSession,
        role: Optional[Tuple[UserRole]] = None
) -> User:
    try:
        query = sa.select(User).where(User.id == user_id)

        role_to_relationship = {
            UserRole.SECRETARY: User.secretary_profile,
            UserRole.JUDGE: User.judge_profile,
            UserRole.MANAGEMENT: User.management_profile,
            UserRole.EXECUTOR: User.executor_profile,
            UserRole.EXECUTOR_ORGANIZATION: User.executor_organization_profile,
            UserRole.MANAGEMENT_DEPARTMENT: User.management_department_profile
        }

        if role is not None:
            query = query.options(*(so.joinedload(role_to_relationship[r]) for r in role))

        user_result = await session.execute(query)
        user = user_result.scalar_one()

        return user

    except NoResultFound:
        config.logger.info(f"User not found by ID: {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading user by ID {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading user by ID {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


@connection
async def sql_get_user_by_username(
        username: str,
        session: AsyncSession
) -> User:
    try:
        user_result = await session.execute(sa.select(User).where(User.username == username))
        user = user_result.scalar_one()

        return user

    except NoResultFound:
        config.logger.info(f"User not found by ID: {username}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading user by username {username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading user by username {username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем данные пользователя по id
@connection
async def sql_get_info_user_by_id(
        user_id: int,
        session: AsyncSession
) -> UserInfoResponse:
    try:
        user_data_result = await session.execute(
            sa.select(User.full_name, User.role, User.email, User.phone)
            .where(User.id == user_id)
        )
        user_data = user_data_result.fetchone()

        return UserInfoResponse(
            full_name=user_data[0],
            role=user_data[1].value.capitalize(),
            email=user_data[2],
            phone=user_data[3]
        )

    except NoResultFound:
        config.logger.info(f"User not found by ID: {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading user by ID {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading user by ID {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем всех пользователей без роли
@connection
async def sql_get_users_without_role(
        session: AsyncSession
) -> Sequence[User]:
    try:
        users_result = await session.execute(
            sa.select(User)
            .where(User.role == None)
        )
        users = users_result.scalars().all()

        return users

    except NoResultFound:
        config.logger.info("Users not found by without role")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error found user by without role: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error found user by without role: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")

