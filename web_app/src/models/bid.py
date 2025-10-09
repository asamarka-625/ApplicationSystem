# Внешние зависимости
from typing import Optional
from datetime import datetime
import enum
import sqlalchemy as sa
import sqlalchemy.orm as so
# Внутренние модули
from web_app.src.models.base import Base


# Enum для срочности заявки
class BidUrgency(enum.Enum):
    COMMON = "common"  # Обычная скорость
    QUICKLY = "quickly"  # Срочная скорость
    

class BidStatus(enum.Enum):
    CREATED = "created" # Создан
    APPROVED = "approved" # Утвержден
    REJECTED = "rejected" # Отклонен
    COMPLETED = "completed" # Выполнен
    
    
# Модель Заявки
class Bid(Base):
    __tablename__ = "bids"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.Text, nullable=True)
    comment: so.Mapped[Optional[str]] = so.mapped_column(sa.Text, nullable=True)
    item_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey('items.id'),
        nullable=False,
        index=True
    )
    user_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    urgency: so.Mapped[BidUrgency] = so.mapped_column(
        sa.Enum(BidUrgency),
        nullable=False,
        index=True,
        default=BidUrgency.COMMON
    )
    status: so.Mapped[BidStatus] = so.mapped_column(
        sa.Enum(BidStatus),
        nullable=False,
        index=True,
        default=BidStatus.CREATED
    )
    emergency: so.Mapped[bool] = so.mapped_column(
        sa.Boolean,
        nullable=False,
        index=True,
        default=False
    )
    lead_time: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True)
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

    item: so.Mapped["Item"] = so.relationship(
        "Item",
        back_populates="bids"
    )
    user: so.Mapped["User"] = so.mapped_column(
        "User",
        back_populates="bids"
    )
    
    def __repr__(self):
        return f"<Bid(id={self.id}, item_id='{self.item_id}', status='{self.status}')>"

    def __str__(self):
        return self.description