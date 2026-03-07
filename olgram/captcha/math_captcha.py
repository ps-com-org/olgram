"""
Математическая капча: задача вида "a + b = ?", проверка ответа,
ограничение времени и числа попыток, временный бан при превышении.
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

from aiogram import types

from olgram.captcha.base import BaseCaptcha, CaptchaState
from olgram.utils.i18n import get_translator

if TYPE_CHECKING:
    import redis.asyncio as redis

# Время на решение (секунды)
TIME_TO_SOLVE_SEC = 300
# Максимум неверных попыток до временного бана
MAX_ATTEMPTS = 5
# Длительность временного бана (секунды)
BAN_DURATION_SEC = 900  # 15 минут


class MathCaptcha(BaseCaptcha):
    """Математическая капча: сложение двух чисел."""

    def create_task(self, message: types.Message) -> tuple[str, str]:
        """Сгенерировать задачу и готовое сообщение. Возвращает (текст_сообщения, ответ)."""
        a = random.randint(1, 30)
        b = random.randint(1, 30)
        task_text = f"{a} + {b} = ?"
        _ = get_translator(message)
        text = (
            _("Решите задачу: ") + task_text + "\n\n"
            + _("Введите ответ — только число, без дополнительных знаков.")
        )
        return text, str(a + b)

    def verify_answer(self, user_answer: str, state: CaptchaState) -> bool:
        """Проверить ответ пользователя по сохранённому verification_value."""
        return (user_answer or "").strip() == state.verification_value

    def time_to_solve_sec(self) -> int:
        return TIME_TO_SOLVE_SEC

    def max_attempts(self) -> int:
        return MAX_ATTEMPTS

    def ban_duration_sec(self) -> int:
        return BAN_DURATION_SEC
