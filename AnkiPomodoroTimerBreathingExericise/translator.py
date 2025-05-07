import gettext
import os

from aqt import QLocale

# from aqt.utils import tooltip
global lang
global localedir
lang = QLocale.system().name()  # like "zh_CN"

localedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "locales"))
translation = gettext.translation(
    "messages", localedir, languages=[lang], fallback=True
)


def _(*args, **kwargs):
    # # Show tooltip when translation function is called
    # tooltip(f"Current language: {lang}")
    return translation.gettext(*args, **kwargs)
