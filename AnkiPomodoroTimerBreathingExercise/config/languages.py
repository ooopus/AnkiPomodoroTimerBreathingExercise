from enum import Enum


class LanguageCode(str, Enum):
    _display_name: str

    def __new__(cls, value, display_name: str):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._display_name = display_name
        return obj

    @property
    def display_name(self) -> str:
        return self._display_name

    # Define members with their display names
    AUTO = "auto", "Auto"
    ENGLISH = "en_US", "English"
    GERMAN = "de_DE", "Deutsch"
    CHINESE_SIMPLIFIED = "zh_CN", "简体中文"
