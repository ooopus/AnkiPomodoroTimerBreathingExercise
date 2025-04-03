# __init__.py (插件主文件 - PyQt6 & Cycle-based Breathing)

from aqt import mw, gui_hooks

from PyQt6.QtGui import QAction

from .timer_utils import get_pomodoro_timer, get_timer_label
from .hooks import on_reviewer_did_start, on_state_did_change
from .ui import ConfigDialog, show_timer_in_statusbar


def show_config_dialog():
    """Creates and shows the configuration dialog."""
    dialog = ConfigDialog(mw)
    dialog.exec()


def setup_plugin():
    """Loads config, sets up hooks, and adds menu item."""

    # Register hooks
    # Note: Use reviewer_will_start_review is often better than did_show_question
    # as it fires once per review session start. did_show_question fires per card.
    # Let's stick with did_show_question for now as per original code, but consider changing.
    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_start)
    gui_hooks.state_did_change.append(on_state_did_change)

    # Add menu item
    action = QAction("番茄钟 & 呼吸设置...", mw)  # "Pomodoro & Breathing Settings..."
    action.triggered.connect(show_config_dialog)
    if hasattr(mw, "form") and hasattr(mw.form, "menuTools"):
        mw.form.menuTools.addAction(action)
    else:
        from aqt.utils import tooltip

        tooltip("警告: 无法添加番茄钟菜单项 (未找到menuTools)。", period=3000)


def cleanup_plugin():
    """Clean up resources when plugin is unloaded"""
    from .ui.statusbar import remove_widget
    from .timer_utils import get_pomodoro_timer
    
    timer = get_pomodoro_timer()
    if timer:
        timer.stop_timer(True)
    
    remove_widget()

gui_hooks.main_window_did_init.append(cleanup_plugin)

# ---Startup---
# This code runs when Anki loads the addon
if __name__ != "__main__":
    # Use mw.progress.timer to ensure setup runs after Anki is fully initialized
    mw.progress.timer(100, setup_plugin, False)  # Run once after 100ms delay
