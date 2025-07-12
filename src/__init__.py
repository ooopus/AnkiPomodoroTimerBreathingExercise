# __init__.py (插件主文件 - PyQt6 & Cycle-based Breathing)

# __init__.py (插件主文件 - PyQt6 & Cycle-based Breathing)

import time

from anki.buildinfo import version as anki_version
from aqt import QAction, gui_hooks, mw

from .breathing import start_breathing_exercise
from .hooks import on_reviewer_did_start, on_state_did_change, on_theme_change
from .state import AppState, get_app_state
from .translator import _
from .ui import ConfigDialog, show_update_warning

# --- Anki Version Check ---
MIN_ANKI_VERSION = "25.07"


def check_anki_version() -> bool:
    """
    Checks if the current Anki version is sufficient.
    Shows a warning dialog if it's not.
    """
    try:
        min_parts = [int(p) for p in MIN_ANKI_VERSION.split(".")]
        current_parts = [int(p) for p in anki_version.split(".")]

        # Pad shorter version with zeros for fair comparison
        max_len = max(len(min_parts), len(current_parts))
        min_parts.extend([0] * (max_len - len(min_parts)))
        current_parts.extend([0] * (max_len - len(current_parts)))

        if current_parts < min_parts:
            show_update_warning(
                required_version=MIN_ANKI_VERSION, current_version=anki_version
            )
            return False
    except ValueError:
        from aqt.utils import tooltip

        tooltip(_("无法解析Anki版本: {}").format(anki_version))
        show_update_warning(
            required_version=MIN_ANKI_VERSION,
            current_version=f"{anki_version} (unparsable)",
        )
        return False
    return True


def add_menu_item():
    action = QAction(_("番茄钟 & 呼吸设置..."), mw)
    action.triggered.connect(show_config_dialog)

    breathe_action = QAction(_("启动呼吸训练"), mw)
    breathe_action.triggered.connect(start_breathing_exercise)

    if hasattr(mw, "form") and hasattr(mw.form, "menuTools"):
        mw.form.menuTools.addAction(action)
        mw.form.menuTools.addAction(breathe_action)
    else:
        from aqt.utils import tooltip

        tooltip(_("警告: 无法添加番茄钟菜单项"), period=3000)


def show_config_dialog():
    """Creates and shows the configuration dialog."""
    dialog = ConfigDialog(mw)
    dialog.exec()


def _check_and_reset_daily_timer(app_state: AppState):
    """Checks if the date has changed and resets the daily timer if needed."""
    config = app_state.config
    last_date = config.last_date
    today = time.strftime("%Y-%m-%d")
    if last_date != today:
        app_state.update_config_value("daily_pomodoro_seconds", 0)
        app_state.update_config_value("last_date", today)


def setup_plugin():
    """Loads config, sets up hooks, and adds menu item."""
    if not check_anki_version():
        return  # Stop setup if version is too old

    app_state = get_app_state()
    _check_and_reset_daily_timer(app_state)

    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_start)
    gui_hooks.state_did_change.append(on_state_did_change)
    gui_hooks.theme_did_change.append(on_theme_change)
    add_menu_item()


# ---Startup---
# This code runs when Anki loads the addon
if __name__ != "__main__":
    mw.progress.single_shot(100, setup_plugin, False)  # Run once after 100ms delay
