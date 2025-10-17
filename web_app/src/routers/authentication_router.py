# Внешние зависимости
from typing import Optional
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse, RedirectResponse
# Внутренние модули
from web_app.src.core import config
from web_app.src.dependencies import authenticate_user, create_access_token, get_current_user


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

    if config.active_session_tokens.get(user.id, False):
        config.active_session_tokens[user.id].add(access_token)

    else:
        config.active_session_tokens[user.id] = set()
        config.active_session_tokens[user.id].add(access_token)

    return {"message": "Login successful"}


@router.post("/logout")
async def logout(
        response: Response,
        access_token: Optional[str] = Cookie(None, alias="access_token")
):
    if access_token:
        user = await get_current_user(access_token)
        config.blacklisted_tokens.add(access_token)
        config.active_session_tokens[user.id].discard(access_token)

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
        user = await get_current_user(access_token)
        config.blacklisted_tokens.add(access_token)
        config.active_session_tokens[user.id].discard(access_token)

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token", path="/")
    return response


@router.get("/black_tokens", response_class=JSONResponse)
async def get_black_tokens():
    return {
        "count_black_tokens": len(config.blacklisted_tokens),
        "black_list_tokens": config.blacklisted_tokens
    }

@router.get("/active_tokens", response_class=JSONResponse)
async def get_black_tokens():
    return {
        "count_active_tokens": sum(len(value) for value in config.active_session_tokens.values()),
        "active_list_tokens": config.active_session_tokens
    }

