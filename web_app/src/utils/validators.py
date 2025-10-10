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
    # Убираем все нецифровые символы
    phone = re.sub(r'\D', '', field.data)
    _validate_phone(str(phone))


def validate_phone_list(phone_list):
    """Валидация списка телефонных номеров"""
    if not phone_list:
        return

    for phone in phone_list:
        phone = re.sub(r'\D', '', phone)
        _validate_phone(str(phone))