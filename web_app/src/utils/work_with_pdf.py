# Внешние зависимости
import os
import magic
import aiofiles
from jinja2 import Template
from weasyprint import HTML
from fastapi import HTTPException, status, UploadFile
# Внутренние модули
from web_app.src.core import config
from web_app.src.schemas import DocumentResponse, DocumentData


# Генерирует PDF с данными по предметам заявки
def generate_pdf(data: DocumentData, filename: str) -> DocumentResponse:
    # Загружаем шаблон из файла
    template_path = "web_app/templates/pdf_template.html"
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    data_dict = data.model_dump()

    if data.signature is None:
        file_path = f"{config.PDF_REQUESTS}/not_signed/{filename}.pdf"

    else:
        file_path = f"{config.PDF_REQUESTS}/temp/{filename}.pdf"
        data_dict["valid_from"] = data_dict["valid_from"].strftime("%d.%m.%Y")
        data_dict["valid_until"] = data_dict["valid_until"].strftime("%d.%m.%Y")

    # Рендерим шаблон с помощью Jinja2
    template = Template(template_content)
    rendered_html = template.render(**data_dict)

    # Создаем PDF из HTML
    HTML(string=rendered_html, encoding='utf-8').write_pdf(file_path)

    return DocumentResponse(
        file_url=file_path.replace("web_app/src", "")
    )


# Проверяет файл на pdf формат
def validate_pdf_file(file_content: bytes, filename: str) -> None:
    # Проверяем расширение файла
    file_extension = os.path.splitext(filename)[1].lower()

    if file_extension != ".pdf":
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

    if detected_mime != "application/octet-stream":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Тип файла не поддерживается"
        )

    # Проверяем размер файла в соответствии с категорией
    max_size = 5 * 1024 * 1024
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл слишком большой. Максимальный размер: {max_size // 1024 // 1024}MB"
        )


# Сохраняет pdf файл с подписью и удаляет pdf файл из temp
async def save_pdf_signed(file: UploadFile, filename: str) -> DocumentResponse:
    content = await file.read()

    validate_pdf_file(content, file.filename)
    temp_file_path = f"{config.PDF_REQUESTS}/temp/{filename}.pdf"
    file_path = f"{config.PDF_REQUESTS}/signed/{filename}.pdf"

    # Сохраняем файл с помощью aiofiles
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)

    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)

    return DocumentResponse(
        file_url=file_path.replace("web_app/src", "")
    )
