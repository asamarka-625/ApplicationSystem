# Внешние зависимости
from typing import Optional
from io import BytesIO
from datetime import datetime
import pandas as pd
from fastapi import APIRouter, Depends, Response, HTTPException
from fastapi import status as status_
# Внутренние модули
from web_app.src.dependencies import get_current_user
from web_app.src.models import User, UserRole
from web_app.src.crud import sql_get_requests_for_download, sql_get_planning_for_download


router = APIRouter(
    prefix="/api/v1",
    tags=["API"],
)


@router.get(
    path="/download/requests",
    response_class=Response,
    summary="Скачивание заявок в xlsx"
)
async def download_requests(
        status: int,
        request_type: Optional[int] = None,
        department: Optional[int] = None,
        date_filter_from: Optional[datetime] = None,
        date_filter_until: Optional[datetime] = None,
        current_user: User = Depends(get_current_user)
):
    if current_user.role not in (UserRole.MANAGEMENT, UserRole.MANAGEMENT_DEPARTMENT):
        raise HTTPException(status_code=status_.HTTP_403_FORBIDDEN, detail="Not enough rights")

    # Получаем данные
    requests = await sql_get_requests_for_download(
        status_filter_id=status,
        type_filter_id=request_type,
        department_filter_id=department,
        date_filter_from=date_filter_from,
        date_filter_until=date_filter_until
    )

    # Создаем DataFrame
    df = pd.DataFrame(requests)

    # Создаем Excel файл в памяти
    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Заявки', index=False)

    output.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"requests_{timestamp}.xlsx"

    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    path="/download/planning",
    response_class=Response,
    summary="Скачивание заявок из планирования в xlsx"
)
async def download_planning(
        department: Optional[int] = None,
        current_user: User = Depends(get_current_user)
):
    if current_user.role not in (UserRole.MANAGEMENT, UserRole.MANAGEMENT_DEPARTMENT):
        raise HTTPException(status_code=status_.HTTP_403_FORBIDDEN, detail="Not enough rights")

    # Получаем данные
    requests = await sql_get_planning_for_download(
        department_filter_id=department
    )

    # Создаем DataFrame
    df = pd.DataFrame(requests)

    # Создаем Excel файл в памяти
    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Планирование', index=False)

    output.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"planning_{timestamp}.xlsx"

    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )