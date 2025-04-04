import gettext
import os
from aqt import QLocale

lang = QLocale.system().name()  # like "zh_CN"

localedir = os.path.join(os.path.dirname(__file__), './locales')
translation = gettext.translation('messages', localedir, languages=lang, fallback=True)
_ = translation.gettext