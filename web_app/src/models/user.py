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
    SECRETARY = "секретарь суда"
    JUDGE = "мировой судья"
    MANAGEMENT = "сотрудник управления"
    EXECUTOR = "исполнитель"


ROLE_MAPPING = {
    "секретарь суда": UserRole.SECRETARY,
    "мировой судья": UserRole.JUDGE,
    "сотрудник управления": UserRole.MANAGEMENT,
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
    judge_profile: so.Mapped[Optional["Judge"]] = so.relationship(
        "Judge",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    secretary_profile: so.Mapped[Optional["Secretary"]] = so.relationship(
        "Secretary",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    management_profile: so.Mapped[Optional["Management"]] = so.relationship(
        "Management",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    executor_profile: so.Mapped[Optional["Executor"]] = so.relationship(
        "Executor",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Связи с заявками
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

    # связи всех ролей с requests. Добавить для каждой модели связь с requests в виде List
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"

    def __str__(self):
        return self.full_name