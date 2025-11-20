# Внешние зависимости
from typing import Optional, Tuple
from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt
from fastapi import HTTPException, status, Cookie
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import UserRole, User
from web_app.src.crud import sql_get_user_by_id, sql_get_user_by_username
from web_app.src.utils import verify_password
from web_app.src.utils import token_service


async def authenticate_user(username: str, password: str):
    user = await sql_get_user_by_username(username=username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt


async def get_current_user(
        access_token: Optional[str] = Cookie(None, alias="access_token")
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Проверяем наличие токена в куках
    if not access_token:
        raise credentials_exception

    if await token_service.is_blacklisted(access_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )

    try:
        payload = jwt.decode(access_token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        # Преобразуем в int для базы данных
        user_id = int(user_id_str)

    except JWTError:
        raise credentials_exception

    user = await sql_get_user_by_id(user_id=user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active or user.role is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return user


def get_current_user_with_role(roles: Optional[Tuple[UserRole]] = None):
    """Фабрика для создания зависимости с указанием ролей"""

    async def role_dependency(
            access_token: Optional[str] = Cookie(None, alias="access_token"),
    ):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if not access_token:
            raise credentials_exception

        if await token_service.is_blacklisted(access_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )

        try:
            payload = jwt.decode(access_token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            user_id_str: str = payload.get("sub")
            if user_id_str is None:
                raise credentials_exception

            user_id = int(user_id_str)

        except JWTError:
            raise credentials_exception

        user = await sql_get_user_by_id(user_id=user_id, role=roles)
        if user is None:
            raise credentials_exception

        if not user.is_active or user.role is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

        return user

    return role_dependency
