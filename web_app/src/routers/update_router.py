# Внешние зависимости
from typing import Annotated
from pydantic import Field
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
# Внутренние модули
from web_app.src.models import User, UserRole
from web_app.src.dependencies import get_current_user, get_current_user_with_role
from web_app.src.schemas import CreateRequest, RedirectRequest, CommentRequest, ScheduleRequest
from web_app.src.crud import (sql_edit_request, sql_approve_request, sql_reject_request,
                              sql_redirect_request, sql_deadline_request, sql_execute_request)


router = APIRouter(
    prefix="/api/v1/request",
    tags=["API"],
)


@router.patch(
    path="/edit/{registration_number}",
    response_class=JSONResponse,
    summary="Редактирование заявки"
)
async def edit_request(
        registration_number: Annotated[str, Field(strict=True)],
        data: CreateRequest,
        current_user: User = Depends(
            get_current_user_with_role((UserRole.SECRETARY, UserRole.JUDGE))
        )
):
    if not (current_user.is_secretary or current_user.is_judge):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

    role_id = current_user.secretary_profile.id if current_user.role == UserRole.SECRETARY \
        else current_user.judge_profile.id

    await sql_edit_request(
        registration_number=registration_number,
        user_id=current_user.id,
        role=current_user.role,
        role_id=role_id,
        data=data
    )

    return {"status": "success"}


@router.patch(
    path="/approve/{registration_number}",
    response_class=JSONResponse,
    summary="Утвердить заявку"
)
async def approve_request(
        registration_number: Annotated[str, Field(strict=True)],
        current_user: User = Depends(
            get_current_user_with_role((UserRole.JUDGE,))
        )
):
    if not current_user.is_judge:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

    await sql_approve_request(
        registration_number=registration_number,
        user_id=current_user.id,
        judge_id=current_user.judge_profile.id
    )

    return {"status": "success"}


@router.patch(
    path="/reject/{registration_number}",
    response_class=JSONResponse,
    summary="Отклонить заявку"
)
async def reject_request(
        data: CommentRequest,
        registration_number: Annotated[str, Field(strict=True)],
        current_user: User = Depends(
            get_current_user_with_role((UserRole.JUDGE, UserRole.MANAGEMENT))
        )
):
    if not (current_user.is_judge or current_user.is_management):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

    role_id = current_user.judge_profile.id if current_user.role == UserRole.JUDGE \
        else current_user.management_profile.id

    await sql_reject_request(
        registration_number=registration_number,
        user_id=current_user.id,
        role=current_user.role,
        role_id=role_id,
        comment=data.comment
    )

    return {"status": "success"}


@router.patch(
    path="/redirect/{registration_number}",
    response_class=JSONResponse,
    summary="Назначить исполнителя"
)
async def redirect_request(
        registration_number: Annotated[str, Field(strict=True)],
        data: RedirectRequest,
        current_user: User = Depends(
            get_current_user_with_role((UserRole.MANAGEMENT,))
        )
):
    if not current_user.is_management:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

    await sql_redirect_request(
        registration_number=registration_number,
        user_id=current_user.id,
        management_id=current_user.management_profile.id,
        data=data
    )

    return {"status": "success"}


@router.patch(
    path="/deadline/{registration_number}",
    response_class=JSONResponse,
    summary="Назначить сроки"
)
async def deadline_request(
        registration_number: Annotated[str, Field(strict=True)],
        data: ScheduleRequest,
        current_user: User = Depends(get_current_user)
):
    if not current_user.is_management:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

    await sql_deadline_request(
        registration_number=registration_number,
        user_id=current_user.id,
        deadline=data.scheduled_datetime
    )

    return {"status": "success"}


@router.patch(
    path="/execute/{registration_number}",
    response_class=JSONResponse,
    summary="Выполнить заявку"
)
async def execute_request(
        registration_number: Annotated[str, Field(strict=True)],
        current_user: User = Depends(get_current_user)
):
    if not current_user.is_executor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

    await sql_execute_request(
        registration_number=registration_number,
        user_id=current_user.id
    )

    return {"status": "success"}