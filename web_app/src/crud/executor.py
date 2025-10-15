# Внешние зависимости
from typing import List, Dict, Any
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import Executor, User
from web_app.src.core import connection


# Поиск исполнителей по имени
@connection
async def sql_search_executors(search: str, session: AsyncSession) -> List[Dict[str, Any]]:
    try:
        names_result = await session.execute(
            sa.select(Executor.id, Executor.position, User.full_name)
            .join(Executor.user)
            .where(User.full_name.ilike(f"%{search}%"))
        )

        return [
            {"id": i, "position": position, "full_name": full_name}
            for i, position, full_name in names_result.all()
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error search executors: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error search executors: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")