# Внешние зависимости
from typing import Annotated, Optional
from pydantic import Field
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as status_
from fastapi.responses import JSONResponse
# Внутренние модули
from web_app.src.models import TYPE_ID_MAPPING, STATUS_ID_MAPPING, User, UserRole, REQUEST_ITEM_STATUS_ID_MAPPING
from web_app.src.crud import (sql_get_requests_by_user, sql_get_request_details,
                              sql_get_all_department, sql_get_request_data, sql_get_requests_for_executor,
                              sql_get_planning_requests)
from web_app.src.dependencies import get_current_user_with_role, get_current_user
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
async def get_filter_info(
    current_user: User = Depends(get_current_user)
):
    result = {
        "request_type": TYPE_ID_MAPPING,
        "department": await sql_get_all_department()
    }

    if current_user.is_management:
        result["status"] = STATUS_ID_MAPPING[1:]

    elif current_user.is_management_department:
        result["status"] = STATUS_ID_MAPPING[2:]

    elif current_user.role in (UserRole.EXECUTOR, UserRole.EXECUTOR_ORGANIZATION):
        result["status"] = REQUEST_ITEM_STATUS_ID_MAPPING

    else:
        result["status"] = STATUS_ID_MAPPING

    return result


@router.get(
    path="/list/requests",
    response_class=JSONResponse,
    summary="Список заявок пользователя"
)
async def get_requests_by_user(
    status: Optional[int] = None,
    request_type: Optional[int] = None,
    department: Optional[int] = None,
    current_user: User = Depends(get_current_user_with_role(tuple(UserRole)))
):
    if current_user.is_executor or current_user.is_executor_organization:
        requests = await sql_get_requests_for_executor(
            user=current_user,
            status_filter_id=status,
            type_filter_id=request_type,
            department_filter_id=department
        )

    else:
        requests = await sql_get_requests_by_user(
            user=current_user,
            status_filter_id=status,
            type_filter_id=request_type,
            department_filter_id=department
        )

    return {
        "rights": get_allowed_rights(current_user),
        "requests": requests
    }


@router.get(
    path="/list/planning",
    response_class=JSONResponse,
    summary="Список планирования заявок пользователя"
)
async def get_planning_requests_by_user(
    department: Optional[int] = None,
    current_user: User = Depends(
        get_current_user_with_role((UserRole.MANAGEMENT, UserRole.MANAGEMENT_DEPARTMENT,
                                    UserRole.EXECUTOR, UserRole.EXECUTOR_ORGANIZATION))
    )
):
    if not (current_user.is_management or current_user.is_management_department or
            current_user.is_executor or current_user.is_executor_organization):
        raise HTTPException(status_code=status_.HTTP_403_FORBIDDEN, detail="Not enough rights")

    planning = await sql_get_planning_requests(
        user=current_user,
        department_filter_id=department
    )

    return {
        "rights": get_allowed_rights(current_user),
        "planning": planning
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
    current_user: User = Depends(
        get_current_user_with_role((UserRole.EXECUTOR, UserRole.EXECUTOR_ORGANIZATION))
    )
):
    details = await sql_get_request_details(
        registration_number=registration_number,
        user=current_user
    )

    return {
        "rights": get_allowed_rights(current_user),
        "details": details
    }