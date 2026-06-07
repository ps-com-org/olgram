"""
Общий клиент Redis для модулей olgram.
Инициализация при старте приложения, использование через get_redis().
"""
import logging
from typing import Optional

import redis.asyncio as redis

from olgram.settings import ServerSettings

_logger = logging.getLogger(__name__)

_redis: Optional[redis.Redis] = None


async def init_redis() -> None:
    """Подключиться к Redis и сохранить клиент. При ошибке сбрасывает клиент и пробрасывает исключение."""
    global _redis
    try:
        redis_url = ServerSettings.redis_path()
        _logger.info("Подключение к Redis: %s", redis_url)
        _redis = await redis.from_url(redis_url)
        await _redis.ping()
        _logger.info("Успешное подключение к Redis")
    except Exception as e:
        _logger.error("Ошибка подключения к Redis: %s", e, exc_info=True)
        _redis = None
        raise


def get_redis() -> Optional[redis.Redis]:
    """Получить глобальный клиент Redis."""
    return _redis
