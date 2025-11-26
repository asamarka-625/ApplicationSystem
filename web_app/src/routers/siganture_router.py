# Внешние зависимости
from typing import Annotated
from pydantic import Field
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
# Внутренние модули
from web_app.src.models import User, UserRole
from web_app.src.dependencies import get_current_user_with_role
from web_app.src.schemas import DocumentResponse, DucumentEmblem
from web_app.src.crud import sql_check_request_by_judge, sql_approve_request
from web_app.src.utils import generate_pdf_with_emblem, save_pdf_signed


router = APIRouter(
    prefix="/api/v1/signature",
    tags=["API"],
)


@router.post(
    path="/generate-pdf/emblem/{registration_number}",
    response_model=DocumentResponse,
    summary="Генерация pdf файла с эмблемой подписи"
)
async def generate_pdf_with_emblem_request(
        registration_number: Annotated[str, Field(strict=True)],
        data: DucumentEmblem,
        current_user: User = Depends(get_current_user_with_role((UserRole.JUDGE, )))
):
    if not current_user.is_judge:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    flag = await sql_check_request_by_judge(
        judge_id=current_user.judge_profile.id,
        registration_number=registration_number
    )

    if not flag:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    document_info = generate_pdf_with_emblem(filename=registration_number, signature_data=data)

    return document_info


@router.post(
    path="/load-pdf/signed/{registration_number}",
    response_model=DocumentResponse,
    summary="Загрузка pdf файла с подписью и утверждение заявки"
)
async def load_pdf_signed_request(
        registration_number: Annotated[str, Field(strict=True)],
        file: UploadFile,
        current_user: User = Depends(get_current_user_with_role((UserRole.JUDGE,)))
):
    if not current_user.is_judge:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    flag = await sql_check_request_by_judge(
        judge_id=current_user.judge_profile.id,
        registration_number=registration_number
    )

    if not flag:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

    document_info = await save_pdf_signed(file=file, filename=registration_number)

    await sql_approve_request(
        registration_number=registration_number,
        user_id=current_user.id,
        judge_id=current_user.judge_profile.id,
        signed_pdf_url=document_info.file_url
    )

    return document_info