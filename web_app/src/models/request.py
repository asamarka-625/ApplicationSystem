# Внешние зависимости
from typing import Optional, List
from datetime import datetime
import enum
import sqlalchemy as sa
import sqlalchemy.orm as so
# Внутренние модули
from web_app.src.models.base import Base
from web_app.src.models.table import request_item


# Enum для статуса заявки
class RequestStatus(enum.Enum):
    REGISTERED = "зарегистрирована"
    IN_PROGRESS = "в работе"
    COMPLETED = "выполнена"
    CANCELLED = "отменена"

# Enum для типа заявки
class RequestType(enum.Enum):
    MATERIAL = "материально-техническое обеспечение"
    TECHNICAL = "техническое обслуживание"
    OPERATIONAL = "эксплуатационное обслуживание"
    EMERGENCY = "аварийная"

STATUS_MAPPING = {
    "зарегистрирована": RequestStatus.REGISTERED,
    "в работе": RequestStatus.IN_PROGRESS,
    "выполнена": RequestStatus.COMPLETED,
    "отменена": RequestStatus.CANCELLED
}

TYPE_MAPPING = {
    "материально-техническое обеспечение": RequestType.MATERIAL,
    "техническое обслуживание": RequestType.TECHNICAL,
    "эксплуатационное обслуживание": RequestType.OPERATIONAL,
    "аварийная": RequestType.EMERGENCY
}


# Модель Заявки
class Request(Base):
    __tablename__ = "requests"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    registration_number: so.Mapped[str] = so.mapped_column(
        sa.String,
        unique=True,
        index=True,
        nullable=False
    )
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.Text, nullable=True)
    request_type: so.Mapped[RequestType] = so.mapped_column(
        sa.Enum(RequestType),
        nullable=False,
        index=True
    )
    status: so.Mapped[RequestStatus] = so.mapped_column(
        sa.Enum(RequestStatus),
        default=RequestStatus.REGISTERED,
        index=True,
        nullable=False
    )
    is_emergency: so.Mapped[bool] = so.mapped_column(
        sa.Boolean,
        default=False,
        nullable=False
    )

    # Сроки
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now()
    )
    update_at: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True),
        onupdate=sa.func.now(),
        nullable=True
    )
    deadline: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=True
    )
    completed_at: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=True
    )

    # Внешние ключи
    creator_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    assignee_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    department_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("departments.id"),
        nullable=False,
        index=True
    )

    # Связи
    creator: so.Mapped["User"] = so.relationship(
        "User",
        back_populates="created_requests",
        foreign_keys=[creator_id]
    )
    assignee: so.Mapped[Optional["User"]] = so.relationship(
        "User",
        back_populates="assigned_requests",
        foreign_keys=[assignee_id],
    )
    department: so.Mapped[List["Department"]] = so.relationship(
    "Department",
        back_populates="requests"
    )
    related_documents: so.Mapped[Optional["RequestDocument"]] = so.relationship(
        "RequestDocument",
        back_populates="request",
    )
    history: so.Mapped[Optional["RequestHistory"]] = so.relationship(
        "RequestHistory",
        back_populates="request",
    )
    items: so.Mapped[List["Item"]] = so.relationship(
        "Item",
        secondary=request_item,
        back_populates="requests"
    )

    def __repr__(self):
        return f"<Request(id={self.id}, registration_number='{self.registration_number}', status='{self.status}')>"

    def __str__(self):
        return f"#{self.registration_number}"


# Модель документа
class RequestDocument(Base):
    __tablename__ = "request_documents"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    document_type: so.Mapped[str] = so.mapped_column(
        sa.String,
        nullable=False
    )
    file_path: so.Mapped[str] = so.mapped_column(
        sa.String,
        nullable=False
    )
    file_name: so.Mapped[str] = so.mapped_column(
        sa.String,
        nullable=False
    )
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now()
    )

    # Внешние ключи
    request_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("requests.id"),
        nullable=False,
        index=True
    )

    # Связи
    request: so.Mapped["Request"] = so.relationship(
        "Request",
        back_populates="related_documents"
    )

    def __repr__(self):
        return f"<RequestDocument(id={self.id}, document_type='{self.document_type}', file_name='{self.file_name}')>"

    def __str__(self):
        return f"{self.file_path}/{self.file_name}"


# Модель истории заявок
class RequestHistory(Base):
    __tablename__ = "request_history"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    action: so.Mapped[str] = so.mapped_column(
        sa.String(32),
        nullable=False
    )
    description: so.Mapped[str] = so.mapped_column(
        sa.Text,
        nullable=False
    )
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now()
    )

    # Внешние ключи
    request_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("requests.id"),
        nullable=False,
        index=True
    )
    user_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("users.id"),
        nullable=False
    )

    # Связи
    request: so.Mapped["Request"] = so.relationship(
        "Request",
        back_populates="history"
    )
    user: so.Mapped["User"] = so.relationship("User")

    def __repr__(self):
        return f"<RequestHistory(id={self.id}, action='{self.action}', created_at='{self.created_at}')>"