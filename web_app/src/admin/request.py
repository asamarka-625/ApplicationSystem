# Внешние зависимости
import uuid
from markupsafe import Markup
from sqladmin import ModelView
from wtforms import SelectField
# Внутренние модули
from web_app.src.models import Request


class RequestAdmin(ModelView, model=Request):
    column_list = [
        Request.id,
        Request.registration_number,
        Request.request_type,
        Request.status,
        Request.is_emergency
    ]

    column_labels = {
        Request.id: "Идентификатор",
        Request.registration_number: "Регистрационный номер",
        Request.request_type: "Тип заявки",
        Request.status: "Статус заявки",
        Request.is_emergency: "Срочность",
        Request.created_at: "Дата создания",
        Request.update_at: "Дата обновления",
        Request.deadline: "Срок выполнения",
        Request.completed_at: "Выполнено",
        Request.department: "Отделение",
        'items_formatted': "Запрошено"
    }

    column_searchable_list = [Request.registration_number] # список столбцов, которые можно искать
    column_sortable_list = [Request.id]  # список столбцов, которые можно сортировать
    column_default_sort = [(Request.id, True)]

    column_formatters = {
        Request.request_type: lambda m, a: m.request_type.value.capitalize() if m.request_type else '',
        Request.status: lambda m, a: m.status.value.capitalize() if m.status else ''
    }

    column_formatters_detail = {
        Request.request_type: lambda m, a: m.request_type.value.capitalize() if m.request_type else '',
        Request.status: lambda m, a: m.status.value.capitalize() if m.status else '',
        Request.created_at: lambda m, a: m.created_at.strftime("%d.%m.%Y %H:%M") if m.created_at else "Не создан",
        Request.update_at: lambda m, a: m.update_at.strftime("%d.%m.%Y %H:%M") if m.update_at else "Не обновлен",
        Request.deadline: lambda m, a: m.deadline.strftime("%d.%m.%Y %H:%M") if m.deadline else "Не установлен",
        Request.completed_at: lambda m, a: m.completed_at.strftime("%d.%m.%Y %H:%M") \
            if m.completed_at else "Не выполнено",
        'items_formatted': lambda m, a: RequestAdmin._format_items_detail(m.items)
    }

    @staticmethod
    def _format_items_detail(items):
        """Детальное форматирование с ссылками"""
        if not items:
            return "Нет запрошенных элементов"

        items_links = []
        for item in items:
            item_url = f"/admin/item/details/{item.id}"
            items_links.append(
                f'<a href="{item_url}" target="_blank" style="text-decoration: none; color: #007bff;">'
                f'{item.name} (SN: {item.serial_number})'
                f'</a>'
            )

        items_list = "<br>".join(items_links)  # используем <br> вместо \n
        return Markup(f"<div>{items_list}</div>")  # оборачиваем в Markup

    form_create_rules = [
        'department',
        'creator',
        'items',
        'description',
        'request_type',
        'is_emergency'
    ]

    form_overrides = {
        'request_type': SelectField,
    }

    form_args = {
        'request_type': {
            'label': 'Тип заявки',
            'description': 'Выберите тип заявки',
            'choices': [
                ('материально-техническое обеспечение', 'Материально-техническое обеспечение'),
                ('техническое обслуживание', 'Техническое обслуживание'),
                ('эксплуатационное обслуживание', 'Эксплуатационное обслуживание'),
                ('аварийная', 'Аварийная')
            ],
            'coerce': lambda x: x
        }
    }

    async def on_model_change(self, data, model, is_created, request):
        if is_created:
            data['registration_number'] = str(uuid.uuid4())

    column_details_list = [
        Request.id,
        Request.registration_number,
        Request.request_type,
        Request.status,
        Request.is_emergency,
        Request.created_at,
        Request.update_at,
        Request.deadline,
        Request.completed_at,
        Request.department,
        'items_formatted'
    ]

    form_edit_rules = [
        'department',
        'creator',
        'items',
        'description',
        'request_type',
        'is_emergency',
        'assignee',
        'deadline',
        'status'
    ]

    can_create = True # право создавать
    can_edit = True # право редактировать
    can_delete = True # право удалять
    can_view_details = True # право смотреть всю информацию
    can_export = True # право экспортировать

    name = "Заявка" # название
    name_plural = "Заявки" # множественное название
    icon = "fa-solid fa-file" # иконка
    category = "Заявки" # категория
    category_icon = "fa-solid fa-folder-open" # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]