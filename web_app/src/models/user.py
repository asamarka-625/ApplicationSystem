# Внешние зависимости
from typing import Optional, List
from datetime import datetime
import enum
import sqlalchemy as sa
import sqlalchemy.orm as so
# Внутренние модули
from web_app.src.models.base import Base


# Enum для роли пользователя
class UserRole(enum.Enum):
    COMMITTEE = "сотрудник комитета"
    MANAGEMENT = "сотрудник управления"
    JUDGE = "мировой судья"
    SECRETARY = "секретарь суда"
    FBU = "сотрудник ФБУ"
    EXECUTOR = "исполнитель"


ROLE_MAPPING = {
    "сотрудник комитета": UserRole.COMMITTEE,
    "сотрудник управления": UserRole.MANAGEMENT,
    "мировой судья": UserRole.JUDGE,
    "секретарь суда": UserRole.SECRETARY,
    "сотрудник фбу": UserRole.FBU,
    "исполнитель": UserRole.EXECUTOR
}


# Модель Пользователя
class User(Base):
    __tablename__ = "users"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    username: so.Mapped[str] = so.mapped_column(
        sa.String(50),
        unique=True,
        index=True,
        nullable=False
    )
    email: so.Mapped[str] = so.mapped_column(
        sa.String(255),
        unique=True,
        index=True,
        nullable=False
    )
    password_hash: so.Mapped[str] = so.mapped_column(
        sa.String(255),
        nullable=False
    )
    full_name: so.Mapped[str] = so.mapped_column(
        sa.String(255),
        nullable=False,
        index=True
    )
    role: so.Mapped[UserRole] = so.mapped_column(
        sa.Enum(UserRole),
        nullable=False,
        index=True
    )
    position: so.Mapped[str] = so.mapped_column(
        sa.String(64),
        nullable=False
    )
    phone: so.Mapped[Optional[str]] = so.mapped_column(
        sa.String(11),
        nullable=True
    )
    is_active: so.Mapped[bool] = so.mapped_column(
        sa.Boolean,
        nullable=False,
        index=True,
        default=True
    )
    last_login: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=True
    )
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False
    )
    updated_at: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True),
        onupdate=sa.func.now(),
        nullable=True
    )

    # Связи
    created_requests: so.Mapped[Optional[List["Request"]]] = so.relationship(
        "Request",
        back_populates="creator",
        foreign_keys="Request.creator_id",
    )
    assigned_requests: so.Mapped[Optional[List["Request"]]] = so.relationship(
        "Request",
        back_populates="assignee",
        foreign_keys="Request.assignee_id",
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"

    def __str__(self):
        return self.full_name

    # Вспомогательные свойства для проверки прав
    @property
    def is_committee(self) -> bool:
        return self.role == UserRole.COMMITTEE

    @property
    def is_management(self) -> bool:
        return self.role == UserRole.MANAGEMENT

    @property
    def is_judge(self) -> bool:
        return self.role == UserRole.JUDGE

    @property
    def is_secretary(self) -> bool:
        return self.role == UserRole.SECRETARY

    @property
    def is_fbu(self) -> bool:
        return self.role == UserRole.FBU

    @property
    def is_executor(self) -> bool:
        return self.role == UserRole.EXECUTOR