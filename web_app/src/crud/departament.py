# Внешние зависимости
from typing import List, Dict, Any
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import Department
from web_app.src.core import connection


# Выводим все отделы
@connection
async def sql_get_all_departament(session: AsyncSession) -> List[Dict[str, Any]]:
    try:
        departments_result = await session.execute(
            sa.select(Department)
        )
        departments = departments_result.scalars()

        return [
            {"code": d.id, "name": f"[{d.code}] {d.name} ({d.address})"}
            for d in departments
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading all departament: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading all departament: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")