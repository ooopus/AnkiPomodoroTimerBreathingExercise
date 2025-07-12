import webbrowser

from aqt import QDialog, QLabel, QPushButton, QVBoxLayout, mw

from ..translator import _

ANKI_RELEASES_URL = "https://github.com/ankitects/anki/releases/latest"


def show_update_warning(required_version: str, current_version: str):
    """Shows a dialog warning the user to update Anki."""
    dialog = QDialog(mw)
    dialog.setWindowTitle(_("请更新Anki"))
    dialog.setModal(True)

    layout = QVBoxLayout(dialog)
    dialog.setLayout(layout)

    message_text = (
        _(
            "Anki番茄钟 & 呼吸训练插件需要Anki版本 <b>{required_version}</b> 或更高版本才能运行。"
        ).format(required_version=required_version)
        + "<br><br>"
        + _("您当前使用的Anki版本是 <b>{current_version}</b>。").format(
            current_version=current_version
        )
        + "<br><br>"
        + _("请更新Anki到最新版本以使用此插件。")
    )
    message = QLabel(message_text)
    message.setWordWrap(True)
    layout.addWidget(message)

    update_button = QPushButton(_("跳转到Anki更新页面"))
    update_button.clicked.connect(lambda: webbrowser.open(ANKI_RELEASES_URL))
    layout.addWidget(update_button)

    ok_button = QPushButton(_("确定"))
    ok_button.clicked.connect(dialog.accept)
    layout.addWidget(ok_button)

    dialog.exec()
