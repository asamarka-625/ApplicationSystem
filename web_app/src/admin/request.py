# Внешние зависимости
from markupsafe import Markup
from sqladmin import ModelView
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
        Request.completed_at: "Выполнено",
        Request.department: "Отделение",
        Request.secretary: "Секретарь судьи",
        Request.judge: "Судья",
        Request.management: "НАУ",
        Request.management_department: "Сотрудник управления отдела",
        'items_formatted': "Запрошено",
        Request.description: "Описание",
        Request.description_management_department: "Комментарий от НАУ",
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
        Request.completed_at: lambda m, a: m.completed_at.strftime("%d.%m.%Y %H:%M") \
            if m.completed_at else "Не выполнено",
        'items_formatted': lambda m, a: RequestAdmin._format_items_detail(m.item_associations)
    }

    @staticmethod
    def _format_items_detail(associations):
        if not associations:
            return "Нет запрошенных элементов"

        items_links = []
        for association in associations:
            item_url = f"/admin/item/details/{association.item_id}"
            items_links.append(
                f'<a href="{item_url}" target="_blank" style="text-decoration: none; color: #007bff;">'
                f'Предмет #{association.item_id}</a>'
            )

        items_list = "<br>".join(items_links)
        return Markup(f"<div>{items_list}</div>")


    column_details_list = [
        Request.id,
        Request.registration_number,
        Request.request_type,
        Request.status,
        Request.is_emergency,
        Request.created_at,
        Request.update_at,
        Request.completed_at,
        Request.department,
        Request.secretary,
        Request.judge,
        Request.management,
        Request.management_department,
        'items_formatted',
        Request.description,
        Request.description_management_department
    ]

    can_create = False # право создавать
    can_edit = False # право редактировать
    can_delete = False # право удалять
    can_view_details = True # право смотреть всю информацию
    can_export = True # право экспортировать

    name = "Заявка" # название
    name_plural = "Заявки" # множественное название
    icon = "fa-solid fa-file" # иконка
    category = "Заявки" # категория
    category_icon = "fa-solid fa-folder-open" # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]