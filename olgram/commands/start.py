"""
Здесь простые команды на первом уровне вложенности: /start /help
"""

from aiogram import types, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from textwrap import dedent
from olgram.settings import OlgramSettings
from olgram.utils.permissions import public
from locales.locale import _

from olgram.router import router


@router.message(Command("start"), StateFilter("*"))
@public()
async def start(message: types.Message, state: FSMContext):
    """
    Команда /start
    """
    await state.clear()

    await message.answer(dedent(_("""
    Olgram Bot — это конструктор ботов обратной связи в Telegram. Подробнее \
<a href="https://olgram.readthedocs.io">читайте здесь</a>. Следите за обновлениями \
<a href="https://t.me/civsoc_it">здесь</a>.

    Используйте эти команды, чтобы управлять этим ботом:

    /addbot - добавить бот
    /mybots - управление ботами

    /help - помощь
    """)), parse_mode="html", link_preview_options={"is_disabled": True})


@router.message(Command("help"), StateFilter("*"))
@public()
async def help(message: types.Message, state: FSMContext):
    """
    Команда /help
    """
    await message.answer(dedent(_("""
    Читайте инструкции на нашем сайте https://olgram.readthedocs.io
    Техническая поддержка: @civsocit_feedback_bot
    Версия {0}
    """)).format(OlgramSettings.version()))


@router.message(Command("chatid"), StateFilter("*"))
@public()
async def chat_id(message: types.Message, state: FSMContext):
    """
    Команда /chatid
    """
    await message.answer(str(message.chat.id))
