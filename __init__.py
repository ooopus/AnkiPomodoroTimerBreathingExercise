# __init__.py (插件主文件 - PyQt6 & Cycle-based Breathing)

from aqt import mw, gui_hooks

from PyQt6.QtGui import QAction

from .config import get_pomodoro_timer, get_timer_label
from .hooks import on_reviewer_did_start, on_state_did_change
from .ui import ConfigDialog, show_timer_in_statusbar

def show_config_dialog():
    """Creates and shows the configuration dialog."""
    dialog = ConfigDialog(mw)
    dialog.exec()

def setup_plugin():
    """Loads config, sets up hooks, and adds menu item."""
    print("Setting up Pomodoro & Breathing Addon...")
    
    # Register hooks
    # Note: Use reviewer_will_start_review is often better than did_show_question
    # as it fires once per review session start. did_show_question fires per card.
    # Let's stick with did_show_question for now as per original code, but consider changing.
    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_start)
    gui_hooks.state_did_change.append(on_state_did_change)

    # Add menu item
    action = QAction("番茄钟 & 呼吸设置...", mw) # "Pomodoro & Breathing Settings..."
    action.triggered.connect(show_config_dialog)
    if hasattr(mw, 'form') and hasattr(mw.form, 'menuTools'):
        mw.form.menuTools.addAction(action)
        print("Menu item added to Tools menu.")
    else:
        print("Warning: Could not add Pomodoro menu item (menuTools not found).")

    # Initial status bar setup if enabled and timer exists (e.g., addon reloaded)
    timer = get_pomodoro_timer()
    label = get_timer_label()
    if timer and timer.isActive():
        show_timer_in_statusbar(True)
    elif label:
        show_timer_in_statusbar(False)

    print("Pomodoro & Breathing Addon setup complete.")


# --- 启动插件 ---
# This code runs when Anki loads the addon
if __name__ != "__main__":
    # Use mw.progress.timer to ensure setup runs after Anki is fully initialized
    mw.progress.timer(100, setup_plugin, False) # Run once after 100ms delay