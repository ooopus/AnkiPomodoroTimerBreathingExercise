import gettext
import json
import os
from typing import TYPE_CHECKING, TypedDict, cast

from aqt import QLocale

if TYPE_CHECKING:
    from .config.languages import LanguageCode


class ConfigJson(TypedDict):
    language: str


def get_lang_from_config() -> str:
    config_path: str = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_path, encoding="utf-8") as f:
            config = cast(ConfigJson, json.load(f))
        lang_value = config.get("language")
        return lang_value
    except Exception as e:
        print(f"[translator] Error reading config file: {e}")
    return QLocale.system().name()  # like "zh_CN"


lang = get_lang_from_config()
localedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "locales"))


def build_translation(language_code: str):
    return gettext.translation(
        "messages", localedir, languages=[language_code], fallback=True
    )


translation = build_translation(lang)


def _(s: str) -> str:
    """带类型注解的翻译函数"""
    return translation.gettext(s)


def set_language(language_code: "LanguageCode"):
    from .config.languages import LanguageCode

    if language_code == LanguageCode.AUTO.value:
        global lang
        lang = QLocale.system().name()  # like "zh_CN"
    else:
        lang = language_code
    global translation
    translation = build_translation(lang)
