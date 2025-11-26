# Внешние зависимости
from typing import Dict, Any
from datetime import datetime
from io import BytesIO
import os
import magic
import aiofiles
from jinja2 import Template
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from PyPDF2 import PdfReader, PdfWriter
from fastapi import HTTPException, status, UploadFile
# Внутренние модули
from web_app.src.core import config
from web_app.src.schemas import DocumentResponse, DucumentEmblem


pdfmetrics.registerFont(TTFont('CustomFont', config.FONT_PATH))


# Генерирует PDF с данными по предметам заявки
def generate_pdf(data: Dict[str, Any], filename: str) -> DocumentResponse:
    # Загружаем шаблон из файла
    template_path = "web_app/templates/pdf_template.html"
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Создаем документ
    file_path = f"{config.PDF_REQUESTS}/not_signed/{filename}.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    story = []

    # Рендерим шаблон
    template = Template(template_content)
    rendered_content = template.render(
        data=data,
        current_date=datetime.now().strftime('%d.%m.%Y %H:%M')
    )

    # Стиль для всего контента
    content_style = ParagraphStyle(
        'ContentStyle',
        fontName='CustomFont',
        fontSize=10,
        leading=14,
        leftIndent=0,
        rightIndent=0,
        firstLineIndent=0
    )

    story.append(Paragraph(rendered_content, content_style))
    doc.build(story)

    return DocumentResponse(
        file_url=file_path.replace("web_app/src", "")
    )


# Создает слой с эмблемой ЭЦП по центру внизу
def create_signature_layer(signature_data: DucumentEmblem, page_size=A4):
    buffer = BytesIO()

    # Создаем canvas для подписи
    c = canvas.Canvas(buffer, pagesize=page_size)
    width, height = page_size

    # Вычисляем координаты для центрирования эмблемы внизу
    logo_width = 80
    logo_height = 80
    logo_y = 30  # Отступ от нижнего края

    # Добавляем блок ЭЦП по центру над эмблемой
    signature_width = 200
    signature_x = (width - signature_width) / 2
    signature_y = logo_y + logo_height + 20  # Над эмблемой

    # Заголовок ЭЦП
    c.setFont("CustomFont", 10)
    c.drawString(signature_x, signature_y + 40, "ЭЛЕКТРОННАЯ ЦИФРОВАЯ ПОДПИСЬ")

    # Информация о подписи
    c.setFont("CustomFont", 9)
    y_position = signature_y + 25

    signature_info = [
        f"Подписано: {signature_data.owner}",
        f"Издатель: {signature_data.publisher}",
        f"Отпечаток: {signature_data.Thumbprint}",
        f"Срок действия от: {signature_data.valid_from.strftime('%d-%m-%Y')}",
        f"Срок действия до: {signature_data.valid_until.strftime('%d-%m-%Y')}"
    ]

    for info in signature_info:
        c.drawString(signature_x, y_position, info)
        y_position -= 15

    # Добавляем разделительную линию над подписью
    c.line(signature_x - 10, signature_y + 50, signature_x + signature_width + 10, signature_y + 50)

    c.save()
    buffer.seek(0)
    return buffer


# Добавляет подпись и эмблему в существующий PDF
def generate_pdf_with_emblem(filename: str, signature_data: DucumentEmblem) -> DocumentResponse:
    # Читаем исходный PDF
    input_pdf_path = f"{config.PDF_REQUESTS}/not_signed/{filename}.pdf"
    output_pdf_path = f"{config.PDF_REQUESTS}/temp/{filename}.pdf"

    # Создаем слой с подписью
    signature_layer = create_signature_layer(signature_data)
    signature_reader = PdfReader(signature_layer)

    with open(input_pdf_path, 'rb') as f:
        pdf_data = f.read()

    pdf_reader = PdfReader(BytesIO(pdf_data))

    # Создаем writer для результата
    writer = PdfWriter()

    # Для каждой страницы добавляем подпись
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]

        # Если это последняя страница, добавляем подпись
        if page_num == len(pdf_reader.pages) - 1:
            signature_page = signature_reader.pages[0]
            page.merge_page(signature_page)

        writer.add_page(page)

    # Сохраняем результат
    with open(output_pdf_path, 'wb') as f:
        writer.write(f)

    return DocumentResponse(
        file_url=output_pdf_path.replace("web_app/src", "")
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
