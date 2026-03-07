import aiogram.types as types
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from collections.abc import Awaitable, Callable
import typing as ty
from locales.locale import _


def public():
    """
    Хендлеры с этим декоратором будут обрабатываться даже если пользователь не является владельцем бота
    (например, команда /help)
    :return:
    """

    def decorator(func):
        setattr(func, "access_public", True)
        return func

    return decorator


class AccessMiddleware(BaseMiddleware):
    def __init__(self, access_chat_ids: ty.Iterable[int]):
        self._access_chat_ids = access_chat_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, ty.Any]], Awaitable[ty.Any]],
        event: TelegramObject,
        data: dict[str, ty.Any]
    ) -> ty.Any:
        # Проверяем, является ли хэндлер публичным
        handler_func = data.get("handler")
        is_public = handler_func and getattr(handler_func.callback, "access_public", False)

        admin_ids = self._access_chat_ids
        if not admin_ids:
            return await handler(event, data)  # Администраторы бота вообще не указаны

        if is_public:  # Эта команда разрешена всем пользователям
            return await handler(event, data)

        # Определяем chat_id в зависимости от типа события
        chat_id = None
        if isinstance(event, types.Message):
            chat_id = event.chat.id
        elif isinstance(event, types.CallbackQuery) and event.message:
            chat_id = event.message.chat.id

        if chat_id and chat_id not in admin_ids:
            if isinstance(event, types.Message):
                await event.answer(_("Владелец бота ограничил доступ к этому функционалу 😞"))
            elif isinstance(event, types.CallbackQuery):
                await event.answer(_("Владелец бота ограничил доступ к этому функционалу😞"))
            return

        return await handler(event, data)
