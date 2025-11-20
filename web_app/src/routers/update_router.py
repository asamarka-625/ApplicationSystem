# Внешние зависимости
from typing import Annotated, Optional, List
import json
from pydantic import Field
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from fastapi.responses import JSONResponse
# Внутренние модули
from web_app.src.models import User, UserRole
from web_app.src.dependencies import get_current_user, get_current_user_with_role
from web_app.src.schemas import (CreateRequest, RedirectRequest, CommentRequest, ItemsExecuteRequest,
                                 RedirectRequestWithDeadline, PlanningRequest, ItemsRequest)
from web_app.src.crud import (sql_edit_request, sql_approve_request, sql_reject_request,
                              sql_redirect_executor_request, sql_execute_request,
                              sql_redirect_management_request, sql_redirect_organization_request,
                              sql_planning_request, sql_finish_request, sql_delete_attachment)
from web_app.src.core import config
from web_app.src.utils import save_uploaded_files, delete_files


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
        items: str = Form(None),
        is_emergency: bool = Form(False),
        description: str = Form(...),
        request_type: int = Form(...),
        attachments: Optional[List[UploadFile]] = File(None),
        current_user: User = Depends(
            get_current_user_with_role((UserRole.SECRETARY, UserRole.JUDGE))
        )
):
    if not (current_user.is_secretary or current_user.is_judge):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    items_list = []
    if items and items != "null":
        try:
            items_data = json.loads(items)
            if items_data:  # Проверяем что не пустой массив
                items_list.extend([ItemsRequest(**item) for item in items_data])

        except json.JSONDecodeError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid items JSON")

    if not items_list:
        items_list.append(ItemsRequest(
            id=config.MAINTENANCE_ITEM_ID,
            quantity=1
        ))

    request_data = CreateRequest(
        items=items_list,
        is_emergency=is_emergency,
        description=description,
        request_type=request_type
    )

    role_id = current_user.secretary_profile.id if current_user.role == UserRole.SECRETARY \
        else current_user.judge_profile.id

    files_info = await save_uploaded_files(attachments)
    request_data.attachments = files_info

    try:
        await sql_edit_request(
            registration_number=registration_number,
            user_id=current_user.id,
            role=current_user.role,
            role_id=role_id,
            data=request_data
        )

    except:
        delete_files(file_paths=[file.file_path for file in files_info])
        raise

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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

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
    path="/redirect/management/{registration_number}",
    response_class=JSONResponse,
    summary="Назначить сотрудника отдела"
)
async def redirect_management_request(
        registration_number: Annotated[str, Field(strict=True)],
        data: RedirectRequest,
        current_user: User = Depends(
            get_current_user_with_role((UserRole.MANAGEMENT,))
        )
):
    if not current_user.is_management:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    await sql_redirect_management_request(
        registration_number=registration_number,
        user_id=current_user.id,
        management_id=current_user.management_profile.id,
        data=data
    )

    return {"status": "success"}


@router.patch(
    path="/redirect/executor/{registration_number}",
    response_class=JSONResponse,
    summary="Назначить исполнителя"
)
async def redirect_executor_request(
        registration_number: Annotated[str, Field(strict=True)],
        data: RedirectRequestWithDeadline,
        current_user: User = Depends(
            get_current_user_with_role((UserRole.MANAGEMENT_DEPARTMENT,))
        )
):
    if not (current_user.is_management_department or current_user.is_management):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    await sql_redirect_executor_request(
        registration_number=registration_number,
        user_id=current_user.id,
        data=data,
        user=current_user
    )

    return {"status": "success"}


@router.patch(
    path="/redirect/organization/{registration_number}",
    response_class=JSONResponse,
    summary="Назначить организацию-исполнителя"
)
async def redirect_organization_request(
        registration_number: Annotated[str, Field(strict=True)],
        data: RedirectRequestWithDeadline,
        current_user: User = Depends(
            get_current_user_with_role((UserRole.EXECUTOR,))
        )
):
    if not (current_user.is_management_department or current_user.is_management or current_user.is_executor):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    await sql_redirect_organization_request(
        registration_number=registration_number,
        user_id=current_user.id,
        data=data,
        user=current_user
    )

    return {"status": "success"}


@router.patch(
    path="/execute/{registration_number}",
    response_class=JSONResponse,
    summary="Выполнить заявку"
)
async def execute_request(
        registration_number: Annotated[str, Field(strict=True)],
        data: Optional[ItemsExecuteRequest] = None,
        current_user: User = Depends(get_current_user)
):
    if current_user.role in (UserRole.EXECUTOR, UserRole.EXECUTOR_ORGANIZATION) and data:
        await sql_execute_request(
            registration_number=registration_number,
            user_id=current_user.id,
            item_id=data.id,
            comment=data.comment
        )

    elif current_user.role in (UserRole.MANAGEMENT_DEPARTMENT, UserRole.MANAGEMENT):
        await sql_finish_request(
            registration_number=registration_number,
            user=current_user
        )

    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    return {"status": "success"}


@router.patch(
    path="/planning/{registration_number}",
    response_class=JSONResponse,
    summary="Добавить предмет в планирование"
)
async def planning_request(
    registration_number: Annotated[str, Field(strict=True)],
    data: PlanningRequest,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_executor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    await sql_planning_request(
        registration_number=registration_number,
        user_id=current_user.id,
        data=data
    )

    return {"status": "success"}


@router.delete(
    path="/attachment/{registration_number}/{filename}",
    response_class=JSONResponse,
    summary="Удалить прикрепленный файл"
)
async def delete_attachment(
    registration_number: Annotated[str, Field(strict=True)],
    filename: str = Annotated[str, Field(strict=True)],
    current_user: User = Depends(
        get_current_user_with_role((UserRole.SECRETARY, UserRole.JUDGE))
    )
):
    if not (current_user.is_secretary or current_user.is_judge):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    await sql_delete_attachment(
        registration_number=registration_number,
        filename=filename,
        user=current_user
    )

    return {"status": "success"}