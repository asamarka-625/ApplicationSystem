# Внешние зависимости
from typing import Optional
import enum
import sqlalchemy as sa
import sqlalchemy.orm as so
# Внутренние модули
from web_app.src.models.base import Base


# Enum для статуса заявки
class RequestItemStatus(enum.Enum):
    REGISTERED = "зарегистрирована"
    IN_PROGRESS = "в работе"
    COMPLETED = "выполнена"
    CANCELLED = "отменена"
    PLANNED = "запланирована"


request_item = sa.Table(
    "request_item",
    Base.metadata,
    sa.Column("request_id", sa.ForeignKey("requests.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("item_id", sa.ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("count", sa.Integer(), nullable=False),
    sa.CheckConstraint("count > 0", name="positive_count"),
    sa.Column("executor_id", sa.ForeignKey("executors.id"), nullable=True, index=True),
    sa.Column(
        "executor_organization_id",
        sa.ForeignKey("executor_organizations.id"),
        nullable=True,
        index=True
    ),
    sa.Column(
        "status",
        sa.Enum(RequestItemStatus),
        default=RequestItemStatus.REGISTERED,
        nullable=False,
        index=True
    ),
    sa.Column("deadline_executor", sa.DateTime(timezone=True), nullable=True),
    sa.Column("deadline_organization", sa.DateTime(timezone=True), nullable=True),
    sa.Column("description_executor", sa.Text, nullable=True),
    sa.Column("description_organization", sa.Text, nullable=True)
)


# Таблица для many-to-many
class RequestItem(Base):
    __table__ = request_item

    request: so.Mapped["Request"] = so.relationship("Request", back_populates="item_associations")
    item: so.Mapped["Item"] = so.relationship("Item", back_populates="request_associations")
    executor: so.Mapped[Optional["Executor"]] = so.relationship("Executor", back_populates="executor_items")
    executor_organization: so.Mapped[Optional["ExecutorOrganization"]] = so.relationship(
        "ExecutorOrganization",
        back_populates="executor_organization_items"
    )