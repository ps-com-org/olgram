"""Капча выключена — всегда пропускать."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from aiogram import types

from olgram.captcha.base import BaseCaptcha, CaptchaState

if TYPE_CHECKING:
    from olgram.models.models import Bot


class DisabledCaptcha(BaseCaptcha):
    """Реализация «капча выключена»: переопределяет всё поведение require_check — всегда пропускать."""

    async def require_check(
        self,
        message: types.Message,
        bot: "Bot",
    ) -> bool:
        return False

    def create_task(self, message: types.Message) -> tuple[str, str]:
        raise NotImplementedError("Капча отключена")

    def verify_answer(self, user_answer: str, state: CaptchaState) -> bool:
        return False

    def time_to_solve_sec(self) -> int:
        return 0

    def max_attempts(self) -> int:
        return 0

    def ban_duration_sec(self) -> int:
        return 0
