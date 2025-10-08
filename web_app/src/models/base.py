# Внешние зависимости
from sqlalchemy.ext.asyncio import AsyncAttrs
import sqlalchemy.orm as so


class Base(AsyncAttrs, so.DeclarativeBase):
    def update_from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
