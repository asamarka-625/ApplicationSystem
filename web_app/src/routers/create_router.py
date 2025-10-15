# Внешние зависимости
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi import HTTPException, status
from pydantic import Field
# Внутренние модули
from web_app.src.crud import sql_search_items, sql_create_request, sql_search_executors
from web_app.src.models import TYPE_ID_MAPPING, User, UserRole
from web_app.src.schemas import CreateRequest
from web_app.src.dependencies import get_current_user, get_current_user_with_role


router = APIRouter(
    prefix="/api/v1/request/create",
    tags=["API"],
)


@router.get(
    path="/info",
    response_class=JSONResponse,
    summary="Данные для создания заявки"
)
async def get_info_for_create(current_user: User = Depends(get_current_user)):
    if not (current_user.is_secretary or current_user.is_judge):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

    return {
        "request_type": TYPE_ID_MAPPING
    }    
    
@router.get(
    path="/item/",
    response_class=JSONResponse,
    summary="Поиск предметов"
)
async def search_items(
        search: Annotated[
            str,
            Field(strict=True, max_length=50, strip_whitespace=True)
        ],
        current_user: User = Depends(get_current_user)
):
    if not (current_user.is_secretary or current_user.is_judge):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

    items = await sql_search_items(search=search)

    return items


@router.get(
    path="/executor/",
    response_class=JSONResponse,
    summary="Поиск исполнителей"
)
async def search_executors(
        search: Annotated[
            str,
            Field(strict=True, max_length=50, strip_whitespace=True)
        ],
        current_user: User = Depends(get_current_user)
):
    if not current_user.is_management:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

    executors = await sql_search_executors(search=search)

    return executors

@router.post(
    path="/",
    response_class=JSONResponse,
    summary="Создание новой заявки"
)
async def create_request(
        data: CreateRequest,
        current_user: User = Depends(get_current_user_with_role(
            (UserRole.SECRETARY,)
        )),
):
    print(data)
    if not current_user.is_secretary:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

    request_id = await sql_create_request(
        data=data,
        user_id=current_user.id,
        secretary_id=current_user.secretary_profile.id,
        judge_id=current_user.secretary_profile.judge_id,
        department_id=current_user.secretary_profile.department_id
    )

    return {"status": "success", "registration_number": request_id}