# Внешние зависимости
from typing import Type
from sqladmin import ModelView
from sqladmin.forms import Form
from wtforms import SelectField
from wtforms.validators import ValidationError
# Внутренние модули
from web_app.src.models import Management, UserRole
from web_app.src.crud import (sql_chek_update_role_by_user_id, sql_get_users_without_role,
                              sql_update_role_by_user_id)


class ManagementAdmin(ModelView, model=Management):
    column_list = [
        Management.id,
        Management.user,
    ]

    column_labels = {
        Management.id: "Идентификатор",
        Management.user: "Пользователь",
        "management_departments_count": "Количество сотрудников управления отдела",
        "requests_count": "Количество заявок"
    }

    column_searchable_list = [Management.id]
    column_sortable_list = [Management.id]
    column_default_sort = [(Management.id, True)]

    column_formatters = {
        Management.user: lambda m, a: m.user.full_name if m.user else "Не назначен"
    }

    column_formatters_detail = {
        Management.user: lambda m, a: m.user.full_name if m.user else "Не назначен",
        "management_departments_count": lambda m, a: len(m.management_departments) \
            if hasattr(m, 'management_departments') and m.management_departments else 0,
        "requests_count": lambda m, a: len(m.management_requests) if hasattr(m, 'management_requests')
                                                                and m.management_requests else 0
    }

    form_create_rules = [
        "user"
    ]

    column_details_list = [
        Management.id,
        Management.user,
        "management_departments_count",
        "requests_count"
    ]

    can_create = True # право создавать
    can_edit = False # право редактировать
    can_delete = True # право удалять
    can_view_details = True # право смотреть всю информацию
    can_export = True # право экспортировать

    name = "Сотрудник управления" # название
    name_plural = "Сотрудники управления" # множественное название
    icon = "fa-solid fa-people-roof" # иконка
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
                role=UserRole.MANAGEMENT
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
