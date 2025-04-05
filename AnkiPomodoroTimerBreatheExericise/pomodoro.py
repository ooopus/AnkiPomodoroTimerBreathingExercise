import time
from aqt import mw, QTimer, QWidget
from .state import get_app_state

from .ui.circular_timer import setup_circular_timer
from .ui import show_timer_in_statusbar # Import show_timer_in_statusbar directly
from .constants import (
    STATUSBAR_FILLED_TOMATO,
    STATUSBAR_EMPTY_TOMATO,
    STATUSBAR_BREAK_WARNING,
    STATUSBAR_FORMATS,
)

from .translator import _


class PomodoroTimer(QTimer):
    def __init__(self, parent=None):

        super().__init__(parent)
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.remaining_break_seconds = 0
        self.break_timer = QTimer(self)
        self.break_timer.timeout.connect(self._update_break_time)
        self.timeout.connect(self.update_timer)
        app_state = get_app_state()
        app_state.pomodoro_timer = self 
        self.circular_timer = None

    def start_timer(self, minutes):
        """Starts the Pomodoro timer for the given number of minutes."""

        app_state = get_app_state()
        config = app_state.config # Use local var for config in this scope

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
            app_state.update_config_value("completed_pomodoros", 0) 
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

        tooltip(_("番茄钟计时器已启动，时长: {} 分钟。").format(minutes), period=3000)
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
                # Ensure proper cleanup
                self.circular_timer.setParent(None)
                self.circular_timer.deleteLater()
                self.circular_timer = None
                # Also update status bar when stopping completely
                self.update_display() 

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
            app_state = get_app_state() # Get state to update completion
            from aqt.utils import tooltip

            tooltip(_("连胜中断"), period=3000)
            self.break_timer.stop()
            self.remaining_break_seconds = 0 # Explicitly reset break seconds
            app_state.update_config_value("completed_pomodoros", 0) # Reset combo on break interrupt
            # Force immediate display update
            self.update_display()  # Update display to clear break time

    def update_timer(self):
        app_state = get_app_state()
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1

            # Update total pomodoro time for today via AppState only when reviewing
            if mw and mw.state == "review": 
                current_daily_seconds = app_state.config.get("daily_pomodoro_seconds", 0)
                app_state.update_config_value("daily_pomodoro_seconds", current_daily_seconds + 1)
            
            self.update_display() # Update display every second

        else:
            from .hooks import on_pomodoro_finished
            from aqt.utils import tooltip

            tooltip(_("本次番茄钟结束"), period=3000)
            self.stop()

            # Increment completed count first
            completed_count = app_state.config.get("completed_pomodoros", 0) + 1
            app_state.update_config_value("completed_pomodoros", completed_count)

            # Set last completion time and start break timer via AppState
            current_time = time.time()
            app_state.update_config_value("last_pomodoro_time", current_time)
            max_break_duration = app_state.config.get("max_break_duration", 30 * 60)
            self.remaining_break_seconds = max_break_duration
            self.break_timer.start(1000)

            # Update display immediately after finishing pomodoro
            self.update_display()
            on_pomodoro_finished() # Call hook after state update

    def _check_and_reset_daily_timer(self, app_state):
        """Checks if the date has changed and resets the daily timer if needed."""
        config = app_state.config
        last_date = config.get("last_date", "")
        today = time.strftime("%Y-%m-%d")
        if last_date != today:
            app_state.update_config_value("daily_pomodoro_seconds", 0)
            app_state.update_config_value("last_date", today)

    def _get_statusbar_text(self, app_state):
        """Generates the text for the status bar label."""
        config = app_state.config

        # Build progress display
        completed = config.get("completed_pomodoros", 0)
        target = config.get("pomodoros_before_long_break", 4)
        # Ensure target is at least 1 to avoid modulo by zero or negative numbers
        target = max(1, target) 
        # Handle completion cycle: reset completed count if it reaches target
        # This logic might be better placed in on_pomodoro_finished hook?
        # For now, keep it here for display consistency.
        completed_display = completed % target
        progress = (
            STATUSBAR_FILLED_TOMATO * completed_display
            + STATUSBAR_EMPTY_TOMATO * (target - completed_display)
        )

        # Get break time information
        break_mins, break_secs = divmod(self.remaining_break_seconds, 60)

        # Get daily time information
        daily_total_seconds = config.get("daily_pomodoro_seconds", 0)
        daily_mins, daily_secs = divmod(daily_total_seconds, 60)

        # Determine current state and icon
        if self.break_timer.isActive() and self.remaining_break_seconds > 0:
            icon = STATUSBAR_BREAK_WARNING
            mins, secs = break_mins, break_secs
        elif self.isActive() and self.remaining_seconds > 0:
            icon = STATUSBAR_FILLED_TOMATO
            mins, secs = divmod(self.remaining_seconds, 60)
        else: # Idle state
            icon = STATUSBAR_EMPTY_TOMATO
            mins, secs = divmod(config.get("pomodoro_duration", 25) * 60, 60) # Show configured duration when idle
            progress = STATUSBAR_EMPTY_TOMATO * target # Show all empty when idle

        # Get status bar format string
        statusbar_format_key = config.get(
            "statusbar_format", "ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME"
        )
        format_str = getattr(
            STATUSBAR_FORMATS,
            statusbar_format_key,
            STATUSBAR_FORMATS.ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME, # Default format
        )

        # Dynamically generate display content based on format string
        try:
            return format_str.format(
                icon=icon,
                mins=mins,
                secs=secs,
                progress=progress,
                daily_mins=daily_mins,
                daily_secs=daily_secs,
                completed=completed, # Add total completed count
                target=target, # Add target count
            )
        except KeyError as e:
            # Fallback to default format if unsupported variables
            print(f"Warning: Status bar format '{statusbar_format_key}' caused KeyError: {e}. Falling back to default.")
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

    def _update_circular_timer_progress(self, app_state):
        """Updates the progress of the circular timer."""
        if not self.circular_timer:
            return

        config = app_state.config
        if self.isActive() and self.remaining_seconds > 0:
            self.circular_timer.set_progress(
                self.remaining_seconds, self.total_seconds
            )
        elif self.break_timer.isActive() and self.remaining_break_seconds > 0:
            max_break_duration = max(1, config.get("max_break_duration", 1))
            self.circular_timer.set_progress(
                self.remaining_break_seconds, max_break_duration
            )
        else: # Idle or finished
            self.circular_timer.set_progress(0, 1)  # Reset when idle/finished

    def update_display(self):
        """Updates the status bar and circular timer displays."""
        # Ensure UI updates run in main thread using a single timer event
        def _update_ui():
            app_state = get_app_state()

            # Check and reset daily timer if necessary
            self._check_and_reset_daily_timer(app_state)

            # Update status bar label
            label = app_state.timer_label
            if label:
                status_text = self._get_statusbar_text(app_state)
                label.setText(status_text)
                show_timer_in_statusbar(True) # Keep status bar visible if label exists
            else:
                show_timer_in_statusbar(False) # Hide if label doesn't exist

            # Update circular timer
            self._update_circular_timer_progress(app_state)

        # Schedule the UI update in the main thread
        if mw and mw.isVisible(): # Only schedule if main window is visible
            mw.progress.timer(10, _update_ui, False)
