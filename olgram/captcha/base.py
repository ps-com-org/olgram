"""
Базовый класс для проверки капчи.
Общая логика: чтение записи из Redis, проверка banned_until, сравнение тега.
Модель хранения состояния — класс CaptchaState.
Redis передаётся в конструктор.
"""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from aiogram import types

from olgram.settings import ServerSettings
from olgram.utils.i18n import get_translator

if TYPE_CHECKING:
    import redis.asyncio as redis
    from olgram.models.models import Bot


class CaptchaStatus(str, Enum):
    """Статус прохождения капчи."""

    PENDING = "pending"
    PASSED = "passed"
    BANNED = "banned"


@dataclass
class CaptchaState:
    """
    Модель состояния капчи в Redis.
    Сериализуется в JSON при записи и восстанавливается при чтении.
    """
    status: CaptchaStatus = CaptchaStatus.PENDING
    tag: str = ""
    verification_value: str = ""
    started_at: int = 0
    expires_at: int = 0
    attempts: int = 0
    banned_until: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        """Словарь для сериализации в JSON (без None-полей, чтобы не раздувать запись)."""
        d = asdict(self)
        d["status"] = self.status.value
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> Optional["CaptchaState"]:
        """Восстановить из словаря (например, из JSON Redis). None если data пустой или невалидный."""
        if not data or not isinstance(data, dict):
            return None
        try:
            raw_status = str(data.get("status", CaptchaStatus.PENDING.value))
            try:
                status = CaptchaStatus(raw_status)
            except ValueError:
                status = CaptchaStatus.PENDING
            return cls(
                status=status,
                tag=str(data.get("tag", "")),
                verification_value=str(data.get("verification_value", "")),
                started_at=int(data.get("started_at", 0)),
                expires_at=int(data.get("expires_at", 0)),
                attempts=int(data.get("attempts", 0)),
                banned_until=cls._read_banned_until(data.get("banned_until")),
            )
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _read_banned_until(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class BaseCaptcha(ABC):
    """Абстрактный базовый класс капчи. Redis передаётся в конструктор."""

    def __init__(self, redis: Optional["redis.Redis"]) -> None:
        self._redis = redis

    def _captcha_key(self, bot_id: int, chat_id: int, tag: str) -> str:
        """Ключ Redis для состояния капчи: bot.pk, chat.id, captcha_tag."""
        return f"captcha_{bot_id}_{chat_id}_{tag or ''}"

    async def _get_record(self, key: str) -> Optional[CaptchaState]:
        """Прочитать запись капчи из Redis. Возвращает None если ключа нет или не JSON."""
        if self._redis is None:
            return None
        raw = await self._redis.get(key)
        if not raw:
            return None
        try:
            data = json.loads(raw)
            return CaptchaState.from_dict(data)
        except (json.JSONDecodeError, TypeError):
            return None

    def _is_banned(self, state: Optional[CaptchaState]) -> bool:
        """Проверка: действует ли временный бан (banned_until в записи)."""
        if not state or state.banned_until is None:
            return False
        return time.time() < state.banned_until

    def _tag_matches(self, state: Optional[CaptchaState], current_tag: str) -> bool:
        """Проверка: совпадает ли тег в записи с текущим тегом бота."""
        if not state:
            return False
        current = (current_tag or "").strip()
        return state.tag == current

    def _should_create_task(
        self,
        record: Optional[CaptchaState],
        tag: str,
    ) -> bool:
        """
        Нужно ли выдать новую задачу: нет записи, тег не совпадает
        или статус banned и время бана вышло.
        """
        if not record or not self._tag_matches(record, tag):
            return True
        return (
            record.status == CaptchaStatus.BANNED
            and not self._is_banned(record)
        )

    async def _save_state(self, key: str, state: CaptchaState) -> None:
        """Сохранить состояние в Redis (JSON + TTL). Переопределить при другой стратегии TTL."""
        if self._redis is None:
            return
        payload = json.dumps(state.to_dict())
        px = ServerSettings.redis_timeout_ms()
        if px:
            await self._redis.set(key, payload, px=px)
        else:
            await self._redis.set(key, payload)

    # --- Абстрактные методы для реализации типа капчи ---

    @abstractmethod
    def create_task(self) -> tuple[str, str]:
        """Создать задачу. Возвращает (текст_задачи, правильный_ответ)."""
        pass

    @abstractmethod
    def verify_answer(self, user_answer: str, state: CaptchaState) -> bool:
        """Проверить ответ пользователя. Возвращает True, если ответ верный."""
        pass

    @abstractmethod
    def time_to_solve_sec(self) -> int:
        """Время на решение задачи (секунды)."""
        pass

    @abstractmethod
    def max_attempts(self) -> int:
        """Максимум неверных попыток до временного бана."""
        pass

    @abstractmethod
    def ban_duration_sec(self) -> int:
        """Длительность временного бана (секунды)."""
        pass

    async def _check_banned_and_respond(
        self,
        message: types.Message,
        bot: "Bot",
    ) -> bool:
        """
        Если в записи капчи установлен banned_until и бан действует —
        отправить сообщение и вернуть True. Иначе False.
        """
        _ = get_translator(message)
        tag = (bot.captcha_tag or "").strip()
        key = self._captcha_key(bot.pk, message.chat.id, tag)
        record = await self._get_record(key)
        if not self._is_banned(record):
            return False
        await message.answer(
            text=_(
                "Вы временно заблокированы за неудачные попытки ввода капчи. Попробуйте позже.",
            ),
        )
        return True

    async def require_check(
        self,
        message: types.Message,
        bot: "Bot",
    ) -> bool:
        """
        Проверить/обработать капчу для сообщения: бан, валидность записи, тег,
        создание задачи или проверка ответа. Вся логика в базовом классе.
        :return: True — капча обработала сообщение (показала задачу, ответ, бан), выйти.
                 False — проверка не нужна или пройдена, продолжать handle_user_message.
        """
        _ = get_translator(message)
        if await self._check_banned_and_respond(message, bot):
            return True

        tag = (bot.captcha_tag or "").strip()
        key = self._captcha_key(bot.pk, message.chat.id, tag)
        record = await self._get_record(key)

        # Запись есть, тег совпадает, статус passed — пропускаем
        if record and self._tag_matches(record, tag) and record.status == CaptchaStatus.PASSED:
            return False

        # Нужна новая задача: нет записи / не совпадает тег / бан закончился
        if self._should_create_task(record, tag):
            task_text, answer = self.create_task()
            now = int(time.time())
            state = CaptchaState(
                status=CaptchaStatus.PENDING,
                tag=tag,
                verification_value=answer,
                started_at=record.started_at if record else now,
                expires_at=now + self.time_to_solve_sec(),
                attempts=0,
            )
            await self._save_state(key, state)
            await message.answer(
                text=_("Решите задачу: ") + task_text,
            )
            return True

        # Ожидаем ответ (pending)
        if record.status != CaptchaStatus.PENDING:
            return False

        # Просрочено
        if record.expires_at and time.time() > float(record.expires_at):
            await message.answer(
                text=_("Время на решение вышло. Напишите что угодно для новой задачи."),
            )
            if self._redis is not None:
                await self._redis.delete(key)
            return True

        user_answer = (message.text or "").strip()
        if self.verify_answer(user_answer, record):
            record.status = CaptchaStatus.PASSED
            await self._save_state(key, record)
            await message.answer(
                text=_("Верно! Отправьте ваше сообщение ещё раз, пожалуйста."),
            )
            return True

        # Неверный ответ
        record.attempts += 1
        if record.attempts >= self.max_attempts():
            record.status = CaptchaStatus.BANNED
            record.banned_until = time.time() + self.ban_duration_sec()
            await self._save_state(key, record)
            await message.answer(
                text=_(
                    "Вы временно заблокированы за неудачные попытки ввода капчи. Попробуйте позже.",
                ),
            )
            return True

        await self._save_state(key, record)
        await message.answer(text=_("Неверно. Попробуйте ещё раз."))
        return True
