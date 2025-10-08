# Внешние зависимости
from typing import Optional
from datetime import datetime
import enum
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import nullsfirst

# Внутренние модули
from web_app.src.models.base import Base


# Enum для ролей пользователей
class UserRole(enum.Enum):
    EMPLOYEE = "employee"  #
    JUDGE = "judge"  # Судья
    ENGINEER = "engineer"  # Инженер
    ADMIN = "admin"  # Администратор


ROLE_LABELS = {
    UserRole.EMPLOYEE: "Сотрудник",
    UserRole.JUDGE: "Судья",
    UserRole.ENGINEER: "Инженер",
    UserRole.ADMIN: "Администратор"
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
        index=True,
        default=UserRole.EMPLOYEE
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

    employee_profile: so.Mapped[Optional["EmployeeProfile"]] = so.relationship(
        "EmployeeProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    judge_profile: so.Mapped[Optional["JudgeProfile"]] = so.relationship(
        "JudgeProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    engineer_profile: so.Mapped[Optional["EngineerProfile"]] = so.relationship(
        "EngineerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    admin_profile: so.Mapped[Optional["AdminProfile"]] = so.relationship(
        "AdminProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"

    def __str__(self):
        return self.full_name

    # Вспомогательные свойства для проверки прав
    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_judge(self) -> bool:
        return self.role == UserRole.JUDGE

    @property
    def is_engineer(self) -> bool:
        return self.role == UserRole.ENGINEER

    @property
    def is_employee(self) -> bool:
        return self.role == UserRole.EMPLOYEE


# Модель Сотрудника
class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True
    )
    department: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    position: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))

    user: so.Mapped["User"] = so.relationship(
        "User",
        back_populates="employee_profile"
    )


# Модель Судьи
class JudgeProfile(Base):
    __tablename__ = "judge_profiles"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True
    )
    court_district: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    judge_id: so.Mapped[Optional[str]] = so.mapped_column(sa.String(50))

    user: so.Mapped["User"] = so.relationship("User", back_populates="judge_profile")


# Модель Инженера
class EngineerProfile(Base):
    __tablename__ = "engineer_profiles"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True
    )
    specialization: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    license_number: so.Mapped[Optional[str]] = so.mapped_column(sa.String(50))

    user: so.Mapped["User"] = so.relationship("User", back_populates="engineer_profile")


# Модель Администратора
class AdminProfile(Base):
    __tablename__ = "admin_profiles"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True
    )

    user: so.Mapped["User"] = so.relationship("User", back_populates="admin_profile")