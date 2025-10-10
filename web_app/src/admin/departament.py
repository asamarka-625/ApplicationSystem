# Внешние зависимости
from sqladmin import ModelView
# Внутренние модули
from web_app.src.models import Department
from web_app.src.utils import validate_phone_list


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
        Department.phone_numbers: 'Телефонные номера'
    }

    column_searchable_list = [Department.code, Department.address] # список столбцов, которые можно искать
    column_sortable_list = [Department.id]  # список столбцов, которые можно сортировать
    column_default_sort = [(Department.id, True)]

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
        Department.phone_numbers
    ]

    form_edit_rules = [
        'code',
        'name',
        'address',
        'phone_numbers'
    ]

    async def on_model_change(self, data, model, is_created, request):
        if 'phone_numbers' in data:
            validate_phone_list(data['phone_numbers'])

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