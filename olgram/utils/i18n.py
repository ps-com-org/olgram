"""
Общие утилиты локализации: получить функцию перевода по контексту (например, сообщению).
"""
from typing import Callable

from aiogram import types

from locales.locale import _, translators


def get_translator(message: types.Message) -> Callable[[str], str]:
    """
    Вернуть функцию перевода для языка пользователя из сообщения.
    Использует message.from_user.locale; при отсутствии или ошибке — дефолтный _.
    """
    try:
        if not message.from_user.locale:
            return _
        return translators.get(message.from_user.locale.language, _)
    except Exception:
        return _
