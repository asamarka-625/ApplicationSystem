# Внешние зависимости
from sqladmin import ModelView
from wtforms import PasswordField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email
import bcrypt  # или другой хэширующий алгоритм
# Внутренние модули
from web_app.src.models import User, ROLE_MAPPING
from web_app.src.crud import sql_chek_existing_user_by_name, sql_chek_existing_user_by_email
from web_app.src.utils import validate_phone_from_form


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.role, User.username, User.full_name, User.email]
    column_labels = {
        User.id: "Идентификатор",
        User.role: "Роль",
        User.username: "Имя пользователя",
        User.full_name: "ФИО",
        User.email: "Email",
        User.position: "Должность",
        User.phone: "Номер телефона",
        User.last_login: "Последняя дата входа",
        User.is_active: "Статус"
    }

    column_searchable_list = [User.full_name] # список столбцов, которые можно искать
    column_sortable_list = [User.id]  # список столбцов, которые можно сортировать
    column_default_sort = [(User.id, True)]

    column_formatters = {
        User.role: lambda m, a: m.role.value.capitalize() if m.role else ''
    }

    column_formatters_detail = {
        User.role: lambda m, a: m.role.value.capitalize() if m.role else '',
        User.is_active: lambda m, a: "Активен" if m.is_active else "Неактивен",
        User.last_login: lambda m, a: m.last_login.strftime("%d.%m.%Y %H:%M") if m.last_login else "Не заходил"
    }

    form_create_rules = [
        'username',
        'full_name',
        'email',
        'password_hash',
        'role',
        'position',
        'phone',
        'is_active'
    ]
    # Добавляем виртуальное поле password
    form_overrides = {
        'password_hash': PasswordField,
        'role': SelectField,
        'is_active': SelectField
    }

    form_args = {
        'username': {
            'label': 'Уникальное имя',
            'description': 'Придумайте уникальное'
        },
        'email': {
            'label': 'Электронная почта',
            'validators': [DataRequired(), Email()],
            'description': 'Напишите вашу электронную почту'
        },
        'password_hash': {
            'label': 'Пароль',
            'validators': [DataRequired()],
            'description': 'Придумайте пароль'
        },
        'full_name': {
            'label': 'ФИО',
            'description': 'Напишите ваше ФИО полностью'
        },
        'role': {
            'label': 'Роль',
            'description': 'Выберите роль пользователя',
            'choices': [
                ('сотрудник комитета', 'Сотрудник комитета'),
                ('сотрудник управления', 'Сотрудник управления'),
                ('мировой судья', 'Мировой судья'),
                ('секретарь суда', 'Секретарь суда'),
                ('сотрудник фбу', 'Сотрудник ФБУ'),
                ('исполнитель', 'Исполнитель')
            ],
            'coerce': lambda x: x
        },
        'position': {
            'label': 'Должность',
            'description': 'Напишите вашу должность'
        },
        'phone': {
            'label': 'Номер телефона',
            'validators': [DataRequired(), validate_phone_from_form],
            'description': 'Напишите ваш номер тедефона'
        },
        'is_active': {
            'label': 'Статус',
            'description': 'Выберите статус пользоваеля',
            'choices': [("Активен", "Активен"), ("Неактивен", "Неактивен")],  # ИСПРАВЛЕНО
            'coerce': lambda x: x == "Активен"
        }
    }

    # При создании пользователя
    async def on_model_change(self, data, model, is_created, request):
        if 'role' in data:
            convert_role = data['role']
            data['role'] = ROLE_MAPPING[convert_role]

        if 'full_name' in data:
            data['full_name'] = data['full_name'].lower()
            full_name_list = data['full_name'].split(' ')
            if len(full_name_list) > 1:
                data['full_name'] = ' '.join(string.capitalize() for string in full_name_list)

            else:
                raise ValidationError(f"Неправильный формат ФИО: '{data['full_name']}'")

        # Проверка уникальности username
        if 'username' in data:
            data['username'] = data['username'].lower()
            existing = await sql_chek_existing_user_by_name(data['username'])
            if is_created:
                if existing is not None:
                    raise ValidationError(f"Уникальное имя '{data['username']}' уже существует")
            else:
                if model.id != existing:
                    raise ValidationError(f"Уникальное имя '{data['username']}' уже занят")

        # Проверка уникальности email
        if 'email' in data:
            data['email'] = data['email'].lower()
            existing = await sql_chek_existing_user_by_email(data['email'])
            if is_created:
                if existing is not None:
                    raise ValidationError(f"Email '{data['email']}' уже зарегистрирован")
            else:
                if model.id != existing:
                    raise ValidationError(f"Email '{data['username']}' уже используется")

        # Хэширование пароля
        if 'password_hash' in data:
            password = data['password_hash']
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt)

            # Сохраняем хэш
            data['password_hash'] = hashed_password.decode('utf-8')

        return await super().on_model_change(data, model, is_created, request)

    column_details_list = [
        User.id,
        User.full_name,
        User.username,
        User.role,
        User.email,
        User.position,
        User.phone,
        User.last_login,
        User.is_active
    ]

    form_edit_rules = [
        "username",
        "email",
        "password_hash",
        "full_name",
        "role",
        "position",
        "phone",
        "is_active"
    ]

    can_create = True # право создавать
    can_edit = True # право редактировать
    can_delete = True # право удалять
    can_view_details = True # право смотреть всю информацию
    can_export = True # право экспортировать

    name = "Пользователь" # название
    name_plural = "Пользователи" # множественное название
    icon = "fa-solid fa-circle-user" # иконка
    category = "Аккаунты" # категория
    category_icon = "fa-solid fa-list" # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]