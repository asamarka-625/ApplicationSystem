# Внешние зависимости
import re
from wtforms.validators import ValidationError


def _validate_phone(phone):
    """Валидация телефонного номера"""
    if len(phone) > 11:
        raise ValidationError('Номер телефона должен иметь 11 цифр')

    # Проверяем код страны/оператора
    if len(phone) == 11 and not phone.startswith(('7', '8')):
        raise ValidationError('Неверный формат номера. Должен начинаться с 7 или 8')


def validate_phone_from_form(form, field):
    """Валидация телефонного номера из формы"""
    if not field.data:  # Если поле пустое (Optional)
        return

    # Проверяем, что в строке есть только разрешенные символы
    if not re.match(r'^[\d\s\(\)\-\+]+$', field.data):
        raise ValidationError('Номер телефона может содержать только цифры, пробелы, скобки, дефисы и знак +')

    # Убираем все нецифровые символы для проверки формата
    phone = re.sub(r'\D', '', field.data)

    if not phone:  # Если после очистки ничего не осталось
        raise ValidationError('Номер телефона должен содержать цифры')

    _validate_phone(phone)


def validate_phone_list(phone_list):
    """Валидация списка телефонных номеров"""
    if not phone_list:
        return

    for phone in phone_list:
        phone = re.sub(r'\D', '', phone)
        _validate_phone(str(phone))