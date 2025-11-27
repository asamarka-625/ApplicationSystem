FROM python:3.12.3-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*
	
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

RUN mkdir -p /app/logs

CMD ["sh", "-c", "mkdir -p /app/logs && uvicorn web_app:app --host 0.0.0.0 --port 8000"]