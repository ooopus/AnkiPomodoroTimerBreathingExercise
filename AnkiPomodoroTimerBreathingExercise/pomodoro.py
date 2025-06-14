import time
from enum import Enum, auto
from typing import Any, Optional

from aqt import QTimer, QWidget, mw
from aqt.utils import tooltip

from .constants import STATUSBAR_FORMATS, Defaults
from .state import AppState, get_app_state
from .translator import _
from .ui import show_timer_in_statusbar
from .ui.circular_timer import setupCircularTimer


class TimerState(Enum):
    """番茄钟计时器的状态枚举"""

    IDLE = auto()  # 空闲状态
    WORKING = auto()  # 工作状态
    BREAK = auto()  # 休息状态


class PomodoroTimer(QTimer):
    """番茄钟计时器类

    负责管理番茄工作法的计时功能，包括工作时间和休息时间的计时，
    以及相关状态的更新和显示。
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """初始化番茄钟计时器

        Args:
            parent: 父级QWidget对象
        """
        super().__init__(parent)
        # 计时相关属性
        self.remaining_seconds: int = 0
        self.total_seconds: int = 0
        self.remaining_break_seconds: int = 0

        # 休息计时器
        self.break_timer: QTimer = QTimer(self)
        self.break_timer.timeout.connect(self._update_break_time)

        # 主计时器超时连接
        self.timeout.connect(self._on_timer_timeout)

        # 获取应用状态并注册计时器
        app_state = get_app_state()
        app_state.pomodoro_timer = self

        # 圆形计时器UI组件
        self.circular_timer = None

        # 当前计时器状态
        self._state: TimerState = TimerState.IDLE

    @property
    def state(self) -> TimerState:
        """获取当前计时器状态"""
        return self._state

    @state.setter
    def state(self, new_state: TimerState) -> None:
        """设置计时器状态并触发相应操作

        Args:
            new_state: 新的计时器状态
        """
        self._state = new_state
        self.update_display()  # 状态变化时更新显示

    def start_timer(self, minutes: int) -> None:
        """启动番茄钟计时器

        Args:
            minutes: 计时时长（分钟）
        """
        app_state = get_app_state()
        config = app_state.config

        # 检查计时器是否启用
        if not self._check_timer_enabled(config):
            return

        # 检查时长是否有效
        if not self._validate_timer_duration(minutes):
            return

        # 检查长时间空闲
        self._check_long_idle_period(config)

        # 处理圆形计时器显示
        self._setup_circular_timer(config)

        # 设置计时时长并启动
        self.total_seconds = minutes * 60
        self.remaining_seconds = self.total_seconds

        tooltip(_("番茄钟计时器已启动，时长: {} 分钟。").format(minutes), period=3000)
        self.update_display()
        self.start(1000)  # 每秒触发一次
        self.state = TimerState.WORKING

        # 显示状态栏计时器
        show_timer_in_statusbar(config.get("statusbar_format", True))

    def _check_timer_enabled(self, config: dict[str, Any]) -> bool:
        """检查计时器是否启用

        Args:
            config: 配置字典

        Returns:
            计时器是否启用
        """
        if not config.get("enabled", True):
            tooltip(_("番茄钟计时器已被禁用。"), period=3000)
            return False
        return True

    def _validate_timer_duration(self, minutes: int) -> bool:
        """验证计时器时长是否有效

        Args:
            minutes: 计时时长（分钟）

        Returns:
            时长是否有效
        """
        if minutes <= 0:
            tooltip(f"无效的番茄钟时长: {minutes} 分钟。计时器未启动。", period=3000)
            return False
        return True

    def _check_long_idle_period(self, config: dict[str, Any]) -> None:
        """检查长时间空闲并重置连胜

        Args:
            config: 配置字典
        """
        current_time = time.time()
        last_pomodoro_time = config.get("last_pomodoro_time", 0)
        max_break_duration = config.get("max_break_duration", 30 * 60)

        if (
            last_pomodoro_time > 0
            and (current_time - last_pomodoro_time) > max_break_duration
        ):
            app_state = get_app_state()
            app_state.update_config_value("completed_pomodoros", 0)
            tooltip(_("检测到长时间空闲，连胜中断。"), period=3000)

    def _setup_circular_timer(self, config: dict[str, Any]) -> None:
        """设置圆形计时器

        Args:
            config: 配置字典
        """
        if config.get("show_circular_timer", True):
            # 如果计时器不存在或父窗口已关闭，则创建新计时器
            parent_widget = (
                self.circular_timer.parent() if self.circular_timer else None
            )
            if not self.circular_timer or (
                isinstance(parent_widget, QWidget) and not parent_widget.isVisible()
            ):
                self.circular_timer = setupCircularTimer()
        elif self.circular_timer:
            # 如果设置为不显示但计时器存在，则关闭计时器
            parent_widget = self.circular_timer.parent()
            if isinstance(parent_widget, QWidget):
                parent_widget.close()
            self.circular_timer = None

    def stop_timer(self) -> None:
        """停止番茄钟计时器并重置显示"""
        if self.isActive():
            tooltip(_("番茄钟计时器已停止。"), period=3000)
            self.stop()
            self.state = TimerState.IDLE

        # 确保UI更新在主线程中运行
        mw.progress.single_shot(10, self.cleanup, False)

    def cleanup(self) -> None:
        """清理所有计时器资源"""
        # 清理圆形计时器
        if self.circular_timer:
            parent = self.circular_timer.parent()
            if parent and isinstance(parent, QWidget):
                parent.close()
            self.circular_timer.setParent(None)
            self.circular_timer.deleteLater()
            self.circular_timer = None

        # 确保休息计时器停止
        if self.break_timer.isActive():
            self.break_timer.stop()

        # 更新状态栏显示
        self.update_display()

    def _update_break_time(self) -> None:
        """更新休息时间"""
        if self.remaining_break_seconds > 0:
            self.remaining_break_seconds -= 1
            self.update_display()
        else:
            self.stop_break_timer(reset_streak=True)

    def start_break_timer(self, seconds: int):
        """Start break timer that will reset streak if it expires"""
        self.remaining_break_seconds = seconds
        self.break_timer.start(1000)
        self.state = TimerState.BREAK

    def stop_break_timer(self, reset_streak=False) -> None:
        """停止休息时间计时器"""
        if self.break_timer.isActive():
            self.break_timer.stop()
            self.remaining_break_seconds = 0  # 显式重置休息秒数

            if reset_streak:
                app_state = get_app_state()
                tooltip(_("连胜中断"), period=3000)
                app_state.update_config_value(
                    "completed_pomodoros", 0
                )  # 休息中断时重置连胜

            # 强制立即更新显示
            self.state = TimerState.IDLE
            self.update_display()  # 更新显示以清除休息时间

    def _on_timer_timeout(self) -> None:
        """计时器超时处理函数"""
        app_state = get_app_state()
        if self.remaining_seconds > 0:
            self._handle_active_timer(app_state)
        else:
            self._handle_timer_finished(app_state)

    def _handle_active_timer(self, app_state: AppState) -> None:
        """处理活动计时器的更新

        Args:
            app_state: 应用状态对象
        """
        self.remaining_seconds -= 1

        # 仅在复习状态下更新今日番茄钟总时间
        if mw and mw.state == "review":
            current_daily_seconds = app_state.config.get("daily_pomodoro_seconds", 0)
            app_state.update_config_value(
                "daily_pomodoro_seconds", current_daily_seconds + 1
            )

        self.update_display()  # 每秒更新显示

    def _handle_timer_finished(self, app_state: AppState) -> None:
        """处理计时器完成事件

        Args:
            app_state: 应用状态对象
        """
        from .hooks import on_pomodoro_finished

        tooltip(_("本次番茄钟结束"), period=3000)
        self.stop()

        # 通过AppState设置最后完成时间并启动休息计时器
        current_time = time.time()
        app_state.update_config_value("last_pomodoro_time", current_time)
        max_break_duration = app_state.config.get("max_break_duration", 30 * 60)
        self.remaining_break_seconds = max_break_duration
        self.break_timer.start(1000)
        self.state = TimerState.BREAK

        # 番茄钟完成后立即更新显示
        self.update_display()
        on_pomodoro_finished()  # 状态更新后调用钩子

    def _check_and_reset_daily_timer(self, app_state: AppState) -> None:
        """检查日期是否已更改，如有必要则重置每日计时器

        Args:
            app_state: 应用状态对象
        """
        config = app_state.config
        last_date = config.get("last_date", "")
        today = time.strftime("%Y-%m-%d")
        if last_date != today:
            app_state.update_config_value("daily_pomodoro_seconds", 0)
            app_state.update_config_value("last_date", today)
            # Note: completed_pomodoros is preserved across days
            # to maintain streak count

    def _get_timer_display_data(
        self, config: dict[str, Any]
    ) -> tuple[str, int, int, str, int, int]:
        """获取计时器显示数据

        Args:
            config: 配置字典

        Returns:
            图标、分钟、秒数、进度显示、每日分钟、每日秒数的元组
        """
        # 构建进度显示
        completed = config.get("completed_pomodoros", 0)
        target = config.get("pomodoros_before_long_break", 4)
        # 确保目标至少为1，以避免被零或负数取模
        target = max(1, target)

        # 处理完成周期：如果完成计数达到目标，则重置完成计数
        completed_display = completed % target
        progress = (
            Defaults.StatusBar.FILLED_TOMATO * completed_display
            + Defaults.StatusBar.EMPTY_TOMATO * (target - completed_display)
        )

        # 获取休息时间信息
        break_mins, break_secs = divmod(self.remaining_break_seconds, 60)

        # 获取每日时间信息
        daily_total_seconds = config.get("daily_pomodoro_seconds", 0)
        daily_mins, daily_secs = divmod(daily_total_seconds, 60)

        # 确定当前状态和图标
        if self.state == TimerState.BREAK:
            icon = Defaults.StatusBar.BREAK_WARNING
            mins, secs = break_mins, break_secs
        elif self.state == TimerState.WORKING:
            icon = Defaults.StatusBar.FILLED_TOMATO
            mins, secs = divmod(self.remaining_seconds, 60)
        else:  # 空闲状态
            icon = Defaults.StatusBar.EMPTY_TOMATO
            mins, secs = divmod(
                config.get("pomodoro_duration", 25) * 60, 60
            )  # 空闲时显示配置的时长
            # Use the same progress calculation for all states
            # progress variable is already set above

        return icon, mins, secs, progress, daily_mins, daily_secs

    def _get_statusbar_text(self, app_state: AppState) -> str:
        """生成状态栏标签的文本

        Args:
            app_state: 应用状态对象

        Returns:
            格式化的状态栏文本
        """
        config = app_state.config

        # 获取显示数据
        icon, mins, secs, progress, daily_mins, daily_secs = (
            self._get_timer_display_data(config)
        )
        completed = config.get("completed_pomodoros", 0)
        target = max(1, config.get("pomodoros_before_long_break", 4))

        # 获取状态栏格式字符串
        statusbar_format_key = config.get(
            "statusbar_format", "ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME"
        )
        format_str = getattr(
            STATUSBAR_FORMATS,
            statusbar_format_key,
            STATUSBAR_FORMATS.ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME,  # 默认格式
        )

        # 根据格式字符串动态生成显示内容
        try:
            return format_str.format(
                icon=icon,
                mins=mins,
                secs=secs,
                progress=progress,
                daily_mins=daily_mins,
                daily_secs=daily_secs,
                completed=completed,  # 添加总完成计数
                target=target,  # 添加目标计数
            )
        except KeyError as e:
            # 如果不支持的变量则回退到默认格式
            print(
                f"Warning: Status bar format '{statusbar_format_key}' "
                f"caused KeyError: {e}. Falling back to default."
            )
            return STATUSBAR_FORMATS.ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME.format(
                icon=icon,
                mins=mins,
                secs=secs,
                progress=progress,
                daily_mins=daily_mins,
                daily_secs=daily_secs,
                completed=completed,
                target=target,
            )

    def _update_circular_timer_progress(self, app_state: AppState) -> None:
        """更新圆形计时器的进度

        Args:
            app_state: 应用状态对象
        """
        if not self.circular_timer:
            return

        config = app_state.config
        if self.state == TimerState.WORKING:
            self.circular_timer.set_progress(self.remaining_seconds, self.total_seconds)
        elif self.state == TimerState.BREAK:
            max_break_duration = max(1, config.get("max_break_duration", 1))
            self.circular_timer.set_progress(
                self.remaining_break_seconds, max_break_duration
            )
        else:  # 空闲或完成
            self.circular_timer.set_progress(0, 1)  # 空闲/完成时重置

    def update_display(self) -> None:
        """更新状态栏和圆形计时器显示"""

        # 确保UI更新在主线程中运行，使用单个计时器事件
        if mw and mw.isVisible():  # 仅在主窗口可见时调度
            mw.progress.single_shot(10, self._update_ui, False)

    def _update_ui(self) -> None:
        """更新UI组件"""
        app_state = get_app_state()

        # 检查并在必要时重置每日计时器
        self._check_and_reset_daily_timer(app_state)

        # 更新状态栏标签
        label = app_state.timer_label
        if label:
            status_text = self._get_statusbar_text(app_state)
            label.setText(status_text)
            show_timer_in_statusbar(True)  # 如果标签存在，则保持状态栏可见
        else:
            show_timer_in_statusbar(False)  # 如果标签不存在，则隐藏

        # 更新圆形计时器
        self._update_circular_timer_progress(app_state)
