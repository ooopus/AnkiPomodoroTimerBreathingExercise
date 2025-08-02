import gettext
import json
import os
from pathlib import Path
from typing import TypedDict, cast

from aqt import QLocale

from .config.languages import LanguageCode


class ConfigJson(TypedDict):
    language: str


def _get_config_file_path() -> Path:
    """获取配置文件的完整路径。"""
    module_path = os.path.abspath(__file__)
    package_root = os.path.dirname(module_path)
    config_file_path = Path(package_root) / "user_files" / "config.json"
    return config_file_path


def get_lang_from_config() -> str:
    config_path = _get_config_file_path()
    try:
        with open(config_path, encoding="utf-8") as f:
            config = cast(ConfigJson, json.load(f))
        lang_value = config.get("language")
        if lang_value == LanguageCode.AUTO.value:
            return QLocale.system().name()
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


def set_language(language_code: LanguageCode):
    if language_code == LanguageCode.AUTO.value:
        global lang
        lang = QLocale.system().name()  # like "zh_CN"
    else:
        lang = language_code
    global translation
    translation = build_translation(lang)
