# Внешние зависимости
from typing import List, Dict, Any
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import ExecutorOrganization, User
from web_app.src.core import connection


# Вывод организаций-исполнителей
@connection
async def sql_get_executor_organizations(session: AsyncSession) -> List[Dict[str, Any]]:
    try:
        names_result = await session.execute(
            sa.select(ExecutorOrganization.id, ExecutorOrganization.name, User.full_name)
            .join(ExecutorOrganization.user)
        )

        return [
            {"id": i, "name": name, "full_name": full_name}
            for i, name, full_name in names_result.all()
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error get all executor_organizations: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error get all executor_organizations: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")