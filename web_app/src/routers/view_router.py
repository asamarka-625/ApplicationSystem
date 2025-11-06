# Внешние зависимости
from typing import Annotated
from pydantic import Field
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
# Внутренние модули
from web_app.src.models import TYPE_ID_MAPPING, STATUS_ID_MAPPING, User, UserRole
from web_app.src.crud import (sql_get_requests_by_user, sql_get_request_details,
                              sql_get_all_departament, sql_get_request_data)
from web_app.src.dependencies import get_current_user, get_current_user_with_role
from web_app.src.utils import get_allowed_rights


router = APIRouter(
    prefix="/api/v1/request/view",
    tags=["API"],
)


@router.get(
    path="/filter/info",
    response_class=JSONResponse,
    summary="Данные для фильтрации заявок"
)
async def get_filter_info(departament: bool = False):
    result = {
        "request_type": TYPE_ID_MAPPING,
        "status": STATUS_ID_MAPPING
    }

    if departament:
        result["departament"] = await sql_get_all_departament()

    return result


@router.get(
    path="/list/",
    response_class=JSONResponse,
    summary="Список заявок пользователя"
)
async def get_requests_by_user(
    status: str = "all",
    request_type: str = "all",
    for_executor: bool = False,
    current_user: User = Depends(get_current_user_with_role(tuple(UserRole))),
):
    if for_executor:
        requests = await sql_get_requests_for_executor(
            user=current_user,
            status_filter=status,
            type_filter=request_type,
        )

    else:
        requests = await sql_get_requests_by_user(
            user=current_user,
            status_filter=status,
            type_filter=request_type,
        )

    return {
        "rights": get_allowed_rights(current_user),
        "requests": requests
    }


@router.get(
    path="/data/{registration_number}",
    response_class=JSONResponse,
    summary="Данные заявки"
)
async def get_request_data(
    registration_number: Annotated[str, Field(strict=True)]
):
    data = await sql_get_request_data(
        registration_number=registration_number
    )

    return data


@router.get(
    path="/detail/{registration_number}",
    response_class=JSONResponse,
    summary="Детали заявки"
)
async def get_request_details(
    registration_number: Annotated[str, Field(strict=True)],
    current_user: User = Depends(get_current_user)
):
    details = await sql_get_request_details(
        registration_number=registration_number,
        role=current_user.role
    )

    return {
        "rights": get_allowed_rights(current_user),
        "details": details
    }