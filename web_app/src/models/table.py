# Внешние зависимости
import sqlalchemy as sa
# Внутренние модули
from web_app.src.models.base import Base


# Таблица для many-to-many
request_item = sa.Table(
    "request_item",
    Base.metadata,
    sa.Column("request_id", sa.ForeignKey("requests.id"), primary_key=True),
    sa.Column("item_id", sa.ForeignKey("items.id"), primary_key=True)
)