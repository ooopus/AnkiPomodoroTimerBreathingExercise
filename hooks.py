from aqt import mw
from aqt.utils import tooltip
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QDialog
from .constants import PHASES, DEFAULT_POMODORO_MINUTES, DEFAULT_BREATHING_CYCLES
from .breathing import BreathingDialog
from .config import get_config, get_pomodoro_timer
from .pomodoro import PomodoroTimer

# --- Anki 钩子函数 ---

def on_reviewer_did_start(reviewer):
    """Starts the Pomodoro timer when the reviewer screen is shown."""
    config = get_config()  # Use our config getter
    timer = get_pomodoro_timer()
    
    if not config.get("enabled", True):
        return

    # 确保只有一个计时器实例
    if timer is None or not isinstance(timer, PomodoroTimer):
        timer = PomodoroTimer(mw)
    
    # 确保在主线程操作
    def _start_timer():
        if not timer.isActive():
            pomo_minutes = config.get("pomodoro_minutes", DEFAULT_POMODORO_MINUTES)
            timer.start_timer(pomo_minutes)
    
    mw.progress.timer(100, _start_timer, False)


def on_state_did_change(new_state: str, old_state: str):
    """Stops the Pomodoro timer when leaving the reviewer state."""
    timer = get_pomodoro_timer()
    config = get_config()
    if old_state == "review" and new_state != "review":
        if timer and timer.isActive() and config.get("enabled", True):
            print(f"Left reviewer state ({old_state} -> {new_state}). Stopping Pomodoro timer.")
            timer.stop_timer()
            tooltip("番茄钟已暂停。", period=2000)

def on_pomodoro_finished():
    """Called when the Pomodoro timer reaches zero."""
    tooltip("番茄钟时间到！休息一下。", period=3000) # "Pomodoro time's up! Take a break."
    # Ensure we are on the main thread before changing state or showing dialog
    mw.progress.timer(100, lambda: _after_pomodoro_finish_tasks(), False)


def _after_pomodoro_finish_tasks():
    """Actions to perform after the Pomodoro finishes (runs on main thread)."""
    from .ui import show_timer_in_statusbar
    
    # Return to deck browser
    if mw.state == "review":
        print("Returning to deck browser after Pomodoro.")
        mw.moveToState("deckBrowser")
    
    # 双重确保状态栏隐藏
    show_timer_in_statusbar(False)
    
    # Show breathing dialog after a short delay
    QTimer.singleShot(200, show_breathing_dialog) # Delay allows state change to settle

def show_breathing_dialog():
    """Checks config and shows the BreathingDialog if appropriate."""
    config = get_config()  # Use our config getter
    if not config.get("enabled", True):
        return

    # Check if *any* breathing phase is enabled
    any_phase_enabled = any(
        config.get(f"{p['key']}_enabled", p['default_enabled']) for p in PHASES
    )
    if not any_phase_enabled:
        tooltip("呼吸训练已跳过 (无启用阶段)。", period=3000)
        print("Skipping breathing dialog: No phases enabled.")
        return

    # Get configured number of cycles using our config system
    target_cycles = config.get("breathing_cycles", DEFAULT_BREATHING_CYCLES)
    if target_cycles <= 0:
        tooltip("呼吸训练已跳过 (循环次数为 0)。", period=3000)
        print(f"Skipping breathing dialog: Target cycles is {target_cycles}.")
        return

    # Ensure main window is visible before showing modal dialog
    if mw and mw.isVisible():
        print(f"Showing breathing dialog for {target_cycles} cycles.")
        # Pass target_cycles to the dialog
        dialog = BreathingDialog(target_cycles, mw)
        result = dialog.exec() # Show modally
        if result == QDialog.DialogCode.Accepted:
            print("Breathing exercise completed.")
            tooltip("呼吸训练完成！", period=2000) # "Breathing exercise complete!"
        else:
            print("Breathing exercise skipped or closed.")
            tooltip("呼吸训练已跳过。", period=2000) # "Breathing exercise skipped."
    else:
        print("Skipping breathing dialog: Main window not visible.")
