from anki.cards import Card
from aqt import QTimer, mw
from aqt.utils import tooltip

from .breathing import start_breathing_exercise
from .config import save_config
from .config.constants import AnkiStates
from .config.enums import PHASES
from .pomodoro.pomodoro_manager import PomodoroManager
from .pomodoro.timer_manager import TimerState
from .state import get_app_state, get_config, get_pomodoro_manager, set_pomodoro_manager
from .translator import _

# --- Anki 钩子函数 ---


def on_reviewer_did_start(card: Card):
    """Starts the Pomodoro timer when the reviewer screen is shown."""
    config = get_config()
    pomodoro_manager = get_pomodoro_manager()

    if not config.enabled:
        return

    # If Anki is in review state
    if mw.state == AnkiStates.REVIEW:
        if pomodoro_manager is None:
            pomodoro_manager = PomodoroManager()
            set_pomodoro_manager(pomodoro_manager)
            # Set the callback for when a pomodoro finishes
            pomodoro_manager.on_pomodoro_finished_callback = on_pomodoro_finished

        # If currently in a break, stop it and start a new pomodoro
        match pomodoro_manager.timer_manager.state:
            case TimerState.LONG_BREAK | TimerState.MAX_BREAK_COUNTDOWN:
                pomodoro_manager.stop_max_break_countdown()
                mw.progress.single_shot(100, pomodoro_manager.start_pomodoro, False)
            case TimerState.IDLE:
                mw.progress.single_shot(100, pomodoro_manager.start_pomodoro, False)
            case TimerState.WORKING:
                pass


def on_state_did_change(new_state: str, old_state: str):
    """管理状态变更时的Pomodoro计时器和休息状态"""
    pomodoro_manager = get_pomodoro_manager()
    config = get_config()

    # 离开复习状态时保存休息进度
    if (
        not config.work_across_decks
        and old_state == AnkiStates.REVIEW
        and new_state != AnkiStates.REVIEW
        and pomodoro_manager
        and config.enabled
        and pomodoro_manager.timer_manager.state == TimerState.WORKING
    ):
        # 停止工作番茄钟计时器
        pomodoro_manager.timer_manager.stop()
        tooltip(_("番茄钟计时器已停止。"), period=3000)

        # 启动最长休息时间倒计时
        # config.max_break_duration 是秒，start_max_break_countdown 期望分钟
        pomodoro_manager.start_max_break_countdown(config.max_break_duration / 60)


def on_pomodoro_finished():
    """番茄钟完成时的处理函数"""
    config = get_config()
    app_state = get_app_state()

    target = config.pomodoros_before_long_break

    # 根据完成数量显示不同提示
    if config.completed_pomodoros >= target:
        long_break_mins = config.long_break_minutes
        tooltip(
            _("恭喜完成{target}个番茄钟！建议休息{minutes}分钟。").format(
                target=target, minutes=long_break_mins
            ),
            period=5000,
        )
        config.completed_pomodoros = 0
        app_state.pending_break_type = True  # True to start a long break
        tooltip(_("番茄钟时间到！"), period=3000)

    save_config(config)

    mw.progress.single_shot(100, lambda: _after_pomodoro_finish_tasks(), False)


def on_theme_change():
    """
    当Anki的主题（白天/夜间模式）改变时调用。
    这个函数会找到活动的计时器实例并更新其颜色。
    """
    pomodoro_manager = get_pomodoro_manager()
    if (
        pomodoro_manager
        and pomodoro_manager.ui_updater.circular_timer
        and hasattr(pomodoro_manager.ui_updater.circular_timer, "update_theme_colors")
    ):
        timer_widget = pomodoro_manager.ui_updater.circular_timer
        timer_widget.update_theme_colors()


def _after_pomodoro_finish_tasks():
    """Actions to perform after the Pomodoro finishes (runs on main thread)."""
    if mw.state == AnkiStates.REVIEW.value:
        mw.moveToState(AnkiStates.DECK_BROWSER.value)
    QTimer.singleShot(200, _start_breathing_and_break)


def show_breathing_dialog():
    """Checks config and shows the breathing exercise if appropriate."""
    config = get_config()
    if not config.enabled:
        return

    any_phase_enabled = any(
        getattr(config, f"{p.key}_enabled", p.default_enabled) for p in PHASES
    )
    if not any_phase_enabled:
        tooltip(_("呼吸训练已跳过 (无启用阶段)。"), period=3000)
        return

    target_cycles = config.breathing_cycles
    if target_cycles <= 0:
        tooltip(_("呼吸训练已跳过 (循环次数为 0)。"), period=3000)
        return

    if mw and mw.isVisible():
        result = start_breathing_exercise(target_cycles, mw)
        if result:
            tooltip(_("呼吸训练完成！"), period=2000)
        else:
            tooltip(_("呼吸训练已跳过。"), period=2000)
    else:
        tooltip(_("跳过呼吸训练 (主窗口不可见)。"), period=2000)


def _start_breathing_and_break():
    """
    Starts breathing exercise and then the appropriate break or max break countdown.
    """
    config = get_config()
    app_state = get_app_state()
    pomodoro_manager = get_pomodoro_manager()

    # Always show breathing dialog
    show_breathing_dialog()  # This is a blocking call

    # After breathing, start the pending break or max break countdown
    if pomodoro_manager and app_state.pending_break_type:
        pomodoro_manager.start_long_break()
        app_state.pending_break_type = False

        pomodoro_manager.ui_updater.update(pomodoro_manager.timer_manager)
    elif pomodoro_manager:
        pomodoro_manager.start_max_break_countdown(config.max_break_duration / 60)
