import gettext
import os
from aqt import QLocale

lang = QLocale.system().name()  # like "zh_CN"


def get_locale():
    """Returns the current locale."""
    return getattr(QLocale.system().name(), lang, "zh")

localedir = os.path.join(os.path.dirname(__file__), './locales')
translation = gettext.translation('messages', localedir,languages=get_locale(), fallback=True)
_ = translation.gettext