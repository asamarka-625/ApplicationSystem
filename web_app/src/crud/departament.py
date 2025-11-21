# Внешние зависимости
from typing import List, Dict, Any
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import Department, Secretary, Judge, User
from web_app.src.core import connection


# Выводим все отделы
@connection
async def sql_get_all_department(session: AsyncSession) -> List[Dict[str, Any]]:
    try:
        departments_result = await session.execute(
            sa.select(Department)
        )
        departments = departments_result.scalars()

        return [
            {"id": d.id, "name": f"{d.name} ({d.address})"}
            for d in departments
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading all departament: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading all departament: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Создаем новый судебный участок
@connection
async def sql_create_department(
    name: str,
    code: int,
    address: str,
    phone_numbers: list,
    session: AsyncSession
) -> None:
    try:
        new_department = Department(
            name=name,
            code=code,
            address=address,
            phone_numbers=phone_numbers
        )
        session.add(new_department)
        await session.commit()

    except SQLAlchemyError as e:
        config.logger.error(f"Database error create departament: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error create departament: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Удаляем роли пользователей, которые были связаны с участком
@connection
async def sql_delete_role_users_by_department_id(
    department_id: int,
    session: AsyncSession
) -> None:
    try:
        await session.execute(
            sa.update(User)
            .values(role=None)
            .where(
                sa.or_(
                    User.id.in_(
                        sa.select(Secretary.user_id)
                        .where(Secretary.department_id == department_id)
                    ),
                    User.id.in_(
                        sa.select(Judge.user_id)
                        .where(Judge.department_id == department_id)
                    )
                )
            )
        )

        await session.commit()

    except SQLAlchemyError as e:
        config.logger.error(f"Database error delete role users by department_id: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error delete role users by department_id: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")