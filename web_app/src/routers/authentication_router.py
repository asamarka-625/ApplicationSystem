# Внешние зависимости
from typing import Optional
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse, RedirectResponse
# Внутренние модули
from web_app.src.core import config
from web_app.src.dependencies import authenticate_user, create_access_token
from web_app.src.utils import token_service, create_reset_token, send_password_reset_email
from web_app.src.crud import sql_get_user_by_email
from web_app.src.schemas import PasswordResetRequest


router = APIRouter()


@router.post("/token", response_class=JSONResponse)
async def login_for_access_token(
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends()
):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False, # http
        samesite="lax",
        max_age=30 * 60  # 30 минут
    )

    await token_service.store_session(token=access_token, user_id=user.id)

    return {"message": "Login successful"}


@router.post("/logout")
async def logout(
        response: Response,
        access_token: Optional[str] = Cookie(None, alias="access_token")
):
    if access_token:
        await token_service.add_to_blacklist(access_token)

    response.delete_cookie(
        key="access_token",
        path="/"
    )

    return {"message": "Logout successful", "redirect": "/login"}


@router.get("/logout")
async def logout_get(
        access_token: Optional[str] = Cookie(None, alias="access_token")
):
    if access_token:
        await token_service.add_to_blacklist(access_token)

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token", path="/")
    return response


@router.get("/black_tokens", response_class=JSONResponse)
async def get_black_tokens():
    return await token_service.get_stats()


# Запрос на восстановление пароля
@router.post("/login/forgot-password", response_class=JSONResponse)
async def forgot_password(request: PasswordResetRequest):
    # Ищем пользователя по email
    user = await sql_get_user_by_email(email=request.email)

    if not user:
        return {"message": "Если пользователь с таким email существует, инструкции отправлены"}

    # Создаем токен восстановления
    reset_token = create_reset_token()

    await token_service.add_reset_password_token(
        token=reset_token,
        user_id=user.id
    )

    # Отправляем email
    email_sent = send_password_reset_email(
        to_email=user.email,
        reset_token=reset_token,
        username=user.username
    )

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error send email"
        )

    return {"message": "Если пользователь с таким email существует, инструкции отправлены"}

