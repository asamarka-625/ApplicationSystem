# Внешние зависимости
import sqlalchemy as sa
import sqlalchemy.orm as so
# Внутренние модули
from web_app.src.models.base import Base


request_item = sa.Table(
        "request_item",
        Base.metadata,
        sa.Column("request_id", sa.ForeignKey("requests.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("item_id", sa.ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.CheckConstraint("count > 0", name="positive_count")
    )


# Таблица для many-to-many
class RequestItem(Base):
    __table__ = request_item

    request = so.relationship("Request", back_populates="item_associations")
    item = so.relationship("Item", back_populates="request_associations")