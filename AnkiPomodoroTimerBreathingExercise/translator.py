import gettext
import json
import os

from aqt import QLocale

from .config.languages import LanguageCode


def get_lang_from_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
        lang = config.get("language")
        if lang:
            return lang
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


def _(*args, **kwargs):
    # # Show tooltip when translation function is called
    # tooltip(f"Current language: {lang}")
    return translation.gettext(*args, **kwargs)


def set_language(language_code: LanguageCode):
    if language_code == LanguageCode.AUTO:
        global lang
        lang = QLocale.system().name()  # like "zh_CN"
    else:
        lang = language_code.value
    global translation
    translation = build_translation(lang)
