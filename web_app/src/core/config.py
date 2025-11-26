# Внешние зависимости
from typing import Dict, List, Set
from dataclasses import dataclass, field
from dotenv import load_dotenv
import os
import logging
# Внутренние модули
from web_app.src.core.logger import setup_logger


load_dotenv()


@dataclass
class Config:
    _database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL"))
    _redis_url: str = field(default_factory=lambda : os.getenv("REDIS_URL"))
    logger: logging.Logger = field(init=False)
    SECRET_KEY: str = field(default_factory=lambda: os.getenv("SECRET_KEY"))
    ALGORITHM: str = field(default_factory=lambda: os.getenv("ALGORITHM"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = field(default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))

    ADMIN_LOGIN: str = field(default_factory=lambda: os.getenv("ADMIN_LOGIN"))
    ADMIN_PASSWORD: str = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD"))

    SMTP_HOST: str = field(default_factory=lambda: os.getenv("SMTP_HOST"))
    SMTP_PORT: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT")))
    SMTP_USERNAME: str = field(default_factory=lambda: os.getenv("SMTP_USERNAME"))
    SMTP_PASSWORD: str = field(default_factory=lambda: os.getenv("SMTP_PASSWORD"))
    EMAIL_FROM: str = field(default_factory=lambda: os.getenv("EMAIL_FROM"))
    FRONTEND_URL: str = field(default_factory=lambda: os.getenv("FRONTEND_URL"))
    APP_NAME: str = field(default_factory=lambda: os.getenv("APP_NAME"))

    MAINTENANCE_ITEM_ID: int = field(default_factory=lambda: os.getenv("MAINTENANCE_ITEM_ID"))
    USER_DOCUMENTS: str = "web_app/src/static/user_documents"
    PDF_REQUESTS: str = "web_app/src/static/pdf_requests"
    FONT_PATH: str = "web_app/src/static/fonts/arial.ttf"

    ALLOWED_MIME_TYPES: Dict[str, List[str]] = field(default_factory=lambda: {
        'image': [
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/bmp',
            'image/webp'
        ],
        'video': [
            'video/mp4',
            'video/avi',
            'video/mov',
            'video/webm'
        ]
    })

    # Разрешенные расширения файлов (дополнительная проверка)
    ALLOWED_EXTENSIONS: Set[str] = field(default_factory=lambda: {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
        '.mp4', '.avi', '.mov', '.webm'
    })

    # Максимальные размеры для разных типов файлов (в байтах)
    MAX_FILE_SIZES: Dict[str, int] = field(default_factory=lambda: {
        'image': 5 * 1024 * 1024,  # 5MB
        'video': 50 * 1024 * 1024,  # 50MB
    })
    
    def __post_init__(self):
        self.logger = setup_logger(
            level=os.getenv("LOG_LEVEL", "INFO"),
            log_dir=os.getenv("LOG_DIR", "logs"),
            log_file=os.getenv("LOG_FILE", "web_log")
        )

        self.validate()
        self.logger.info("Configuration initialized")

        self.active_session_tokens = dict()
        self.blacklisted_tokens = set()

    # Валидация конфигурации
    def validate(self):
        if not self._database_url:
            self.logger.critical("DATABASE_URL is required in environment variables")
            raise ValueError("DATABASE_URL is required")

        self.logger.debug("Configuration validation passed")

    @property
    def DATABASE_URL(self) -> str:
        return self._database_url

    @property
    def REDIS_URL(self) -> str:
        return self._redis_url

    def __str__(self) -> str:
        return f"Config(database={self._database_url}, log_level={self.logger.level})"


_instance = None


def get_config() -> Config:
    global _instance
    if _instance is None:
        _instance = Config()

    return _instance