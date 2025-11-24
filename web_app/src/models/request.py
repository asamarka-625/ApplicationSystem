# Внешние зависимости
from typing import Optional, List
from datetime import datetime
from enum import Enum
import sqlalchemy as sa
import sqlalchemy.orm as so
# Внутренние модули
from web_app.src.models.base import Base
from web_app.src.models.table import RequestItem


# Enum для статуса заявки
class RequestStatus(Enum):
    REGISTERED = "зарегистрирована"
    CANCELLED = "отменена"
    CONFIRMED = "подтверждена"
    IN_PROGRESS = "в работе"
    PARTIALLY_FULFILLED = "частично выполнена"
    PLANNED = "запланирована"
    COMPLETED = "выполнена"
    ENDING_COMPLETED = "подтверждено выполнение"
    FINISHED = "завершена"

# Enum для типа заявки
class RequestType(Enum):
    MATERIAL = "материалы"
    TECHNICAL = "услуги"

# Enum для действий, которые можно делать с заявкой
class RequestAction(Enum):
    REGISTERED = "зарегистрирована"
    UPDATE = "обновлена"
    CONFIRMED = "подтверждена"
    APPOINTED = "назначена"
    REDIRECT = "перенаправлена"
    DEADLINE = "поставлен срок выполнения"
    IN_PROGRESS = "в работе"
    COMPLETED = "выполнена"
    CANCELLED = "отменена"
    PLANNED = "запланирована"
    ENDING_COMPLETED = "выполнение подтверждено"
    FINISHED = "завершена"

STATUS_MAPPING = {
    "зарегистрирована": RequestStatus.REGISTERED,
    "подтверждена": RequestStatus.CONFIRMED,
    "в работе": RequestStatus.IN_PROGRESS,
    "частично выполнена": RequestStatus.PARTIALLY_FULFILLED,
    "запланирована": RequestStatus.PLANNED,
    "выполнена": RequestStatus.COMPLETED,
    "подтверждено выполнение": RequestStatus.ENDING_COMPLETED,
    "завершена": RequestStatus.FINISHED,
    "отменена": RequestStatus.CANCELLED
}

TYPE_MAPPING = {
    "материалы": RequestType.MATERIAL,
    "услуги": RequestType.TECHNICAL,
}

STATUS_ID_MAPPING = [{"id": i, "name": name.capitalize()} for i, name in enumerate(STATUS_MAPPING.keys())]
TYPE_ID_MAPPING = [{"id": i, "name": name.capitalize()} for i, name in enumerate(TYPE_MAPPING.keys())]


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
    human_registration_number: so.Mapped[str] = so.mapped_column(
        sa.String,
        unique=True,
        nullable=True
    )
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.Text, nullable=True)
    description_management_department: so.Mapped[Optional[str]] = so.mapped_column(sa.Text, nullable=True)
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
    completed_at: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=True
    )

    # Внешние ключи
    secretary_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("secretaries.id"),
        nullable=False,
        index=True
    )
    judge_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("judges.id"),
        nullable=False,
        index=True
    )
    management_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("management.id"),
        nullable=True,
        index=True
    )
    management_department_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("management_departments.id"),
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
    secretary: so.Mapped["Secretary"] = so.relationship(
    "Secretary",
        back_populates="secretary_requests"
    )
    judge: so.Mapped["Judge"] = so.relationship(
        "Judge",
        back_populates="judge_requests"
    )
    management: so.Mapped[Optional["Management"]] = so.relationship(
        "Management",
        back_populates="management_requests"
    )
    management_department: so.Mapped[Optional["ManagementDepartment"]] = so.relationship(
        "ManagementDepartment",
        back_populates="management_department_requests"
    )
    department: so.Mapped["Department"] = so.relationship(
    "Department",
        back_populates="requests"
    )
    related_documents: so.Mapped[List["RequestDocument"]] = so.relationship(
        "RequestDocument",
        back_populates="request",
        cascade="all, delete-orphan"
    )
    history: so.Mapped[List["RequestHistory"]] = so.relationship(
        "RequestHistory",
        back_populates="request",
        cascade="all, delete-orphan"
    )
    item_associations: so.Mapped[List["RequestItem"]] = so.relationship(
        "RequestItem",
        back_populates="request",
        viewonly=True,
        cascade="all, delete-orphan"
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
    size: so.Mapped[int] = so.mapped_column(
        sa.Integer,
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
    action: so.Mapped[RequestAction] = so.mapped_column(
        sa.Enum(RequestAction),
        nullable=False
    )
    description: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text,
        nullable=True
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
        nullable=False,
        index=True
    )

    # Связи
    request: so.Mapped["Request"] = so.relationship(
        "Request",
        back_populates="history"
    )
    user: so.Mapped["User"] = so.relationship("User")

    def __repr__(self):
        return f"<RequestHistory(id={self.id}, action='{self.action}', created_at='{self.created_at}')>"