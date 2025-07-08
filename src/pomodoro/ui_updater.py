from aqt import QWidget

from ..config import AppConfig
from ..config.constants import Defaults
from ..config.enums import StatusBarFormat
from ..state import get_app_state
from ..ui.CircularTimer import (
    BaseCircularTimer,
    get_timer_class,
    setup_circular_timer,
)
from ..ui.statusbar import show_timer_in_statusbar
from .timer_manager import TimerManager, TimerState


class UiUpdater:
    """负责更新所有与计时器相关的UI元素。"""

    def __init__(self):
        self.circular_timer: BaseCircularTimer | None = None
        self._setup_circular_timer_if_needed()

    def _setup_circular_timer_if_needed(self):
        """如果需要，则创建圆形计时器。"""
        config = get_app_state().config
        if config.show_circular_timer:
            parent_widget = (
                self.circular_timer.parent() if self.circular_timer else None
            )
            if not self.circular_timer or (
                isinstance(parent_widget, QWidget) and not parent_widget.isVisible()
            ):
                # 从配置中获取计时器样式
                circular_timer_style = config.circular_timer_style
                # 获取对应的计时器类
                timer_class = get_timer_class(circular_timer_style)
                # 使用通用的setup函数创建计时器
                new_timer = setup_circular_timer(timer_class)
                if new_timer:
                    self.circular_timer = new_timer
        elif self.circular_timer:
            parent_widget = self.circular_timer.parent()
            if isinstance(parent_widget, QWidget):
                parent_widget.close()
            self.circular_timer = None

    def update(self, timer_manager: TimerManager):
        """根据 TimerManager 的状态更新所有UI组件。"""
        app_state = get_app_state()

        # 更新状态栏
        label = app_state.timer_label
        if label:
            status_text = self._get_statusbar_text(timer_manager, app_state.config)
            label.setText(status_text)
            show_timer_in_statusbar(True)
        else:
            # 确保在需要时创建标签
            show_timer_in_statusbar(True)
            if app_state.timer_label:
                status_text = self._get_statusbar_text(timer_manager, app_state.config)
                app_state.timer_label.setText(status_text)

        # 更新圆形计时器
        self._update_circular_timer_progress(timer_manager)

    def _get_statusbar_text(
        self, timer_manager: TimerManager, config: AppConfig
    ) -> str:
        """生成状态栏标签的文本。"""
        # 获取显示数据
        icon, mins, secs, progress, daily_mins, daily_secs = (
            self._get_timer_display_data(timer_manager, config)
        )
        completed = config.completed_pomodoros
        target = max(1, config.pomodoros_before_long_break)

        # 获取状态栏格式字符串
        statusbar_format = config.statusbar_format

        # 根据格式字符串动态生成显示内容
        try:
            return statusbar_format.format(
                icon=icon,
                mins=mins,
                secs=secs,
                progress=progress,
                daily_mins=daily_mins,
                daily_secs=daily_secs,
                completed=completed,
                target=target,
            )
        except KeyError as e:
            print(
                f"Warning: Status bar format '{statusbar_format}' caused KeyError: {e}."
                "Falling back to default."
            )
            return StatusBarFormat.ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME.format(
                icon=icon,
                mins=mins,
                secs=secs,
                progress=progress,
                daily_mins=daily_mins,
                daily_secs=daily_secs,
                completed=completed,
                target=target,
            )

    def _get_timer_display_data(
        self, timer_manager: TimerManager, config: AppConfig
    ) -> tuple[str, int, int, str, int, int]:
        """获取计时器显示数据。"""
        completed = config.completed_pomodoros
        target = max(1, config.pomodoros_before_long_break)
        completed_display = completed % target
        progress = (
            Defaults.StatusBar.FILLED_TOMATO * completed_display
            + Defaults.StatusBar.EMPTY_TOMATO * (target - completed_display)
        )

        daily_total_seconds = config.daily_pomodoro_seconds
        daily_mins, daily_secs = divmod(daily_total_seconds, 60)

        match timer_manager.state:
            case TimerState.LONG_BREAK:
                icon = Defaults.StatusBar.BREAK_WARNING
                mins, secs = divmod(timer_manager.remaining_seconds, 60)
            case TimerState.MAX_BREAK_COUNTDOWN:
                icon = Defaults.StatusBar.MAX_BREAK_WARNING
                mins, secs = divmod(timer_manager.remaining_seconds, 60)
            case TimerState.WORKING:
                icon = Defaults.StatusBar.FILLED_TOMATO
                mins, secs = divmod(timer_manager.remaining_seconds, 60)
            case TimerState.IDLE | _:
                icon = Defaults.StatusBar.EMPTY_TOMATO
                mins, secs = divmod(int(config.pomodoro_minutes * 60), 60)

        return icon, mins, secs, progress, daily_mins, daily_secs

    def _update_circular_timer_progress(self, timer_manager: TimerManager):
        """更新圆形计时器的进度。"""
        if not self.circular_timer:
            return

        match timer_manager.state:
            case (
                TimerState.WORKING
                | TimerState.LONG_BREAK
                | TimerState.MAX_BREAK_COUNTDOWN
            ):
                self.circular_timer.set_progress(
                    timer_manager.remaining_seconds, timer_manager.total_seconds
                )
            case _:  # 空闲或完成
                self.circular_timer.set_progress(0, 1)

    def cleanup(self):
        """清理所有UI资源。"""
        if self.circular_timer:
            parent = self.circular_timer.parent()
            if parent and isinstance(parent, QWidget):
                parent.close()
            self.circular_timer = None
