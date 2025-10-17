# Внешние зависимости
from sqladmin import ModelView
from wtforms.validators import ValidationError
# Внутренние модули
from web_app.src.models import Category
from web_app.src.crud import sql_chek_existing_category_by_name


class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.name]
    column_labels = {
        Category.id: "Идентификатор",
        Category.name: "Название"
    }

    column_searchable_list = [Category.name] # список столбцов, которые можно искать
    column_sortable_list = [Category.id]  # список столбцов, которые можно сортировать
    column_default_sort = [(Category.id, True)]

    form_create_rules = [
        'name'
    ]

    form_args = {
        'name': {
            'label': 'Название товара'
        }
    }

    column_details_list = [Category.id, Category.name]

    form_edit_rules = [
        "name"
    ]

    can_create = True # право создавать
    can_edit = True # право редактировать
    can_delete = True # право удалять
    can_view_details = True # право смотреть всю информацию
    can_export = True # право экспортировать

    name = "Категория" # название
    name_plural = "Категории" # множественное название
    icon = "fa-solid fa-layer-group" # иконка
    category = "Продукция" # категория
    category_icon = "fa-solid fa-list" # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]

    async def on_model_change(self, data, model, is_created, request):
        # Проверка уникальности username
        if 'name' in data:
            if is_created:
                # При создании - проверяем что name не существует
                existing = await sql_chek_existing_category_by_name(data['name'])
                if existing:
                    raise ValidationError(f"Название '{data['name']}' уже существует")

        return await super().on_model_change(data, model, is_created, request)