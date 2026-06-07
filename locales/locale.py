import gettext
from olgram.settings import BotSettings
from os.path import dirname

locales_dir = dirname(__file__)


def dummy_translator(x: str) -> str:
    return x


def get_translator(lang: str):
    """Получить переводчик для языка с обработкой ошибок"""
    if lang == "ru":
        return dummy_translator
    
    t = gettext.translation("olgram", localedir=locales_dir, languages=[lang], fallback=True)
    return t.gettext
    

lang = BotSettings.language()
_ = get_translator(lang)


translators = {
    "ru": dummy_translator,
    "uk": get_translator("uk"),
    "zh": get_translator("zh"),
    "en": get_translator("en"),
}
