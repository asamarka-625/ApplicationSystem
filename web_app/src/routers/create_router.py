# Внешние зависимости
from typing import Annotated, Optional, List
import json
from fastapi import APIRouter, Depends, Form, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi import HTTPException, status
from pydantic import Field
# Внутренние модули
from web_app.src.crud import (sql_search_items, sql_create_request, sql_get_executors, sql_get_management_departments,
                              sql_get_executor_organizations)
from web_app.src.models import TYPE_ID_MAPPING, User, UserRole
from web_app.src.schemas import CreateRequest, ItemsRequest
from web_app.src.dependencies import get_current_user, get_current_user_with_role
from web_app.src.utils import save_uploaded_files, delete_files
from web_app.src.core import config


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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    return {
        "request_type": TYPE_ID_MAPPING
    }    
    
@router.get(
    path="/item",
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    items = await sql_search_items(search=search)

    return items


@router.get(
    path="/managements",
    response_class=JSONResponse,
    summary="Вывод сотрудников управления отдела"
)
async def get_management_departments(
        current_user: User = Depends(get_current_user)
):
    if not current_user.is_management:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    management_departments = await sql_get_management_departments()

    return management_departments


@router.get(
    path="/executors",
    response_class=JSONResponse,
    summary="Вывод исполнителей"
)
async def get_executors(
        current_user: User = Depends(
            get_current_user_with_role((UserRole.MANAGEMENT_DEPARTMENT,))
        )
):
    if not (current_user.is_management or current_user.is_management_department):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    executors = await sql_get_executors(
        management_department_profile=current_user.management_department_profile
    )

    return executors


@router.get(
    path="/organizations",
    response_class=JSONResponse,
    summary="Вывод организаций-исполнителей"
)
async def get_organizations(
        current_user: User = Depends(get_current_user)
):
    if not (current_user.is_management or current_user.is_management_department or
            current_user.is_executor):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    organizations = await sql_get_executor_organizations()

    return organizations


@router.post(
    path="/",
    response_class=JSONResponse,
    summary="Создание новой заявки"
)
async def create_request(
    items: str = Form(None),
    is_emergency: bool = Form(False),
    description: str = Form(...),
    request_type: int = Form(...),
    attachments: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(
        get_current_user_with_role((UserRole.SECRETARY,))
    )
):
    if not current_user.is_secretary:
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

    files_info = await save_uploaded_files(attachments)
    request_data.attachments = files_info

    try:
        request_id = await sql_create_request(
            data=request_data,
            user_id=current_user.id,
            secretary_id=current_user.secretary_profile.id,
            judge_id=current_user.secretary_profile.judge_id,
            department_id=current_user.secretary_profile.department_id,
            fio_secretary=current_user.full_name
        )

    except:
        delete_files(file_paths=[file.file_path for file in files_info])
        raise

    return {"status": "success", "registration_number": request_id}