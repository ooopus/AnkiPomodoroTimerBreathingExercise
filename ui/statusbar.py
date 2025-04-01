from aqt import mw
from PyQt6.QtWidgets import QLabel
from ..config import get_config, get_pomodoro_timer, get_timer_label, set_timer_label
from ..constants import STATUSBAR_DEFAULT_TEXT


def show_timer_in_statusbar(show: bool):
    """Adds or removes the timer label from the Anki status bar."""
    config = get_config()
    timer = get_pomodoro_timer()
    label = get_timer_label()

    if (
        not show
        or not config.get("enabled", True)
        or not config.get("show_statusbar_timer", True)
    ):
        if label:

            def remove_widget():
                current_label = get_timer_label()
                if current_label:
                    try:
                        mw.statusBar().removeWidget(current_label)
                        current_label.deleteLater()
                        set_timer_label(None)
                    except Exception as e:
                        print(f"Error removing timer widget: {e}")

            mw.progress.timer(0, remove_widget, False)
        return

    if not label:

        def add_widget():
            new_label = QLabel(STATUSBAR_DEFAULT_TEXT)
            try:
                mw.statusBar().addPermanentWidget(new_label, 0)
                new_label.show()
                set_timer_label(new_label)
                if timer:
                    timer.update_display()
            except Exception as e:
                print(f"Error adding timer widget: {e}")

        mw.progress.timer(0, add_widget, False)
    elif label and timer and timer.isActive():
        timer.update_display()
