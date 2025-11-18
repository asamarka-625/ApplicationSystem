# Внешние зависимости
import secrets
import string
from passlib.context import CryptContext


# Настройки безопасности
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    # Опциональные настройки для большей безопасности
    argon2__time_cost=2,
    argon2__memory_cost=1024,
    argon2__parallelism=2,
)


# Вспомогательные функции
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_reset_token():
    return secrets.token_urlsafe(32)


def generate_password(length: int):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password
