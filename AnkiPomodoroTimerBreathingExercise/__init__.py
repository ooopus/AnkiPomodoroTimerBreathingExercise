# __init__.py (插件主文件 - PyQt6 & Cycle-based Breathing)

import time

from aqt import QAction, gui_hooks, mw

from .hooks import on_reviewer_did_start, on_state_did_change, on_theme_change
from .state import AppState, get_app_state
from .translator import _
from .ui import ConfigDialog


def show_config_dialog():
    """Creates and shows the configuration dialog."""
    dialog = ConfigDialog(mw)
    dialog.exec()


def _check_and_reset_daily_timer(app_state: AppState):
    """Checks if the date has changed and resets the daily timer if needed."""
    config = app_state.config
    last_date = config.get("last_date", "")
    today = time.strftime("%Y-%m-%d")
    if last_date != today:
        app_state.update_config_value("daily_pomodoro_seconds", 0)
        app_state.update_config_value("last_date", today)


def setup_plugin():
    """Loads config, sets up hooks, and adds menu item."""

    app_state = get_app_state()
    _check_and_reset_daily_timer(app_state)

    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_start)
    gui_hooks.state_did_change.append(on_state_did_change)
    gui_hooks.theme_did_change.append(on_theme_change)
    # Add menu item
    action = QAction(_("番茄钟 & 呼吸设置..."), mw)
    action.triggered.connect(show_config_dialog)
    if hasattr(mw, "form") and hasattr(mw.form, "menuTools"):
        mw.form.menuTools.addAction(action)
    else:
        from aqt.utils import tooltip

        tooltip(_("警告: 无法添加番茄钟菜单项"), period=3000)


# ---Startup---
# This code runs when Anki loads the addon
if __name__ != "__main__":
    mw.progress.single_shot(100, setup_plugin, False)  # Run once after 100ms delay
