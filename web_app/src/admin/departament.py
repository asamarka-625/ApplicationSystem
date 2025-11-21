# Внешние зависимости
from typing import Type
from sqladmin import ModelView
from sqladmin.forms import Form
from wtforms import StringField
from wtforms.validators import InputRequired, ValidationError
# Внутренние модули
from web_app.src.models import Department
from web_app.src.utils import validate_phone_list
from web_app.src.crud import sql_delete_role_users_by_department_id


class DepartmentAdmin(ModelView, model=Department):
    column_list = [
        Department.id,
        Department.code,
        Department.name,
        Department.address
    ]

    column_labels = {
        Department.id: 'Идентификатор',
        Department.code: 'Номер судебного участка',
        Department.name: 'Название',
        Department.address: 'Адрес',
        Department.phone_numbers: 'Телефонные номера',
        "judges_count": "Количество судьей",
        "secretaries_count": "Количество секретарей",
        "requests_count": "Количество заявок"
    }

    column_searchable_list = [Department.code, Department.address] # список столбцов, которые можно искать
    column_sortable_list = [Department.id]  # список столбцов, которые можно сортировать
    column_default_sort = [(Department.id, True)]

    column_formatters_detail = {
        "judges_count": lambda m, a: len(m.judges) if hasattr(m, 'judges')
                                                                and m.judges else 0,
        "secretaries_count": lambda m, a: len(m.secretaries) if hasattr(m, 'secretaries')
                                                                and m.secretaries else 0,
        "requests_count": lambda m, a: len(m.requests) if hasattr(m, 'requests')
                                                                and m.requests else 0
    }

    form_create_rules = [
        'code',
        'name',
        'address',
        'phone_numbers'
    ]

    column_details_list = [
        Department.id,
        Department.code,
        Department.name,
        Department.address,
        Department.phone_numbers,
        "judges_count",
        "secretaries_count",
        "requests_count"
    ]

    form_edit_rules = [
        'code',
        'name',
        'address',
        'phone_numbers'
    ]

    can_create = True # право создавать
    can_edit = True # право редактировать
    can_delete = True # право удалять
    can_view_details = True # право смотреть всю информацию
    can_export = True # право экспортировать

    name = "Отделение" # название
    name_plural = "Отделения" # множественное название
    icon = "fa-solid fa-building-columns" # иконка
    category = "Организации" # категория
    category_icon = "fa-solid fa-building-user" # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]

    async def scaffold_form(self, form_type: str = None) -> Type[Form]:
        form_class = await super().scaffold_form(form_type)

        # Переопределяем поле phone_numbers
        form_class.phone_numbers = StringField(
            label='Телефонные номера',
            validators=[InputRequired()],
            description='Напишите телефонные номера через запятую'
        )

        return form_class

    async def on_model_change(self, data, model, is_created, request):
        if 'phone_numbers' in data:
            phone_numbers = data['phone_numbers']
            processed_phone_numbers = []
            replace_table = str.maketrans(
                {
                    '+': '',
                    '-': '',
                    '(': '',
                    ')': '',
                    '[': '',
                    ']': '',
                    "'": '',
                    ' ': ''
                }
            )

            if isinstance(phone_numbers, int):
                processed_phone_numbers.append(str(phone_numbers))

            elif isinstance(phone_numbers, list):
                for phone in phone_numbers:
                    if isinstance(phone, int):
                        processed_phone_numbers.append(str(phone))

                    elif isinstance(phone, str) and phone.isdigit():
                        processed_phone = phone.translate(replace_table)
                        if not processed_phone.isdigit():
                            raise ValidationError(f"Неправильный формат номера: {phone}")

                        processed_phone_numbers.append(processed_phone)

                    else:
                        raise ValidationError(f"Неправильный формат номера: {phone}")

            elif isinstance(phone_numbers, str):
                if "," in phone_numbers:
                    for phone in phone_numbers.split(","):
                        processed_phone = phone.translate(replace_table).strip()
                        if not processed_phone.isdigit():
                            raise ValidationError(f"Неправильный формат номера: {phone}")

                        processed_phone_numbers.append(processed_phone)

                elif phone_numbers.isdigit():
                    processed_phone_numbers.append(phone_numbers)

                else:
                    raise ValidationError(f"Неправильный формат номера: {phone_numbers}")

            # Обновляем данные перед валидацией
            data['phone_numbers'] = processed_phone_numbers
            validate_phone_list(phone_numbers)

        return await super().on_model_change(data, model, is_created, request)

    async def on_model_delete(self, model, request):
        if model:
            await sql_delete_role_users_by_department_id(department_id=model.id)