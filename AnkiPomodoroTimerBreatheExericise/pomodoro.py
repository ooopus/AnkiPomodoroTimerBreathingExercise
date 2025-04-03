import time
from aqt import mw
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget
from .timer_utils import set_pomodoro_timer, get_timer_label

from .ui.circular_timer import setup_circular_timer

import gettext
import os
localedir = os.path.join(os.path.dirname(__file__), './locales')
translation = gettext.translation('messages', localedir, fallback=True)
_ = translation.gettext

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
            from aqt.utils import tooltip

            tooltip(_("番茄钟计时器已被禁用。"), period=3000)
            return
        if minutes <= 0:
            from aqt.utils import tooltip

            tooltip(f"无效的番茄钟时长: {minutes} 分钟。计时器未启动。", period=3000)
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
            from aqt.utils import tooltip

            tooltip(_("检测到长时间空闲，连胜中断。"), period=3000)

        # Handle circular timer display logic
        if config.get("show_circular_timer", True):
            # Create new timer if it doesn't exist or its parent window is closed
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
        from aqt.utils import tooltip

        tooltip(f"番茄钟计时器已启动，时长: {minutes} 分钟。", period=3000)
        self.update_display()
        self.start(1000)  # Tick every second
        show_timer_in_statusbar(config.get("statusbar_format", True))

    def stop_timer(self, stop_break_timer=False):
        """Stops the Pomodoro timer and resets the display."""
        if self.isActive():
            from aqt.utils import tooltip

            tooltip(_("番茄钟计时器已停止。"), period=3000)
            self.stop()

            if stop_break_timer:
                self.break_timer.stop()

        # Ensure UI updates run in main thread
        def _clear_display():
            if self.circular_timer:
                parent = self.circular_timer.parent()
                if parent and isinstance(parent, QWidget):
                    parent.close()
                self.circular_timer.setParent(None)  # Need to remove parent-child relationship
                self.circular_timer.deleteLater()
                self.circular_timer = None

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
            from aqt.utils import tooltip

            tooltip(_("连胜中断"), period=3000)
            self.break_timer.stop()
            # Force immediate display update
            mw.progress.timer(10, lambda: self.update_display(), False)
            self.update_display()  # Update display to clear break time

    def update_timer(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1

            self.update_display()

            # Update total pomodoro time for today
            if mw and mw.state == "review":
                self.config["daily_pomodoro_seconds"] = (
                    self.config.get("daily_pomodoro_seconds", 0) + 1
                )
        else:
            from .hooks import on_pomodoro_finished

            from aqt.utils import tooltip

            tooltip(_("本次番茄钟结束"), period=3000)
            self.stop()

            # Set last completion time and start break timer
            current_time = time.time()
            self.config["last_pomodoro_time"] = current_time
            max_break_duration = self.config.get("max_break_duration", 30 * 60)
            self.remaining_break_seconds = max_break_duration
            self.break_timer.start(1000)

            # Update display immediately
            self.update_display()
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
                # Build progress display
                completed = self.config.get("completed_pomodoros", 0)
                target = self.config.get("pomodoros_before_long_break", 4)
                progress = (
                    STATUSBAR_FILLED_TOMATO * completed
                    + STATUSBAR_EMPTY_TOMATO * (target - completed)
                )

                # Get break time information
                break_mins, break_secs = divmod(self.remaining_break_seconds, 60)

                # Initialize daily timer variables
                daily_mins, daily_secs = 0, 0

                # Check if daily timer needs reset
                last_date = self.config.get("last_date", "")
                today = time.strftime("%Y-%m-%d")
                if last_date != today:
                    self.config["daily_pomodoro_seconds"] = 0
                    self.config["last_date"] = today
                    save_config()

                # Calculate daily time regardless of reset
                daily_total_seconds = self.config.get("daily_pomodoro_seconds", 0)
                daily_mins, daily_secs = divmod(daily_total_seconds, 60)

                # Display information according to status bar format in config
                statusbar_format = self.config.get(
                    "statusbar_format", "ICON_TIME_PROGRESS_WITH_TOTAL_TIME"
                )
                format_str = getattr(
                    STATUSBAR_FORMATS,
                    statusbar_format,
                    STATUSBAR_FORMATS.ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME,
                )

                # Set different icons based on timer state
                if self.break_timer.isActive() and self.remaining_break_seconds > 0:
                    icon = STATUSBAR_BREAK_WARNING
                    mins, secs = break_mins, break_secs
                elif self.remaining_seconds > 0:
                    icon = STATUSBAR_FILLED_TOMATO
                    mins, secs = divmod(self.remaining_seconds, 60)
                else:
                    icon = STATUSBAR_EMPTY_TOMATO
                    mins, secs = 0, 0

                # Dynamically generate display content based on format string
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
                    # Use default format if unsupported variables in format string
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

            # Update circular timer
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

        # Ensure UI updates run in main thread
        mw.progress.timer(10, _update, False)
