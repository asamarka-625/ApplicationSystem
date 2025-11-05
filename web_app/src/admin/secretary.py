# Внешние зависимости
from typing import Type
from sqladmin import ModelView
from sqladmin.forms import Form
from wtforms import SelectField
from wtforms.validators import ValidationError
# Внутренние модули
from web_app.src.models import Secretary, UserRole
from web_app.src.crud import (sql_chek_update_role_by_user_id, sql_get_department_id_by_judge_id,
                              sql_get_users_without_role, sql_update_role_by_user_id)


class SecretaryAdmin(ModelView, model=Secretary):
    column_list = [
        Secretary.id,
        Secretary.user,
        Secretary.judge
    ]

    column_labels = {
        Secretary.id: "Идентификатор",
        Secretary.user: "Пользователь",
        Secretary.judge: "Судья",
        Secretary.department: "Отделение",
        "requests_count": "Количество заявок"
    }

    column_searchable_list = [Secretary.id]
    column_sortable_list = [Secretary.id]
    column_default_sort = [(Secretary.id, True)]

    column_formatters = {
        Secretary.user: lambda m, a: m.user.full_name if m.user else "Не назначен",
        Secretary.judge: lambda m, a: m.judge.user.full_name if m.judge else "Не указано"
    }

    column_formatters_detail = {
        Secretary.user: lambda m, a: m.user if m.user else "Не назначен",
        Secretary.judge: lambda m, a: m.judge if m.judge else "Не указано",
        Secretary.department: lambda m, a: m.department if m.department else "Не указано",
        "requests_count": lambda m, a: len(m.secretary_requests) if hasattr(m, 'secretary_requests')
                                                                    and m.secretary_requests else 0
    }

    form_create_rules = [
        "user",
        "judge"
    ]

    column_details_list = [
        Secretary.id,
        Secretary.user,
        Secretary.judge,
        Secretary.department,
        "requests_count"
    ]

    form_edit_rules = [
        "judge"
    ]

    form_args = {
        'judge': {
            'label': 'Судья',
            'description': 'Выберите Судью'
        }
    }

    can_create = True # право создавать
    can_edit = True # право редактировать
    can_delete = True # право удалять
    can_view_details = True # право смотреть всю информацию
    can_export = True # право экспортировать

    name = "Секретарь" # название
    name_plural = "Секретари" # множественное название
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
                role=UserRole.SECRETARY
            )
            if existing:
                raise ValidationError(f"Пользователь уже имеет роль!")

            if data['judge'] and data['judge'].isdigit():
                data['department_id'] = await sql_get_department_id_by_judge_id(
                    judge_id=int(data['judge'])
                )

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
