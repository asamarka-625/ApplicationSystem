# Внешние зависимости
from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
# Внутренние модули
from web_app.src.core import config


class BasicAuthBackend(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        # Проверка учетных данных
        if username == config.ADMIN_LOGIN and password == config.ADMIN_PASSWORD:
            payload = {
                "sub": "admin",
                "exp": datetime.now(UTC) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
                "iat": datetime.now(UTC),
            }
            token = jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)
            request.session.update({"admin_token": token})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("admin_token")
        if not token:
            return False

        try:
            payload = jwt.decode(
                token,
                config.SECRET_KEY,
                algorithms=[config.ALGORITHM],
                options={"require": ["exp", "iat", "sub"]}
            )

            if payload.get("sub") == "admin":
                return True
            return False

        except JWTError:
            return False
