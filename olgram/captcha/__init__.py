"""
Модуль капчи: фабрика синглтонов по типу и единая точка входа require_check.
Redis передаётся в конструкторы реализаций.
"""
from aiogram import types

from olgram.captcha.base import BaseCaptcha
from olgram.captcha.disabled_captcha import DisabledCaptcha
from olgram.captcha.math_captcha import MathCaptcha
from olgram.models.models import Bot, CaptchaType
from olgram.redis_client import get_redis

_math_instance: BaseCaptcha | None = None
_disabled_instance: BaseCaptcha | None = None


def get_captcha(captcha_type: CaptchaType):
    """Фабрика синглтонов: по типу капчи возвращает один и тот же экземпляр. Redis берётся из get_redis()."""
    global _math_instance, _disabled_instance
    redis = get_redis()
    if captcha_type == CaptchaType.math:
        if _math_instance is None:
            _math_instance = MathCaptcha(redis)
        return _math_instance
    else:
        if _disabled_instance is None:
            _disabled_instance = DisabledCaptcha(redis)
        return _disabled_instance


async def require_check(
    message: types.Message,
    bot: Bot,
) -> bool:
    """
    Проверить/обработать капчу для сообщения.
    Redis и переводчик берутся из общих модулей.

    :return: True — капча обработала сообщение, не вызывать handle_user_message.
             False — продолжить, вызвать handle_user_message.
    """
    impl = get_captcha(bot.captcha_type)
    return await impl.require_check(message, bot)
