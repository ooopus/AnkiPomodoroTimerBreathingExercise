import time
from aqt import mw
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget
from .timer_utils import set_pomodoro_timer, get_timer_label

from .ui.circular_timer import setup_circular_timer


class PomodoroTimer(QTimer):
    def __init__(self, parent=None):
        from .config import get_config

        super().__init__(parent)
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.remaining_break_seconds = 0
        self.break_timer = QTimer(self)
        self.break_timer.timeout.connect(self._update_break_time)
        self.timeout.connect(self.update_timer)
        set_pomodoro_timer(self)
        self.circular_timer = None
        self.config = get_config()

    def start_timer(self, minutes):
        """Starts the Pomodoro timer for the given number of minutes."""
        from .ui import show_timer_in_statusbar
        from .config import get_config, save_config

        config = get_config()

        if not config.get("enabled", True):
            print("Pomodoro timer disabled in config.")
            return
        if minutes <= 0:
            print(f"Invalid Pomodoro duration: {minutes} minutes. Timer not started.")
            return

        # Check for long idle period before starting new Pomodoro
        current_time = time.time()
        last_pomodoro_time = config.get("last_pomodoro_time", 0)
        max_break_duration = config.get("max_break_duration", 30 * 60)

        if (
            last_pomodoro_time
            and (current_time - last_pomodoro_time) > max_break_duration
        ):
            config["completed_pomodoros"] = 0
            save_config()
            print("Long idle period detected. Pomodoro count reset.")

        # 处理圆形计时器的显示逻辑
        if config.get("show_circular_timer", True):
            # 如果计时器不存在或其父窗口已被关闭，则创建新的计时器
            parent_widget = (
                self.circular_timer.parent() if self.circular_timer else None
            )
            if not self.circular_timer or (
                isinstance(parent_widget, QWidget) and not parent_widget.isVisible()
            ):
                self.circular_timer = setup_circular_timer()
        elif self.circular_timer:
            parent_widget = self.circular_timer.parent()
            if isinstance(parent_widget, QWidget):
                parent_widget.close()
            self.circular_timer = None

        self.total_seconds = minutes * 60
        self.remaining_seconds = self.total_seconds
        print(f"Pomodoro timer started for {minutes} minutes.")
        self.update_display()
        self.start(1000)  # Tick every second
        show_timer_in_statusbar(config.get("statusbar_format", True))

    def stop_timer(self, stop_break_timer=False):
        """Stops the Pomodoro timer and resets the display.
        Args:
            stop_break_timer (bool): 是否同时停止休息计时器
        """
        if self.isActive():
            print("Pomodoro timer stopped.")
            self.stop()
            if stop_break_timer:
                self.break_timer.stop()

        # 确保在主线程执行UI更新
        def _clear_display():
            self.remaining_seconds = 0
            self.total_seconds = 0
            self.update_display()
            if self.circular_timer:
                self.circular_timer.set_progress(0, 1)

        mw.progress.timer(10, _clear_display, False)

    def _update_break_time(self):
        """更新休息时间"""
        if self.remaining_break_seconds > 0:
            self.remaining_break_seconds -= 1
            self.update_display()
        else:
            self.stop_break_timer()

    def stop_break_timer(self):
        """停止休息时间计时器"""
        if self.break_timer.isActive():
            print("Break timer stopped.")
            self.break_timer.stop()
            # 强制立即更新显示
            mw.progress.timer(10, lambda: self.update_display(), False)
            self.update_display()  # 更新显示以清除休息时间

    def update_timer(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            # 更新当天番茄钟总计时长
            self.config["daily_pomodoro_seconds"] = (
                self.config.get("daily_pomodoro_seconds", 0) + 1
            )
            self.update_display()
        else:
            from .hooks import on_pomodoro_finished

            print("Pomodoro timer finished.")
            self.stop()

            # 设置最后完成时间并启动休息计时器
            current_time = time.time()
            self.config["last_pomodoro_time"] = current_time
            max_break_duration = self.config.get("max_break_duration", 30 * 60)
            self.remaining_break_seconds = max_break_duration
            self.break_timer.start(1000)

            on_pomodoro_finished()

    def update_display(self):
        def _update():
            from .ui import show_timer_in_statusbar
            from .config import save_config
            from .constants import (
                STATUSBAR_FILLED_TOMATO,
                STATUSBAR_EMPTY_TOMATO,
                STATUSBAR_BREAK_WARNING,
                STATUSBAR_FORMATS,
            )

            label = get_timer_label()
            if label:
                # 构建进度显示
                completed = self.config.get("completed_pomodoros", 0)
                target = self.config.get("pomodoros_before_long_break", 4)
                progress = (
                    STATUSBAR_FILLED_TOMATO * completed
                    + STATUSBAR_EMPTY_TOMATO * (target - completed)
                )

                # 获取休息时间信息
                break_mins, break_secs = divmod(self.remaining_break_seconds, 60)

                # 初始化每日计时变量
                daily_mins, daily_secs = 0, 0

                # 检查是否需要重置每日计时
                last_date = self.config.get("last_date", "")
                today = time.strftime("%Y-%m-%d")
                if last_date != today:
                    self.config["daily_pomodoro_seconds"] = 0
                    self.config["last_date"] = today
                    save_config()
                    
                # 无论是否重置，都计算每日时间
                daily_total_seconds = self.config.get("daily_pomodoro_seconds", 0)
                daily_mins, daily_secs = divmod(daily_total_seconds, 60)

                # 根据配置中的状态栏格式显示信息
                statusbar_format = self.config.get(
                    "statusbar_format", "ICON_TIME_PROGRESS_WITH_TOTAL_TIME"
                )
                format_str = getattr(
                    STATUSBAR_FORMATS,
                    statusbar_format,
                    STATUSBAR_FORMATS.ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME,
                )

                # 根据计时器状态设置不同的图标
                if self.break_timer.isActive() and self.remaining_break_seconds > 0:
                    icon = STATUSBAR_BREAK_WARNING
                    mins, secs = break_mins, break_secs
                elif self.remaining_seconds > 0:
                    icon = STATUSBAR_FILLED_TOMATO
                    mins, secs = divmod(self.remaining_seconds, 60)
                else:
                    icon = STATUSBAR_EMPTY_TOMATO
                    mins, secs = 0, 0

                # 根据格式字符串动态生成显示内容
                try:
                    label.setText(
                        format_str.format(
                            icon=icon,
                            mins=mins,
                            secs=secs,
                            progress=progress,
                            daily_mins=daily_mins,
                            daily_secs=daily_secs,
                        )
                    )
                except KeyError:
                    # 如果格式字符串中有不支持的变量，使用默认格式
                    label.setText(
                        STATUSBAR_FORMATS.ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME.format(
                            icon=icon,
                            mins=mins,
                            secs=secs,
                            progress=progress,
                            daily_mins=daily_mins,
                            daily_secs=daily_secs,
                        )
                    )

                show_timer_in_statusbar(True)

            # 更新圆形计时器
            if self.circular_timer:
                if self.remaining_seconds > 0:
                    self.circular_timer.set_progress(
                        self.remaining_seconds, self.total_seconds
                    )
                elif self.break_timer.isActive() and self.remaining_break_seconds > 0:
                    max_break_duration = self.config.get(
                        "max_break_duration", 1
                    )  # Avoid division by zero
                    if max_break_duration > 0:  # Ensure max_break_duration is positive
                        self.circular_timer.set_progress(
                            self.remaining_break_seconds, max_break_duration
                        )
                    else:
                        self.circular_timer.set_progress(
                            0, 1
                        )  # Handle zero/negative case
                else:
                    self.circular_timer.set_progress(0, 1)  # Reset when idle

        # 确保在主线程执行UI更新
        mw.progress.timer(10, _update, False)
