from weasyprint import HTML
from jinja2 import Template
from typing import Dict, Any


def generate_pdf(data: Dict[str, Any], filename: str):
    # Загружаем шаблон из файла
    template_path = "web_app/templates/pdf_template.html"
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Рендерим шаблон с помощью Jinja2
    template = Template(template_content)
    rendered_html = template.render(**data)

    # Создаем PDF из HTML
    file_path = f"{filename}.pdf"
    HTML(string=rendered_html, encoding='utf-8').write_pdf(file_path)


if __name__ == "__main__":
    data_pdf = {
        "date": "10.07.2025",
        "department_number": 1,
        "address": "190068, Санкт-Петербург, Адмиралтейский район, ул. Садовая, д. 55/57, лит. А, пом. 12-Н, 14-Н",
        "items": [
            ("корками ДЕЛО (Форма №18)", 20),
            ("офисное кресло (для канцелярии)", 1)
        ],
        "fio_secretary": "Хмелев Александр Викторович",
        "fio_judge": "Кочеткова Елена Альбертовна",
        "certificate": "432424235dfgrfh4543",
        "owner": "Кочеткова Елена Альбертовна",
        "date_from": "04.06.2025",
        "date_until": "01.01.2027",
        "siganture": False
    }

    generate_pdf(data=data_pdf, filename="test")