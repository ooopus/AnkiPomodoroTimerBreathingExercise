from aqt import mw, QLabel
from typing import Union

from aqt.utils import tooltip
from ..state import get_app_state
from ..constants import STATUSBAR_DEFAULT_TEXT


def remove_widget():
    """Removes the timer widget from status bar"""
    # Use AppState to get label
    app_state = get_app_state()
    label = app_state.timer_label
    if label:
        try:
            status_bar = mw.statusBar()
            if status_bar is not None:
                status_bar.removeWidget(label)
                label.setParent(None)
                label.deleteLater()
                # Use AppState to set label
                app_state.timer_label = None 
                import gc

                label.destroyed.connect(lambda: gc.collect())
        except Exception as e:
            tooltip(f"Error removing timer widget: {e}")


def show_timer_in_statusbar(show: Union[bool, None]) -> None:
    """Adds or removes the timer label from the Anki status bar."""
    # Use AppState
    app_state = get_app_state()
    config = app_state.config 
    label = app_state.timer_label

    if show is None:
        show = False

    if (
        not show
        or not config.get("enabled", True)
        or not config.get("statusbar_format", True)
        or config.get("statusbar_format") == "NONE"
    ):
        if label:
            mw.progress.timer(0, remove_widget, False)
        return

    if not label:

        def add_widget():
            new_label = QLabel(STATUSBAR_DEFAULT_TEXT)
            try:
                status_bar = mw.statusBar()
                if status_bar is not None:
                    status_bar.addPermanentWidget(new_label, 0)
                    new_label.show()
                    # Use AppState to set label
                    app_state.timer_label = new_label
            except Exception as e:
                tooltip(f"Error adding timer widget: {e}")

        mw.progress.timer(0, add_widget, False)
