import secrets
import string


# Генерация случайного секретного ключа (32 байта = 256 бит)
secret_key = secrets.token_urlsafe(32)
print(f"Секретный ключ: {secret_key}")


def generate_password(length=8, use_digits=True, use_special=True):
    characters = string.ascii_letters

    if use_digits:
        characters += string.digits
    if use_special:
        characters += "!@#$%^&*"

    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


# Использование
password = generate_password()
print(f"Сгенерированный пароль: {password}")