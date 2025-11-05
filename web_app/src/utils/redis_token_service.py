# Внешние зависимости
import redis.asyncio as redis
from typing import Optional
# Внутренние модули
from web_app.src.core import config


class TokenService:
    def __init__(self):
        self.redis_url = config.REDIS_URL
        self.redis: Optional[redis.Redis] = None
        self.blacklist_prefix = "blacklist:"
        self.session_prefix = "access_token:"

    async def init_redis(self):
        """Инициализация подключения к Redis"""
        config.logger.info("Инициализируем соединение Redis")

        if not self.redis:
            self.redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

    async def close_redis(self):
        """Закрытие подключения к Redis"""
        config.logger.info("Закрываем соединение Redis")

        if self.redis:
            await self.redis.close()

    async def add_to_blacklist(self, token: str, expire_seconds: int = 86400):
        """Добавление токена в черный список с удалением из активных сессий"""
        # Находим все сессии с этим токеном (независимо от user_id)
        pattern = f"{self.session_prefix}*:{token}"
        session_keys = await self.redis.keys(pattern)

        # Создаем пайплайн для атомарного выполнения
        async with self.redis.pipeline(transaction=True) as pipe:
            # 1. Добавляем токен в черный список
            blacklist_key = f"{self.blacklist_prefix}{token}"
            pipe.setex(blacklist_key, expire_seconds, "1")

            # 2. Удаляем все сессии с этим токеном
            if session_keys:
                pipe.delete(*session_keys)

            # Выполняем атомарно
            await pipe.execute()

    async def is_blacklisted(self, token: str) -> bool:
        """Проверка, находится ли токен в черном списке"""
        key = f"{self.blacklist_prefix}{token}"
        exists = await self.redis.exists(key)
        return bool(exists)

    async def store_session(self, token: str, user_id: int):
        """Сохранение сессии в Redis"""
        key = f"{self.session_prefix}{user_id}:{token}"
        await self.redis.setex(
            key,
            config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "1"
        )

    async def clear_session(self, user_id: int, expire_seconds: int = 86400):
        """Атомарно добавляем активные сессии в черный список и удаляем их"""
        # Находим все активные сессии пользователя
        pattern = f"{self.session_prefix}{user_id}:*"
        session_keys = await self.redis.keys(pattern)

        if not session_keys:
            return

        # Извлекаем токены из ключей сессий
        tokens_to_blacklist = []
        for session_key in session_keys:
            # Формат ключа: "access_token:{user_id}:{token}"
            token = session_key.split(":")[-1]
            tokens_to_blacklist.append(token)

        # Создаем пайплайн для атомарного выполнения операций
        async with self.redis.pipeline(transaction=True) as pipe:
            # 1. Добавляем все токены в черный список
            for token in tokens_to_blacklist:
                blacklist_key = f"{self.blacklist_prefix}{token}"
                pipe.setex(blacklist_key, expire_seconds, "1")

            # 2. Удаляем все сессии пользователя
            pipe.delete(*session_keys)

            # Выполняем атомарно
            await pipe.execute()

    async def get_stats(self) -> dict:
        """Статистика аутентификаций"""
        blacklist_keys = await self.redis.keys(f"{self.blacklist_prefix}*")
        session_keys = await self.redis.keys(f"{self.session_prefix}*")

        return {
            "total_blacklisted": len(blacklist_keys),
            "total_active_sessions": len(session_keys),
            "memory_usage": await self.redis.info('memory')
        }


_instance = None


def get_token_service() -> TokenService:
    global _instance
    if _instance is None:
        _instance = TokenService()

    return _instance