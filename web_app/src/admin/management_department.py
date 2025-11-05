# Внешние зависимости
from typing import Type
from sqladmin import ModelView
from sqladmin.forms import Form
from wtforms import SelectField
from wtforms.validators import ValidationError
# Внутренние модули
from web_app.src.models import ManagementDepartment, UserRole
from web_app.src.crud import (sql_chek_update_role_by_user_id, sql_get_users_without_role,
                              sql_update_role_by_user_id)


class ManagementDepartmentAdmin(ModelView, model=ManagementDepartment):
    column_list = [
        ManagementDepartment.id,
        ManagementDepartment.user,
        ManagementDepartment.management
    ]

    column_labels = {
        ManagementDepartment.id: "Идентификатор",
        ManagementDepartment.user: "Пользователь",
        ManagementDepartment.management: "Сотрудник управления",
        ManagementDepartment.division: "Отдел",
        "executors_count": "Количество исполнителей",
        "requests_count": "Количество заявок"
    }

    column_searchable_list = [ManagementDepartment.id]
    column_sortable_list = [ManagementDepartment.id]
    column_default_sort = [(ManagementDepartment.id, True)]

    column_formatters = {
        ManagementDepartment.user: lambda m, a: m.user.full_name if m.user else "Не назначен",
        ManagementDepartment.management: lambda m, a: m.management.user.full_name if m.management else "Не указано"
    }

    column_formatters_detail = {
        ManagementDepartment.user: lambda m, a: m.user if m.user else "Не назначен",
        ManagementDepartment.management: lambda m, a: m.management if m.management else "Не указано",
        "executors_count": lambda m, a: len(m.executors) if hasattr(m, 'executors')
                                                                and m.executors else 0,
        "requests_count": lambda m, a: len(m.management_department_requests) \
            if hasattr(m, 'management_department_requests') and m.management_department_requests else 0
    }

    form_create_rules = [
        "user",
        "management",
        "division"
    ]

    column_details_list = [
        ManagementDepartment.id,
        ManagementDepartment.user,
        ManagementDepartment.management,
        ManagementDepartment.division,
        "executors_count",
        "requests_count"
    ]

    form_edit_rules = [
        "management",
        "division"
    ]

    form_args = {
        'management': {
            'label': 'Сотрудник управления',
            'description': 'Выберите сотрудника управления'
        },
        'division': {
            'label': 'Отдел',
            'description': 'Напишите отдел'
        }
    }

    can_create = True # право создавать
    can_edit = True # право редактировать
    can_delete = True # право удалять
    can_view_details = True # право смотреть всю информацию
    can_export = True # право экспортировать

    name = "Сотрудник управления отдела" # название
    name_plural = "Сотрудники управления отдела" # множественное название
    icon = "fa-solid fa-user-tie" # иконка
    category = "Пользователи" # категория
    category_icon = "fa-solid fa-list" # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]

    async def on_model_change(self, data, model, is_created, request):
        if is_created and 'user' in data:
            if not isinstance(data['user'], int) and not data['user'].isdigit():
                raise ValidationError(f"Неверно выбран пользователь!")

            existing = await sql_chek_update_role_by_user_id(
                user_id=int(data['user']),
                role=UserRole.MANAGEMENT_DEPARTMENT
            )
            if existing:
                raise ValidationError(f"Пользователь уже имеет роль!")

    async def scaffold_form(self, form_type: str = None) -> Type[Form]:
        form_class = await super().scaffold_form(form_type)
        users = await sql_get_users_without_role()

        if 'user' in form_type:
            form_class.user = SelectField(
                label='Пользователь',
                description='Выберите пользователя',
                choices=[(user.id, str(user)) for user in users],
                coerce=int,
                filters=[],
                default=None,
                render_kw={'class ': 'form-control'}
            )

        return form_class

    async def on_model_delete(self, model, request):
        if model.user:
            await sql_update_role_by_user_id(user_id=model.user.id, role=None)