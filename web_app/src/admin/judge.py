# Внешние зависимости
from typing import Type
from sqladmin import ModelView
from sqladmin.forms import Form
from wtforms import SelectField
from wtforms.validators import ValidationError
# Внутренние модули
from web_app.src.models import Judge, UserRole
from web_app.src.crud import sql_chek_update_role_by_user_id, sql_get_users_without_role


class JudgeAdmin(ModelView, model=Judge):
    column_list = [
        Judge.id,
        Judge.user,
        Judge.department
    ]

    column_labels = {
        Judge.id: "Идентификатор",
        Judge.user: "Пользователь",
        Judge.department: "Отделение",
        "secretaries_count": "Количество секретарей",
        "requests_count": "Количество заявок"
    }

    column_searchable_list = [Judge.id]
    column_sortable_list = [Judge.id]
    column_default_sort = [(Judge.id, True)]

    column_formatters = {
        Judge.user: lambda m, a: m.user.full_name if m.user else "Не назначен",
        Judge.department: lambda m, a: m.department if m.department else "Не указано"
    }

    column_formatters_detail = {
        Judge.user: lambda m, a: m.user.full_name if m.user else "Не назначен",
        Judge.department: lambda m, a: m.department if m.department else "Не указано",
        "secretaries_count": lambda m, a: len(m.secretaries) if hasattr(m, 'secretaries')
                                                                and m.secretaries else 0,
        "requests_count": lambda m, a: len(m.judge_requests) if hasattr(m, 'judge_requests')
                                                                and m.judge_requests else 0
    }

    form_create_rules = [
        "user",
        "department"
    ]

    form_edit_rules = [
        "department"
    ]

    column_details_list = [
        Judge.id,
        Judge.user,
        Judge.department,
        "secretaries_count",
        "requests_count"
    ]

    form_args = {
        'department': {
            'label': 'Отделение',
            'description': 'Выберите отделение'
        }
    }

    can_create = True # право создавать
    can_edit = True # право редактировать
    can_delete = True # право удалять
    can_view_details = True # право смотреть всю информацию
    can_export = True # право экспортировать

    name = "Мировой судья" # название
    name_plural = "Мировые судьи" # множественное название
    icon = "fa-solid fa-earth-americas" # иконка
    category = "Пользователи" # категория
    category_icon = "fa-solid fa-list" # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]

    async def on_model_change(self, data, model, is_created, request):
        if is_created and 'user' in data and data['user'].isdigit():
            existing = await sql_chek_update_role_by_user_id(
                user_id=int(data['user']),
                role=UserRole.JUDGE
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
