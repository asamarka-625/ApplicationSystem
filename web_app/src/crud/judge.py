# Внешние зависимости
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import Judge
from web_app.src.core import connection


# Получаем id отдела судьи
@connection
async def sql_get_department_id_by_judge_id(
        judge_id: int,
        session: AsyncSession
) -> int:
    try:
        user_result = await session.execute(
            sa.select(Judge.department_id)
            .where(Judge.id == judge_id)
        )

        department_id = user_result.scalar_one()

        return department_id

    except NoResultFound:
        config.logger.info(f"User not judge found by ID: {judge_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Judge not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading judge by ID {judge_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading judge by ID {judge_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")