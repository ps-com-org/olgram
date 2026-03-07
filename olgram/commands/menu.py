import logging
from io import BytesIO
from olgram.router import dp
from datetime import datetime, timedelta, timezone
from aiogram import types, Bot as AioBot
from olgram.models.models import Bot, User, DefaultAnswer, BotStartMessage, BotSecondMessage, CaptchaType
from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData
from textwrap import dedent
from olgram.utils.mix import edit_or_create, button_text_limit, wrap, send_stored_message
from olgram.commands import bot_actions
from locales.locale import _

import typing as ty


menu_callback = CallbackData("menu", "level", "bot_id", "operation", "chat")

empty = "0"


async def send_bots_menu(chat_id: int, user_id: int, call=None):
    """
    Отправить пользователю список ботов
    :return:
    """
    if call:
        await call.answer()

    user = await User.get_or_none(telegram_id=user_id)
    bots = await Bot.filter(owner=user)
    if not bots:
        await AioBot.get_current().send_message(
            chat_id,
            dedent(
                _("""
        У вас нет добавленных ботов.

        Отправьте команду /addbot, чтобы добавить бот.
        """)
            ),
        )
        return

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for bot in bots:
        keyboard.insert(
            types.InlineKeyboardButton(
                text="@" + bot.name, callback_data=menu_callback.new(level=1, bot_id=bot.id, operation=empty, chat=empty)
            )
        )

    text = _("Ваши боты")
    if call:
        await edit_or_create(call, text, keyboard)
    else:
        await AioBot.get_current().send_message(chat_id, text, reply_markup=keyboard)


async def send_chats_menu(bot: Bot, call: types.CallbackQuery):
    await call.answer()
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    chats = await bot.group_chats.all()

    for chat in chats:
        keyboard.insert(
            types.InlineKeyboardButton(
                text=button_text_limit(chat.name), callback_data=menu_callback.new(level=3, bot_id=bot.id, operation="chat", chat=chat.id)
            )
        )
    if chats:
        keyboard.insert(
            types.InlineKeyboardButton(
                text=_("Личные сообщения"), callback_data=menu_callback.new(level=3, bot_id=bot.id, operation="chat", chat="personal")
            )
        )
        keyboard.insert(
            types.InlineKeyboardButton(
                text=_("❗️ Выйти из всех чатов"), callback_data=menu_callback.new(level=3, bot_id=bot.id, operation="chat", chat="leave")
            )
        )
    keyboard.insert(
        types.InlineKeyboardButton(text=_("<< Назад"), callback_data=menu_callback.new(level=1, bot_id=bot.id, operation=empty, chat=empty))
    )

    if not chats:
        text = dedent(
            _("""
        Этот бот не добавлен в чаты, поэтому все сообщения будут приходить вам в бот.
        Чтобы подключить чат — добавьте бот @{0} в чат, откройте это меню ещё раз и выберите добавленный чат.
        Если ваш бот состоял в групповом чате до того, как его добавили в Olgram - удалите бота из чата и добавьте
        снова.
        """)
        ).format(bot.name)
    else:
        text = dedent(
            _("""
        В этом разделе вы можете привязать бота @{0} к чату.
        Выберите чат, куда бот будет пересылать сообщения.
        """)
        ).format(bot.name)

    await edit_or_create(call, text, keyboard)


async def send_bot_menu(bot: Bot, call: types.CallbackQuery):
    await call.answer()
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.insert(
        types.InlineKeyboardButton(text=_("Текст"), callback_data=menu_callback.new(level=2, bot_id=bot.id, operation="text", chat=empty))
    )
    keyboard.insert(
        types.InlineKeyboardButton(text=_("Чат"), callback_data=menu_callback.new(level=2, bot_id=bot.id, operation="chat", chat=empty))
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Удалить бот"), callback_data=menu_callback.new(level=2, bot_id=bot.id, operation="delete", chat=empty)
        )
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Статистика"), callback_data=menu_callback.new(level=2, bot_id=bot.id, operation="stat", chat=empty)
        )
    )
    keyboard.insert(
        types.InlineKeyboardButton(text=_("<< Назад"), callback_data=menu_callback.new(level=0, bot_id=empty, operation=empty, chat=empty))
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Опции"), callback_data=menu_callback.new(level=2, bot_id=bot.id, operation="settings", chat=empty)
        )
    )
    if bot.enable_mailing:
        keyboard.insert(
            types.InlineKeyboardButton(
                text=_("Рассылка"), callback_data=menu_callback.new(level=2, bot_id=bot.id, operation="go_mailing", chat=empty)
            )
        )

    await edit_or_create(
        call,
        dedent(
            _("""
    Управление ботом @{0}.

    Если у вас возникли вопросы по настройке бота, то посмотрите нашу справку /help или напишите нам
    @civsocit_feedback_bot
    """)
        ).format(bot.name),
        reply_markup=keyboard,
    )


async def send_bot_delete_menu(bot: Bot, call: types.CallbackQuery):
    await call.answer()
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Да, удалить бот"), callback_data=menu_callback.new(level=3, bot_id=bot.id, operation="delete_yes", chat=empty)
        )
    )
    keyboard.insert(
        types.InlineKeyboardButton(text=_("<< Назад"), callback_data=menu_callback.new(level=1, bot_id=bot.id, operation=empty, chat=empty))
    )

    await edit_or_create(
        call,
        dedent(
            _("""
    Вы уверены, что хотите удалить бота @{0}?
    """)
        ).format(bot.name),
        reply_markup=keyboard,
    )


async def send_bot_settings_menu(bot: Bot, call: types.CallbackQuery):
    await call.answer()
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Потоки сообщений"),
            callback_data=menu_callback.new(
                level=3,
                bot_id=bot.id,
                operation="threads",
                chat=empty,
            ),
        ),
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Данные пользователя"),
            callback_data=menu_callback.new(
                level=3,
                bot_id=bot.id,
                operation="additional_info",
                chat=empty,
            ),
        ),
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Антифлуд"),
            callback_data=menu_callback.new(
                level=3,
                bot_id=bot.id,
                operation="antiflood",
                chat=empty,
            ),
        ),
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Капча"),
            callback_data=menu_callback.new(
                level=3,
                bot_id=bot.id,
                operation="captcha_type",
                chat=empty,
            ),
        ),
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Автоответчик всегда"),
            callback_data=menu_callback.new(
                level=3,
                bot_id=bot.id,
                operation="always_second_message",
                chat=empty,
            ),
        ),
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Рассылка"),
            callback_data=menu_callback.new(
                level=3,
                bot_id=bot.id,
                operation="mailing",
                chat=empty,
            ),
        ),
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Прерывать поток"),
            callback_data=menu_callback.new(
                level=3,
                bot_id=bot.id,
                operation="thread_interrupt",
                chat=empty,
            ),
        ),
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Теги"),
            callback_data=menu_callback.new(
                level=3,
                bot_id=bot.id,
                operation="tags",
                chat=empty,
            ),
        ),
    )
    is_promo = await bot.is_promo()
    if is_promo:
        keyboard.insert(
            types.InlineKeyboardButton(
                text=_("Olgram подпись"),
                callback_data=menu_callback.new(
                    level=3,
                    bot_id=bot.id,
                    operation="olgram_text",
                    chat=empty,
                ),
            ),
        )

    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("<< Назад"),
            callback_data=menu_callback.new(
                level=1,
                bot_id=bot.id,
                operation=empty,
                chat=empty,
            ),
        ),
    )

    thread_turn = _("включены") if bot.enable_threads else _("выключены")
    info_turn = _("включены") if bot.enable_additional_info else _("выключены")
    antiflood_turn = _("включен") if bot.enable_antiflood else _("выключен")
    captcha_turn = _("математическая") if bot.captcha_type == CaptchaType.math else _("выключена")
    enable_always_second_message = _("включён") if bot.enable_always_second_message else _("выключен")
    thread_interrupt = _("да") if bot.enable_thread_interrupt else _("нет")
    mailing_turn = _("включена") if bot.enable_mailing else _("выключена")
    tags_turn = _("включены") if bot.enable_tags else _("выключены")
    text = dedent(
        _("""
    <a href="https://olgram.readthedocs.io/ru/latest/options.html#threads">Потоки сообщений</a>: <b>{0}</b>
    <a href="https://olgram.readthedocs.io/ru/latest/options.html#user-info">Данные пользователя</a>: <b>{1}</b>
    <a href="https://olgram.readthedocs.io/ru/latest/options.html#antiflood">Антифлуд</a>: <b>{2}</b>
    Капча: <b>{3}</b>
    <a href="https://olgram.readthedocs.io/ru/latest/options.html#always_second_message">Автоответчик всегда</a>: <b>{4}</b>
    <a href="https://olgram.readthedocs.io/ru/latest/options.html#thread_interrupt">Прерывать поток</a>: <b>{5}</b>
    <a href="https://olgram.readthedocs.io/ru/latest/options.html#mailing">Рассылка</a>: <b>{6}</b>
    Теги: <b>{7}</b>
    """)
    ).format(thread_turn, info_turn, antiflood_turn, captcha_turn, enable_always_second_message, thread_interrupt, mailing_turn, tags_turn)

    if is_promo:
        olgram_turn = _("включена") if bot.enable_olgram_text else _("выключена")
        text += _("Olgram подпись: <b>{0}</b>").format(olgram_turn)

    await edit_or_create(call, text, reply_markup=keyboard, parse_mode="HTML")


async def send_captcha_settings_menu(bot: Bot, call: types.CallbackQuery):
    """Подменю настройки капчи: тип, тэг, кнопки выбора типа, сброс тэга, назад."""
    await call.answer()
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    type_label = _("математическая") if bot.captcha_type == CaptchaType.math else _("выключена")
    tag_display = (bot.captcha_tag or "").strip() or _("(не задан)")

    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Выключена") + (" ✓" if bot.captcha_type == CaptchaType.disabled else ""),
            callback_data=menu_callback.new(
                level="4",
                bot_id=bot.id,
                operation="captcha_disabled",
                chat=empty,
            ),
        ),
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Математическая") + (" ✓" if bot.captcha_type == CaptchaType.math else ""),
            callback_data=menu_callback.new(
                level="4",
                bot_id=bot.id,
                operation="captcha_math",
                chat=empty,
            ),
        ),
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Сбросить тэг"),
            callback_data=menu_callback.new(
                level="4",
                bot_id=bot.id,
                operation="captcha_reset_tag",
                chat=empty,
            ),
        ),
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("<< Назад"),
            callback_data=menu_callback.new(
                level=3,
                bot_id=bot.id,
                operation="captcha_back",
                chat=empty,
            ),
        ),
    )

    text = dedent(
        _("""
    Настройки капчи для бота @{0}

    Тип капчи: <b>{1}</b>
    Тэг капчи: <b>{2}</b>
    """)
    ).format(bot.name, type_label, tag_display)

    await edit_or_create(call, text, reply_markup=keyboard, parse_mode="HTML")


languages = {
    "en": "English 🇺🇸", 
    "ru": "Русский 🇷🇺", 
    "uk": "Український 🇺🇦", 
    "tr": "Türkçe 🇹🇷", 
    "hy": "հայերեն 🇦🇲", 
    "ka": "ქართული ენა 🇬🇪",
}


async def send_bot_text_menu(bot: Bot, call: ty.Optional[types.CallbackQuery] = None, chat_id: ty.Optional[int] = None, state=None):
    if call:
        await call.answer()

    async with state.proxy() as proxy:
        lang = proxy.get("lang", "none")

    prepared_languages = {ln.locale: ln.text for ln in await bot.start_texts}

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("<< Завершить редактирование"), callback_data=menu_callback.new(level=1, bot_id=bot.id, operation=empty, chat=empty)
        )
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Автоответчик"), callback_data=menu_callback.new(level=3, bot_id=bot.id, operation="next_text", chat=empty)
        )
    )
    keyboard.row(
        types.InlineKeyboardButton(
            text=_("Сбросить текст"), callback_data=menu_callback.new(level=3, bot_id=bot.id, operation="reset_text", chat=empty)
        )
    )
    keyboard.add(
        types.InlineKeyboardButton(
            text=("🟢 " if lang == "none" else "") + _("[все языки]"),
            callback_data=menu_callback.new(level=3, bot_id=bot.id, operation="slang_none", chat=empty),
        )
    )
    for code, name in languages.items():
        prefix = ""
        if code == lang:
            prefix = "🟢 "
        elif code in prepared_languages:
            prefix = "✔️ "
        keyboard.insert(
            types.InlineKeyboardButton(
                text=prefix + name, callback_data=menu_callback.new(level=3, bot_id=bot.id, operation=f"slang_{code}", chat=empty)
            )
        )

    text = dedent(
        _("""
    Сейчас вы редактируете текст, который отправляется после того, как пользователь отправит вашему боту @{0}
    команду /start

    Текущий текст{2}:
    <pre>{1}</pre>
    Отправьте сообщение, чтобы изменить текст.
    """)
    )
    text = text.format(
        bot.name, prepared_languages.get(lang, bot.start_text), _(" (для языка {0})").format(languages[lang]) if lang != "none" else ""
    )
    if call:
        await edit_or_create(call, text, keyboard, parse_mode="HTML")
    else:
        await AioBot.get_current().send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")


async def send_bot_mailing_menu(bot: Bot, call: ty.Optional[types.CallbackQuery] = None, chat_id: ty.Optional[int] = None):
    if call:
        await call.answer()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("<< Отменить рассылку"), callback_data=menu_callback.new(level=1, bot_id=bot.id, operation=empty, chat=empty)
        )
    )

    text = dedent(
        _("""
    Напишите сообщение, которое нужно разослать всем подписчикам вашего бота @{0}. 
    У сообщения будет до {1} получателей. 
    Учтите, что
    1. Рассылается только одно сообщение за раз (в т.ч. только одна картинка)
    2. Когда рассылка запущена, её нельзя отменить 
    """)
    )
    text = text.format(bot.name, len(await bot.mailing_users))
    if call:
        await edit_or_create(call, text, keyboard, parse_mode="HTML")
    else:
        await AioBot.get_current().send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")


@dp.message_handler(
    state="wait_mailing_text",
    content_types=[
        types.ContentType.TEXT,
        types.ContentType.LOCATION,
        types.ContentType.DOCUMENT,
        types.ContentType.PHOTO,
        types.ContentType.AUDIO,
        types.ContentType.VIDEO,
    ],
)  # TODO: not command
async def mailing_text_received(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:
        bot_id = proxy["bot_id"]
        proxy["mailing_content_type"] = message.content_type

        buffer = BytesIO()

        match message.content_type:
            case types.ContentType.TEXT:
                proxy["mailing_text"] = message.html_text
            case types.ContentType.LOCATION:
                proxy["mailing_location"] = message.location
            case types.ContentType.PHOTO | types.ContentType.DOCUMENT | types.ContentType.AUDIO | types.ContentType.VIDEO:
                proxy["mailing_caption"] = message.caption

                match message.content_type:
                    case types.ContentType.PHOTO:
                        obj = message.photo[-1]
                    case types.ContentType.DOCUMENT:
                        obj = message.document
                    case types.ContentType.AUDIO:
                        obj = message.audio
                    case types.ContentType.VIDEO:
                        obj = message.video

                if obj.file_size and obj.file_size > 4194304:
                    return await message.answer(_("Слишком большой файл (4 Мб максимум)"))

                try:
                    await obj.download(buffer, timeout=5)
                except Exception as err:
                    logging.error("Error downloading file")
                    logging.error(err, exc_info=True)
                    return await message.answer(_("Не удалось загрузить файл (слишком большой размер?)"))
                proxy["mailing_data"] = buffer.getvalue()
                proxy["mailing_file_name"] = getattr(obj, "file_name", None)
        _message_id = await send_stored_message(proxy, AioBot.get_current(), message.chat.id)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("<< Отменить рассылку"), callback_data=menu_callback.new(level=1, bot_id=bot_id, operation=empty, chat=empty)
        )
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Да, начать рассылку"), callback_data=menu_callback.new(level=3, bot_id=bot_id, operation="go_go_mailing", chat=empty)
        )
    )

    await AioBot.get_current().send_message(
        message.chat.id,
        reply_to_message_id=_message_id,
        text="Вы уверены, что хотите разослать это сообщение всем пользователям?",
        reply_markup=keyboard,
    )


async def send_bot_statistic_menu(bot: Bot, call: ty.Optional[types.CallbackQuery] = None, chat_id: ty.Optional[int] = None):
    if call:
        await call.answer()
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.insert(
        types.InlineKeyboardButton(text=_("<< Назад"), callback_data=menu_callback.new(level=1, bot_id=bot.id, operation=empty, chat=empty))
    )

    text = dedent(
        _("""
    Статистика по боту @{0}

    Входящих сообщений: <b>{1}</b>
    Ответных сообщений: <b>{2}</b>
    Шаблоны ответов: <b>{3}</b>
    Забанено пользователей: <b>{4}</b>
    """)
    ).format(bot.name, bot.incoming_messages_count, bot.outgoing_messages_count, len(await bot.answers), len(await bot.banned_users))
    if call:
        await edit_or_create(call, text, keyboard, parse_mode="HTML")
    else:
        await AioBot.get_current().send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")


async def send_bot_second_text_menu(bot: Bot, call: ty.Optional[types.CallbackQuery] = None, chat_id: ty.Optional[int] = None, state=None):
    if call:
        await call.answer()

    async with state.proxy() as proxy:
        lang = proxy.get("lang", "none")

    prepared_languages = {ln.locale: ln.text for ln in await bot.second_texts}

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("<< Завершить редактирование"), callback_data=menu_callback.new(level=1, bot_id=bot.id, operation=empty, chat=empty)
        )
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Предыдущий текст"), callback_data=menu_callback.new(level=2, bot_id=bot.id, operation="text", chat=empty)
        )
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Шаблоны ответов..."), callback_data=menu_callback.new(level=3, bot_id=bot.id, operation="templates", chat=empty)
        )
    )
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("Сбросить текст"), callback_data=menu_callback.new(level=3, bot_id=bot.id, operation="reset_second_text", chat=empty)
        )
    )
    keyboard.add(
        types.InlineKeyboardButton(
            text=("🟢 " if lang == "none" else "") + _("[все языки]"),
            callback_data=menu_callback.new(level=3, bot_id=bot.id, operation="alang_none", chat=empty),
        )
    )
    for code, name in languages.items():
        prefix = ""
        if code == lang:
            prefix = "🟢 "
        elif code in prepared_languages:
            prefix = "✔️ "
        keyboard.insert(
            types.InlineKeyboardButton(
                text=prefix + name, callback_data=menu_callback.new(level=3, bot_id=bot.id, operation=f"alang_{code}", chat=empty)
            )
        )

    text = dedent(
        _("""
    Сейчас вы редактируете текст автоответчика. Это сообщение отправляется в ответ на все входящие сообщения @{0} \
автоматически. По умолчанию оно отключено.

    Текущий текст{2}:
    <pre>{1}</pre>
    Отправьте сообщение, чтобы изменить текст.
    """)
    )
    text = text.format(
        bot.name,
        prepared_languages.get(lang, bot.second_text or _("отключено")),
        _(" (для языка {0})").format(languages[lang]) if lang != "none" else "",
    )
    if call:
        await edit_or_create(call, text, keyboard, parse_mode="HTML")
    else:
        await AioBot.get_current().send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")


async def send_bot_templates_menu(bot: Bot, call: ty.Optional[types.CallbackQuery] = None, chat_id: ty.Optional[int] = None):
    if call:
        await call.answer()
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.insert(
        types.InlineKeyboardButton(
            text=_("<< Завершить редактирование"), callback_data=menu_callback.new(level=1, bot_id=bot.id, operation=empty, chat=empty)
        )
    )

    text = dedent(
        _("""
    Сейчас вы редактируете шаблоны ответов для @{0}. Текущие шаблоны:

    <pre>
    {1}
    </pre>
    Отправьте какую-нибудь фразу (например: "Ваш заказ готов, ожидайте!"), чтобы добавить её в шаблон.
    Чтобы удалить шаблон из списка, отправьте его номер в списке (например, 4)
    """)
    )

    templates = await bot.answers

    total_text_len = sum(len(t.text) for t in templates) + len(text)  # примерная длина текста
    max_len = 1000
    if total_text_len > 4000:
        max_len = 100

    templates_text = "\n".join(f"{n}. {wrap(template.text, max_len)}" for n, template in enumerate(templates))
    if not templates_text:
        templates_text = _("(нет шаблонов)")
    text = text.format(bot.name, templates_text)
    if call:
        await edit_or_create(call, text, keyboard, parse_mode="HTML")
    else:
        await AioBot.get_current().send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")


@dp.message_handler(state="wait_start_text", content_types="text", regexp="^[^/].+")  # Not command
async def start_text_received(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:
        bot_id = proxy.get("bot_id")
        lang = proxy.get("lang", "none")

    bot = await Bot.get_or_none(pk=bot_id)
    if lang == "none":
        bot.start_text = message.html_text
        await bot.save(update_fields=["start_text"])
    else:
        obj, created = await BotStartMessage.get_or_create(bot=bot, locale=lang, defaults={"text": message.html_text})
        if not created:
            obj.text = message.html_text
            await obj.save(update_fields=["text"])
    await send_bot_text_menu(bot, chat_id=message.chat.id, state=state)


@dp.message_handler(state="wait_second_text", content_types="text", regexp="^[^/].+")  # Not command
async def second_text_received(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:
        bot_id = proxy.get("bot_id")
        lang = proxy.get("lang", "none")

    bot = await Bot.get_or_none(pk=bot_id)
    if lang == "none":
        bot.second_text = message.html_text
        await bot.save(update_fields=["second_text"])
    else:
        obj, created = await BotSecondMessage.get_or_create(bot=bot, locale=lang, defaults={"text": message.html_text})
        if not created:
            obj.text = message.html_text
            await obj.save(update_fields=["text"])
        if not bot.second_text:
            bot.second_text = message.html_text
            await bot.save(update_fields=["second_text"])
    await send_bot_second_text_menu(bot, chat_id=message.chat.id, state=state)


@dp.message_handler(state="wait_template", content_types="text", regexp="^[^/](.+)?")  # Not command
async def template_received(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:
        bot_id = proxy.get("bot_id")
    bot = await Bot.get_or_none(pk=bot_id)

    if message.text.isdigit():
        # Delete template
        number = int(message.text)
        templates = await bot.answers
        if not templates:
            await message.answer(_("У вас нет шаблонов, чтобы их удалять"))
        if number < 0 or number >= len(templates):
            await message.answer(_("Неправильное число. Чтобы удалить шаблон, введите число от 0 до {0}").format(len(templates)))
            return
        await templates[number].delete()
    else:
        # Add template
        total_templates = len(await bot.answers)
        if total_templates > 30:
            await message.answer(_("У вашего бота уже слишком много шаблонов"))
        else:
            answers = await bot.answers.filter(text=message.text)
            if answers:
                await message.answer(_("Такой текст уже есть в списке шаблонов"))
            else:
                template = DefaultAnswer(text=message.text, bot=bot)
                await template.save()

    await send_bot_templates_menu(bot, chat_id=message.chat.id)


@dp.callback_query_handler(menu_callback.filter(), state="*")
async def callback(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    level = callback_data.get("level")

    if level == "0":
        return await send_bots_menu(call.message.chat.id, call.from_user.id, call)

    bot_id = callback_data.get("bot_id")
    bot = await Bot.get_or_none(id=bot_id)
    if not bot or (await bot.owner).telegram_id != call.from_user.id:
        await call.answer(_("У вас нет прав на этого бота"), show_alert=True)
        return

    operation = callback_data.get("operation")

    match level:
        case "1":
            await state.reset_state()
            return await send_bot_menu(bot, call)

        case "2":
            await state.reset_state()
            match operation:
                case "chat":
                    return await send_chats_menu(bot, call)
                case "delete":
                    return await send_bot_delete_menu(bot, call)
                case "stat":
                    return await send_bot_statistic_menu(bot, call)
                case "settings":
                    return await send_bot_settings_menu(bot, call)
                case "go_mailing":
                    if bot.last_mailing_at and bot.last_mailing_at >= datetime.now(tz=timezone.utc) - timedelta(minutes=5):
                        return await call.answer(_("Рассылка была совсем недавно, подождите немного"), show_alert=True)
                    if not await bot.mailing_users:
                        return await call.answer(_("Нет пользователей для рассылки"))
                    await state.set_state("wait_mailing_text")
                    async with state.proxy() as proxy:
                        proxy["bot_id"] = bot.id
                    return await send_bot_mailing_menu(bot, call)
                case "text":
                    await state.set_state("wait_start_text")
                    async with state.proxy() as proxy:
                        proxy["bot_id"] = bot.id
                    return await send_bot_text_menu(bot, call, state=state)

        case "3":
            match operation:
                case "delete_yes":
                    return await bot_actions.delete_bot(bot, call)
                case "mailing":
                    await bot_actions.mailing(bot, call)
                    return await send_bot_settings_menu(bot, call)
                case "go_go_mailing":
                    if (await state.get_state()) == "wait_mailing_text":
                        async with state.proxy() as proxy:
                            mailing_data = dict(proxy)
                        await state.reset_state()

                        if bot.last_mailing_at and bot.last_mailing_at >= datetime.now(tz=timezone.utc) - timedelta(minutes=5):
                            return await call.answer(_("Рассылка была совсем недавно, подождите немного"), show_alert=True)
                        if not await bot.mailing_users:
                            return await call.answer(_("Нет пользователей для рассылки"))

                        await call.answer(_("Рассылка запущена"))
                        count = await bot_actions.go_mailing(bot, mailing_data)
                        return await call.message.answer(_("Рассылка завершена, отправлено {0} сообщений").format(count))
                    return await call.answer(_("Устарело, создайте новую рассылку"))
                case "chat":
                    return await bot_actions.select_chat(bot, call, callback_data.get("chat"))
                case "threads":
                    await bot_actions.threads(bot, call)
                    return await send_bot_settings_menu(bot, call)
                case "antiflood":
                    await bot_actions.antiflood(bot, call)
                    return await send_bot_settings_menu(bot, call)
                case "captcha_type":
                    return await send_captcha_settings_menu(bot, call)
                case "captcha_back":
                    return await send_bot_settings_menu(bot, call)
                case "additional_info":
                    await bot_actions.additional_info(bot, call)
                    return await send_bot_settings_menu(bot, call)
                case "always_second_message":
                    await bot_actions.always_second_message(bot, call)
                    return await send_bot_settings_menu(bot, call)
                case "tags":
                    await bot_actions.tags(bot, call)
                    return await send_bot_settings_menu(bot, call)
                case "thread_interrupt":
                    await bot_actions.thread_interrupt(bot, call)
                    return await send_bot_settings_menu(bot, call)
                case "olgram_text":
                    await bot_actions.olgram_text(bot, call)
                    return await send_bot_settings_menu(bot, call)
                case "reset_text":
                    await bot_actions.reset_bot_text(bot, call, state)
                    return await send_bot_text_menu(bot, call, state=state)
                case op if op and op.startswith("slang_"):
                    async with state.proxy() as proxy:
                        lang = op.replace("slang_", "")
                        if lang == "none" or lang in languages:
                            proxy["lang"] = lang
                    return await send_bot_text_menu(bot, call, state=state)
                case "next_text":
                    await state.set_state("wait_second_text")
                    async with state.proxy() as proxy:
                        proxy["bot_id"] = bot.id
                    return await send_bot_second_text_menu(bot, call, state=state)
                case op if op and op.startswith("alang_"):
                    async with state.proxy() as proxy:
                        lang = op.replace("alang_", "")
                        if lang == "none" or lang in languages:
                            proxy["lang"] = lang
                    return await send_bot_second_text_menu(bot, call, state=state)
                case "reset_second_text":
                    await bot_actions.reset_bot_second_text(bot, call, state)
                    return await send_bot_second_text_menu(bot, call, state=state)
                case "templates":
                    await state.set_state("wait_template")
                    async with state.proxy() as proxy:
                        proxy["bot_id"] = bot.id
                    return await send_bot_templates_menu(bot, call)

        case "4":
            match operation:
                case "captcha_disabled":
                    await bot_actions.captcha_set_type(bot, CaptchaType.disabled)
                    return await send_captcha_settings_menu(bot, call)
                case "captcha_math":
                    await bot_actions.captcha_set_type(bot, CaptchaType.math)
                    return await send_captcha_settings_menu(bot, call)
                case "captcha_reset_tag":
                    await bot_actions.captcha_reset_tag(bot)
                    return await send_captcha_settings_menu(bot, call)
