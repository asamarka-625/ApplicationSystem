# Внешние зависимости
from typing import List, Tuple, Dict
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import Item, Category
from web_app.src.core import connection


# Проверяем, существует ли товар с таким номером
@connection
async def sql_chek_existing_item_by_serial(serial_number: str, session: AsyncSession) -> bool:
    try:
        item_result = await session.execute(
            sa.select(Item.id)
            .where(Item.serial_number == serial_number)
        )

        return bool(item_result.scalar_one_or_none())

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading item by serial_number {serial_number}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading item by serial_number {serial_number}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Проверяем, существует ли категория с таким названием
@connection
async def sql_chek_existing_category_by_name(name: str, session: AsyncSession) -> bool:
    try:
        category_result = await session.execute(
            sa.select(Category.id)
            .where(Category.name == name)
        )

        return bool(category_result.scalar_one_or_none())

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading category by name {name}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading category by name {name}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем список категорий
@connection
async def sql_get_categories_choices(session: AsyncSession) -> List[Tuple[str, str]]:
    try:
        categories_result = await session.execute(
            sa.select(Category.id, Category.name)
        )

        return [(str(cat.id), cat.name) for cat in categories_result.all()]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading all categories: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading all categories: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем список категорий
@connection
async def sql_search_items(search: str, session: AsyncSession) -> List[Dict[str, str]]:
    try:
        names_result = await session.execute(
            sa.select(Item.name)
            .where(Item.name.ilike(f"%{search}%"))
        )

        return [{"name": name, "title": name} for name in names_result.scalars()]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading all categories: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reading all categories: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")