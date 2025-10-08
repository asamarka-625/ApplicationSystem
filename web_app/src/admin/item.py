# Внешние зависимости
from sqladmin import ModelView
from wtforms.validators import ValidationError
# Внутренние модули
from web_app.src.models import Item
from web_app.src.crud import sql_chek_existing_item_by_serial, sql_get_categories_choices


class ItemAdmin(ModelView, model=Item):
    column_list = [Item.id, Item.serial_number, Item.name]
    column_labels = {
        Item.id: "Идентификатор",
        Item.serial_number: "Серийный номер",
        Item.name: "Название",
        Item.description: "Описание",
        Item.category: "Категория"
    }

    column_searchable_list = [Item.name, Item.serial_number] # список столбцов, которые можно искать
    column_sortable_list = [Item.id]  # список столбцов, которые можно сортировать
    column_default_sort = [(Item.id, True)]

    form_create_rules = [
        'name',
        'serial_number',
        'description',
        'category'
    ]

    form_args = {
        'name': {
            'label': 'Название товара'
        },
        'serial_number': {
            'label': 'Серийный номер',
        },
        'description': {
            'label': 'Описание'
        },
        'category': {
            'label': 'Категория',
            'description': 'Выберите категорию товара',
        }
    }

    # Переопределяем метод для загрузки формы
    async def scaffold_form(self, form_type=None):
        form = await super().scaffold_form(form_type)

        # Динамически загружаем категории
        if hasattr(form, 'category'):
            form.category.choices = await sql_get_categories_choices()

        return form

    # При создании пользователя
    async def on_model_change(self, data, model, is_created, request):
        # Проверка уникальности username
        if 'serial_number' in data:
            if is_created:
                # При создании - проверяем что serial_number не существует
                existing = await sql_chek_existing_item_by_serial(data['serial_number'])
                if existing:
                    raise ValidationError(f"Серийный номер '{data['serial_number']}' уже существует")

        return await super().on_model_change(data, model, is_created, request)

    column_details_list = [
        Item.id,
        Item.serial_number,
        Item.name,
        Item.category,
        Item.description
    ]

    form_edit_rules = [
        "name",
        "description",
        "category",
        "serial_number"
    ]

    can_create = True # право создавать
    can_edit = True # право редактировать
    can_delete = True # право удалять
    can_view_details = True # право смотреть всю информацию
    can_export = True # право экспортировать

    name = "Товар" # название
    name_plural = "Товары" # множественное название
    icon = "fa-solid fa-box-open" # иконка
    category = "Продукция" # категория
    category_icon = "fa-solid fa-list" # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]