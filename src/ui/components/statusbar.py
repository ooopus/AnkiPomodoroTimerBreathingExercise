from aqt import QLabel, mw
from aqt.utils import tooltip

from ...config.constants import Defaults
from ...config.enums import StatusBarFormat
from ...state import get_app_state


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


def show_timer_in_statusbar(show: bool) -> None:
    """Adds or removes the timer label from the Anki status bar."""
    # Use AppState
    app_state = get_app_state()
    config = app_state.config
    label = app_state.timer_label

    if (
        not show
        or not config.enabled
        or not config.statusbar_format
        or config.statusbar_format == StatusBarFormat.NONE
    ):
        if label:
            mw.progress.single_shot(0, remove_widget, False)
        return

    if not label:

        def add_widget():
            new_label = QLabel(Defaults.StatusBar.TEXT)
            try:
                status_bar = mw.statusBar()
                if status_bar is not None:
                    status_bar.addPermanentWidget(new_label, 0)
                    new_label.show()
                    # Use AppState to set label
                    app_state.timer_label = new_label
            except Exception as e:
                tooltip(f"Error adding timer widget: {e}")

        mw.progress.single_shot(0, add_widget, False)
