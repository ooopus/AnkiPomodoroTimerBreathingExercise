import gettext
import os

from aqt import QLocale

from .config.languages import LanguageCode

# from aqt.utils import tooltip
global lang
global localedir
lang = QLocale.system().name()  # like "zh_CN"

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
    global translation
    translation = build_translation(language_code.value)
