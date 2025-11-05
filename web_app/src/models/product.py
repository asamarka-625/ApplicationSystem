# Внешние зависимости
from typing import Optional, List
from datetime import datetime
import sqlalchemy as sa
import sqlalchemy.orm as so
# Внутренние модули
from web_app.src.models.base import Base


# Модель Категории
class Category(Base):
    __tablename__ = 'categories'

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(
        sa.String(255),
        unique=True,
        index=True,
        nullable=False
    )
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now()
    )
    update_at: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True),
        onupdate=sa.func.now(),
        nullable=True
    )

    items: so.Mapped[List["Item"]] = so.relationship(
        "Item",
        back_populates="category",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

    def __str__(self):
        return self.name


# Модель Товара
class Item(Base):
    __tablename__ = "items"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    serial_number: so.Mapped[str] = so.mapped_column(
        sa.String(100),
        index=True,
        unique=True,
        nullable=False
    )
    name: so.Mapped[str] = so.mapped_column(
        sa.String(255),
        index=True,
        nullable=False
    )
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.Text, nullable=True)
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now()
    )
    update_at: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True),
        onupdate=sa.func.now(),
        nullable=True
    )

    # Внешние ключи
    category_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey('categories.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Связи
    category: so.Mapped["Category"] = so.relationship(
        "Category",
        back_populates="items"
    )
    request_associations: so.Mapped[List["RequestItem"]] = so.relationship(
        "RequestItem",
        back_populates="item",
        viewonly=True
    )

    def __repr__(self):
        return f"<Item(id={self.id}, serial='{self.serial_number}', name='{self.name}')>"

    def __str__(self):
        return self.name