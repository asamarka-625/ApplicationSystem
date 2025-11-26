# Внешние зависимости
from typing import List, Optional
import os
import uuid
import aiofiles
import magic
from fastapi import UploadFile
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.schemas import AttachmentsRequest
from web_app.src.core import config


# Извлекаем файлы из формы и сохраняем их
async def save_uploaded_files(attachments: Optional[List[UploadFile]]) -> Optional[List[AttachmentsRequest]]:
    files_info = []

    if not attachments:
        return None

    if len(attachments) > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You can upload no more than 5 files.")

    for attachment in attachments:
        try:
            if attachment.size == 0:
                continue

            content = await attachment.read()

            validate_file_safety(content, attachment.filename)
            file_extension = os.path.splitext(attachment.filename)[1]
            unique_filename = uuid.uuid4().hex
            file_path = f"{config.USER_DOCUMENTS}/{unique_filename}{file_extension}"

            # Сохраняем файл с помощью aiofiles
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)

            files_info.append(AttachmentsRequest(
                file_name=unique_filename,
                content_type=attachment.content_type,
                file_path=f"{config.USER_DOCUMENTS}/{unique_filename}{file_extension}",
                size=attachment.size
            ))

        except HTTPException:
            raise

        except Exception as err:
            delete_files(files_info)

            config.logger.error(f"Error saving file {attachment.filename}: {err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving file {attachment.filename}"
            )

    return files_info


# Удаляем файлы
def delete_files(file_paths: List[str]) -> None:
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass


# Проверяет файл на безопасность
def validate_file_safety(file_content: bytes, filename: str) -> str:
    # Проверяем расширение файла
    file_extension = os.path.splitext(filename)[1].lower()
    if file_extension not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Тип файла {file_extension} не поддерживается"
        )

    # Определяем MIME тип по содержимому (более надежно чем по расширению)
    try:
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_buffer(file_content)

    except:
        # Если не удалось определить MIME, используем расширение как fallback
        detected_mime = None

    if not detected_mime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Тип файла не поддерживается"
        )

    # Сопоставляем MIME тип с категорией
    file_category = None
    for category, mime_types in config.ALLOWED_MIME_TYPES.items():
        if detected_mime in mime_types:
            file_category = category
            break

    if not file_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Тип файла {detected_mime or 'неизвестный'} не поддерживается"
        )

    # Проверяем размер файла в соответствии с категорией
    max_size = config.MAX_FILE_SIZES.get(file_category, 5 * 1024 * 1024)
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл слишком большой. Максимальный размер для {file_category}: {max_size // 1024 // 1024}MB"
        )

    return file_extension
