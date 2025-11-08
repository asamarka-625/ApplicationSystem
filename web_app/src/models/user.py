# Внешние зависимости
from typing import Optional, List
from datetime import datetime
from enum import Enum
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.hybrid import hybrid_property
# Внутренние модули
from web_app.src.models.base import Base


# Enum для роли пользователя
class UserRole(Enum):
    SECRETARY = "секретарь суда"
    JUDGE = "мировой судья"
    MANAGEMENT = "сотрудник управления"
    MANAGEMENT_DEPARTMENT = "сотрудник управления отдела" # new
    EXECUTOR = "исполнитель"
    EXECUTOR_ORGANIZATION= "организация-исполнитель" # new


ROLE_MAPPING = {
    "секретарь суда": UserRole.SECRETARY,
    "мировой судья": UserRole.JUDGE,
    "сотрудник управления": UserRole.MANAGEMENT,
    "сотрудник управления отдела": UserRole.MANAGEMENT_DEPARTMENT,
    "исполнитель": UserRole.EXECUTOR,
    "организация-исполнитель": UserRole.EXECUTOR_ORGANIZATION
}


# Модель пользователя
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
    role: so.Mapped[Optional[UserRole]] = so.mapped_column(
        sa.Enum(UserRole),
        nullable=True,
        index=True
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

    # Связь
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
    management_department_profile: so.Mapped[Optional["ManagementDepartment"]] = so.relationship(
        "ManagementDepartment",
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
    executor_organization_profile: so.Mapped[Optional["ExecutorOrganization"]] = so.relationship(
        "ExecutorOrganization",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"

    def __str__(self):
        return f"{self.full_name} ({self.profile_str})"

    # Вспомогательные свойства для проверки прав
    @property
    def is_secretary(self) -> bool:
        return self.role == UserRole.SECRETARY

    @property
    def is_judge(self) -> bool:
        return self.role == UserRole.JUDGE


    @property
    def is_management(self) -> bool:
        return self.role == UserRole.MANAGEMENT

    @property
    def is_management_department(self) -> bool:
        return self.role == UserRole.MANAGEMENT_DEPARTMENT

    @property
    def is_executor(self) -> bool:
        return self.role == UserRole.EXECUTOR

    @property
    def is_executor_organization(self) -> bool:
        return self.role == UserRole.EXECUTOR_ORGANIZATION

    @property
    def profile_str(self):
        if self.role:
            return self.role.value
        return "Без роли"


# Модель секретаря
class Secretary(Base):
    __tablename__ = "secretaries"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)

    # Внешние ключи
    user_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True
    )
    judge_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("judges.id"),
        nullable=False,
        index=True
    )
    department_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("departments.id"),
        nullable=True,
        index=True
    )

    # Связи
    user: so.Mapped["User"] = so.relationship(
        "User",
        back_populates="secretary_profile",
        lazy='joined'
    )
    judge: so.Mapped["Judge"] = so.relationship(
        "Judge",
        back_populates="secretaries"
    )
    department: so.Mapped[Optional["Department"]] = so.relationship(
        "Department",
        back_populates="secretaries"
    )
    secretary_requests: so.Mapped[List["Request"]] = so.relationship(
        "Request",
        back_populates="secretary",
        foreign_keys="Request.secretary_id"
    )

    def __repr__(self):
        return f"<Secretary(id={self.id})>"

    def __str__(self):
        return f"{self.user.full_name} (Идентификатор: {self.id})"


# Модель судьи
class Judge(Base):
    __tablename__ = "judges"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)

    # Внешние ключи
    user_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True
    )
    department_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("departments.id"),
        nullable=False,
        index=True
    )

    # Связи
    user: so.Mapped["User"] = so.relationship(
        "User",
        back_populates="judge_profile",
        lazy='joined'
    )
    secretaries: so.Mapped[List["Secretary"]] = so.relationship(
        "Secretary",
        back_populates="judge"
    )
    judge_requests: so.Mapped[List["Request"]] = so.relationship(
        "Request",
        back_populates="judge",
        foreign_keys="Request.judge_id"
    )
    department: so.Mapped["Department"] = so.relationship(
        "Department",
        back_populates="judges",
        lazy='joined'
    )

    def __repr__(self):
        return f"<Judge(id={self.id})>"

    def __str__(self):
        return f"{self.user.full_name} ({self.department.name})"

    @hybrid_property
    def user_full_name(self):
        if self.user:
            return self.user.full_name
        return None

    @user_full_name.expression
    def user_full_name(cls):
        return User.full_name


# Модель сотрудника управления
class Management(Base):
    __tablename__ = "management"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)

    # Внешние ключи
    user_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True
    )

    # Связи
    user: so.Mapped["User"] = so.relationship(
        "User",
        back_populates="management_profile",
        lazy='joined'
    )
    management_departments: so.Mapped[List["ManagementDepartment"]] = so.relationship(
        "ManagementDepartment",
        back_populates="management"
    )
    management_requests: so.Mapped[List["Request"]] = so.relationship(
        "Request",
        back_populates="management",
        foreign_keys="Request.management_id"
    )

    def __repr__(self):
        return f"<Management(id={self.id})>"

    def __str__(self):
        return f"{self.user.full_name} ({self.user.role.value})"


# Модель сотрудника управления отдела
class ManagementDepartment(Base):
    __tablename__ = "management_departments"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    division: so.Mapped[str] = so.mapped_column(
        sa.String(128),
        nullable=False
    )

    # Внешние ключи
    user_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True
    )
    management_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("management.id"),
        nullable=False,
        index=True
    )

    # Связи
    user: so.Mapped["User"] = so.relationship(
        "User",
        back_populates="management_department_profile",
        lazy='joined'
    )
    management: so.Mapped["Management"] = so.relationship(
        "Management",
        back_populates="management_departments"
    )
    executors: so.Mapped[List["Executor"]] = so.relationship(
        "Executor",
        back_populates="management_department"
    )
    management_department_requests: so.Mapped[List["Request"]] = so.relationship(
        "Request",
        back_populates="management_department",
        foreign_keys="Request.management_department_id"
    )

    def __repr__(self):
        return f"<ManagementDepartment(id={self.id})>"

    def __str__(self):
        return f"{self.user.full_name} ({self.division})"


# Модель исполнителя
class Executor(Base):
    __tablename__ = "executors"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    position: so.Mapped[str] = so.mapped_column(
        sa.String(64),
        nullable=False
    )

    # Внешние ключи
    user_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True
    )
    management_department_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("management_departments.id"),
        nullable=False,
        index=True
    )

    # Связи
    user: so.Mapped["User"] = so.relationship(
        "User",
        back_populates="executor_profile",
        lazy='joined'
    )
    management_department: so.Mapped["ManagementDepartment"] = so.relationship(
        "ManagementDepartment",
        back_populates="executors"
    )
    executor_items: so.Mapped[List["RequestItem"]] = so.relationship(
        "RequestItem",
        back_populates="executor"
    )

    def __repr__(self):
        return f"<Executor(id={self.id})>"

    def __str__(self):
        return f"{UserRole.EXECUTOR} ({self.position})"


# Модель организации-исполнителя
class ExecutorOrganization(Base):
    __tablename__ = "executor_organizations"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(
        sa.String(128),
        nullable=False
    )

    # Внешние ключи
    user_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True
    )

    # Связи
    user: so.Mapped["User"] = so.relationship(
        "User",
        back_populates="executor_organization_profile",
        lazy='joined'
    )
    executor_organization_items: so.Mapped[List["RequestItem"]] = so.relationship(
        "RequestItem",
        back_populates="executor_organization"
    )

    def __repr__(self):
        return f"<ExecutorOrganization(id={self.id})>"

    def __str__(self):
        return f"{UserRole.EXECUTOR_ORGANIZATION} ({self.name})"