import time
from typing import Callable, Optional

from aqt import QTimer, mw
from aqt.utils import tooltip

from ..config.constants import AnkiStates
from ..state import get_app_state
from ..translator import _
from .timer_manager import TimerManager, TimerState
from .ui_updater import UiUpdater


class PomodoroManager:
    """协调 TimerManager, UiUpdater 和 AppState 来实现番茄钟功能。"""

    def __init__(self):
        self.app_state = get_app_state()
        self.timer_manager = TimerManager(mw)
        self.ui_updater = UiUpdater()

        # Callbacks
        self.on_pomodoro_finished_callback: Optional[Callable[[], None]] = None

        # 连接计时器事件
        self.timer_manager.on_tick = self.on_timer_tick
        self.timer_manager.on_finish = self.on_timer_finish

        self._max_break_timer: Optional[QTimer] = None
        self._init_max_break_timer()

        # 在 AppState 中注册此实例
        self.app_state.pomodoro_manager = self

    def on_timer_tick(self):
        """处理计时器的每个“滴答”"""
        # 更新UI
        self.ui_updater.update(self.timer_manager)

        # 如果正在工作，则更新每日总秒数
        if (
            self.timer_manager.state == TimerState.WORKING
            and mw
            and mw.state == AnkiStates.REVIEW
        ):
            current_daily_seconds = self.app_state.config.daily_pomodoro_seconds
            self.app_state.update_config_value(
                "daily_pomodoro_seconds", current_daily_seconds + 1
            )

    def on_timer_finish(self, finished_state: TimerState):
        """处理计时器完成事件"""
        if finished_state == TimerState.WORKING:
            tooltip(_("本次番茄钟结束"), period=3000)

            # 更新状态
            self.app_state.update_config_value("last_pomodoro_time", time.time())
            completed = self.app_state.config.completed_pomodoros + 1
            self.app_state.update_config_value("completed_pomodoros", completed)

            # 调用钩子函数
            if self.on_pomodoro_finished_callback:
                self.on_pomodoro_finished_callback()
        elif finished_state == TimerState.LONG_BREAK:
            # Long break finished, start max break countdown
            self.start_max_break_countdown(
                self.app_state.config.max_break_duration / 60
            )

        # 确保UI更新到空闲状态
        self.ui_updater.update(self.timer_manager)

    def start_pomodoro(self):
        """启动一个新的番茄钟"""
        config = self.app_state.config
        if not config.enabled:
            tooltip(_("番茄钟计时器已被禁用。"), period=3000)
            return

        if config.pomodoro_minutes <= 0:
            tooltip(
                f"无效的番茄钟时长: {config.pomodoro_minutes} 分钟。计时器未启动。",
                period=3000,
            )
            return

        self._check_long_idle_period()
        self.timer_manager.start(config.pomodoro_minutes, TimerState.WORKING)
        tooltip(
            _("番茄钟计时器已启动，时长: {} 分钟。").format(config.pomodoro_minutes),
            period=3000,
        )

    def stop_pomodoro(self):
        """停止当前的番茄钟"""
        self.timer_manager.stop()
        tooltip(_("番茄钟计时器已停止。"), period=3000)
        self.cleanup()

    def start_long_break(self):
        """开始一个长休息时段"""
        config = self.app_state.config
        duration = config.long_break_minutes
        state = TimerState.LONG_BREAK

        self.timer_manager.start(duration, state)

    def _check_long_idle_period(self):
        """检查长时间空闲并重置连胜"""
        config = self.app_state.config
        current_time = time.time()
        if (
            config.last_pomodoro_time > 0
            and (current_time - config.last_pomodoro_time) > config.max_break_duration
        ):
            self.app_state.update_config_value("completed_pomodoros", 0)
            tooltip(_("检测到长时间空闲，连胜中断。"), period=3000)

    def cleanup(self):
        """清理所有资源"""
        self.ui_updater.cleanup()
        self.stop_max_break_countdown()

    def _init_max_break_timer(self):
        """初始化最长休息时间计时器"""
        if self._max_break_timer is None:
            self._max_break_timer = QTimer(mw)
            self._max_break_timer.setSingleShot(True)
            self._max_break_timer.timeout.connect(self._on_max_break_timeout)

    def start_max_break_countdown(self, duration_minutes: float):
        """启动最长休息时间倒计时"""
        self.stop_max_break_countdown()  # Stop any existing timer
        if self._max_break_timer:
            # Start the main timer for UI updates
            self.timer_manager.start(duration_minutes, TimerState.MAX_BREAK_COUNTDOWN)
            # Start the single-shot timer for timeout event
            self._max_break_timer.start(int(duration_minutes * 60 * 1000))

    def stop_max_break_countdown(self):
        """停止最长休息时间倒计时"""
        if self._max_break_timer and self._max_break_timer.isActive():
            self._max_break_timer.stop()
        # Also stop the main timer and reset its state
        self.timer_manager.stop()
        self.timer_manager.state = TimerState.IDLE  # Ensure state is IDLE
        self.ui_updater.update(self.timer_manager)  # Update UI immediately

    def _on_max_break_timeout(self):
        """最长休息时间倒计时结束时的处理"""
        tooltip(_("休息时间过长，番茄钟连胜已清空。"), period=3000)
        self.app_state.update_config_value("completed_pomodoros", 0)
        self.timer_manager.stop()  # Stop current break timer
        self.timer_manager.state = TimerState.IDLE  # Ensure state is IDLE
        self.ui_updater.update(self.timer_manager)  # Update UI immediately
