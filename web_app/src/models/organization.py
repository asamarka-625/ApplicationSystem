# Внешние зависимости
from typing import List
import sqlalchemy as sa
import sqlalchemy.orm as so
# Внутренние модули
from web_app.src.models.base import Base


class Department(Base):
    __tablename__ = "departments"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(
        sa.String(128),
        nullable=False
    )
    code: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        unique=True,
        nullable=False,
        index=True
    )
    address: so.Mapped[str] = so.mapped_column(
        sa.String,
        nullable=False
    )
    phone_numbers: so.Mapped[list] = so.mapped_column(sa.JSON, nullable=False)  # Список телефонов

    # Связи
    requests: so.Mapped[List["Request"]] = so.relationship(
        "Request",
        back_populates="department",
        cascade="all, delete-orphan"
    )
    # Связи
    judges: so.Mapped[List["Judge"]] = so.relationship(
        "Judge",
        back_populates="department",
        cascade="all, delete-orphan"
    )
    secretaries: so.Mapped[List["Secretary"]] = so.relationship(
        "Secretary",
        back_populates="department",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Department(id={self.id}, code='{self.code}', name='{self.name}')>"

    def __str__(self):
        return f"{self.name} (#{self.code})"