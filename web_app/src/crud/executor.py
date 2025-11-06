# Внешние зависимости
from typing import List, Dict, Any, Optional
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import Executor, User, ManagementDepartment
from web_app.src.core import connection


# Вывод исполнителей
@connection
async def sql_get_executors(
        session: AsyncSession,
        management_department_profile: Optional[ManagementDepartment] = None
) -> List[Dict[str, Any]]:
    try:
        query = sa.select(Executor.id, Executor.position, User.full_name).join(Executor.user)

        if management_department_profile is not None:
            query = query.where(Executor.management_department_id == management_department_profile.id)

        names_result = await session.execute(query)

        return [
            {"id": i, "position": position, "full_name": full_name}
            for i, position, full_name in names_result.all()
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error get all executors: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error get all executors: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")