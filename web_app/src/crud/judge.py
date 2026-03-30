# Внешние зависимости
from typing import List, Tuple
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config, connection
from web_app.src.models import Judge
from web_app.src.schemas import JudgeResponse


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
        config.logger.info(f"Judge not found by ID: {judge_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Judge not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading judge by ID {judge_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading judge by ID {judge_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем всех судей
@connection
async def sql_get_all_judges(
    session: AsyncSession
) -> List[JudgeResponse]:
    try:
        judges_result = await session.execute(
            sa.select(Judge)
            .options(
                so.joinedload(Judge.user),
                so.joinedload(Judge.department)
            )
        )

        return [
            JudgeResponse(
                id=judge.id,
                full_name=judge.user.full_name,
                department=judge.department.name
            )
            for judge in judges_result.scalars()
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error get all judges: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error get all judges: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем email и судебный участок судьи
@connection
async def sql_get_email_department_from_judge_by_id(
    judge_id: int,
    session: AsyncSession
) -> Tuple[str, str, str]:
    try:
        judge_result = await session.execute(
            sa.select(Judge)
            .where(
                Judge.id == judge_id
            )
            .options(
                so.joinedload(Judge.user),
                so.joinedload(Judge.department)
            )
        )
        judge = judge_result.scalar_one()
        return judge.user.email, judge.user.full_name, judge.department.name

    except NoResultFound:
        config.logger.info(f"Judge not found by ID: {judge_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Judge not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error get email and department from judge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error get email and department from judge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")