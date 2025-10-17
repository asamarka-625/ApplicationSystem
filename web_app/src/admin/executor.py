# Внешние зависимости
from typing import Type
from sqladmin import ModelView
from sqladmin.forms import Form
from wtforms import SelectField
from wtforms.validators import ValidationError
# Внутренние модули
from web_app.src.models import Executor, UserRole
from web_app.src.crud import sql_chek_update_role_by_user_id, sql_get_users_without_role


class ExecutorAdmin(ModelView, model=Executor):
    column_list = [
        Executor.id,
        Executor.user,
        Executor.position
    ]

    column_labels = {
        Executor.id: "Идентификатор",
        Executor.user: "Пользователь",
        Executor.position: "Должность",
        "requests_count": "Количество заявок"
    }

    column_searchable_list = [Executor.id]
    column_sortable_list = [Executor.id]
    column_default_sort = [(Executor.id, True)]

    column_formatters = {
        Executor.user: lambda m, a: m.user.full_name if m.user else "Не назначен"
    }

    column_formatters_detail = {
        Executor.user: lambda m, a: m.user.full_name if m.user else "Не назначен",
        "requests_count": lambda m, a: len(m.executor_requests) if hasattr(m, 'executor_requests')
                                                                and m.executor_requests else 0
    }

    form_create_rules = [
        "user",
        "position"
    ]

    form_edit_rules = [
        "position"
    ]

    column_details_list = [
        Executor.id,
        Executor.user,
        Executor.position,
        "requests_count"
    ]

    form_args = {
        'position': {
            'label': 'Должность',
            'description': 'Напишите должность'
        }
    }

    can_create = True # право создавать
    can_edit = True # право редактировать
    can_delete = True # право удалять
    can_view_details = True # право смотреть всю информацию
    can_export = True # право экспортировать

    name = "Исполнитель" # название
    name_plural = "Исполнители" # множественное название
    icon = "fa-solid fa-hammer" # иконка
    category = "Пользователи" # категория
    category_icon = "fa-solid fa-list" # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]

    async def on_model_change(self, data, model, is_created, request):
        if is_created and 'user' in data and data['user'].isdigit():
            existing = await sql_chek_update_role_by_user_id(
                user_id=int(data['user']),
                role=UserRole.EXECUTOR
            )
            if existing:
                raise ValidationError(f"Пользователь уже имеет роль!")

    async def scaffold_form(self, form_type: str = None) -> Type[Form]:
        form_class = await super().scaffold_form(form_type)
        users = await sql_get_users_without_role()

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
