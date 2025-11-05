# Внешние зависимости
from typing import List, Dict, Any
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import ManagementDepartment, User
from web_app.src.core import connection


# Вывод сотрудников управления отдела
@connection
async def sql_get_management_departments(session: AsyncSession) -> List[Dict[str, Any]]:
    try:
        names_result = await session.execute(
            sa.select(ManagementDepartment.id, ManagementDepartment.division, User.full_name)
            .join(ManagementDepartment.user)
        )

        return [
            {"id": i, "division": division, "full_name": full_name}
            for i, division, full_name in names_result.all()
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error get all management_departments: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error get all management_departments: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")