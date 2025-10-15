# Внешние зависимости
from typing import Annotated
from pydantic import Field
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
# Внутренние модули
from web_app.src.models import TYPE_ID_MAPPING, STATUS_ID_MAPPING, User
from web_app.src.schemas import RequestDetailResponse
from web_app.src.crud import (sql_get_requests_by_user, sql_get_request_details,
                              sql_get_all_departament)
from web_app.src.dependencies import get_current_user


router = APIRouter(
    prefix="/api/v1/request/view",
    tags=["API"],
)


@router.get(
    path="/info",
    response_class=JSONResponse,
    summary="Данные для фильтрации заявок"
)
async def get_info_for_view(departament: bool = False):
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
    current_user: User = Depends(get_current_user)
):
    requests = await sql_get_requests_by_user(
        user=current_user,
        status_filter=status,
        type_filter=request_type,
    )

    return {
        "rights": {
            "view": True,
            "edit": current_user.is_secretary or current_user.is_judge,
            "approve": current_user.is_judge or current_user.is_management,
            "reject": current_user.is_judge or current_user.is_management,
            "redirect": current_user.is_management,
            "deadline": current_user.is_management,
            "planning": current_user.is_management or current_user.is_executor,
            "ready": current_user.is_executor
        },
        "requests": requests
    }


@router.get(
    path="/detail/{registration_number}",
    response_model=RequestDetailResponse,
    summary="Детали заявки"
)
async def get_request_details(
    registration_number: Annotated[str, Field(strict=True)]
):
    details = await sql_get_request_details(
        registration_number=registration_number
    )

    return details