from aqt import mw
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget
from .config import get_config, set_pomodoro_timer, get_timer_label
from .constants import STATUSBAR_DEFAULT_TEXT
from .ui.circular_timer import setup_circular_timer


class PomodoroTimer(QTimer):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.timeout.connect(self.update_timer)
        set_pomodoro_timer(self)
        self.circular_timer = None

    def start_timer(self, minutes):
        """Starts the Pomodoro timer for the given number of minutes."""
        from .ui import show_timer_in_statusbar

        config = get_config()  # Use our config getter

        if not config.get("enabled", True):
            print("Pomodoro timer disabled in config.")
            return
        if minutes <= 0:
            print(f"Invalid Pomodoro duration: {minutes} minutes. Timer not started.")
            return

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
        show_timer_in_statusbar(config.get("show_statusbar_timer", True))

    def stop_timer(self):
        """Stops the Pomodoro timer and resets the display."""
        from .ui import show_timer_in_statusbar

        if self.isActive():
            print("Pomodoro timer stopped.")
            self.stop()

        # 确保在主线程执行UI更新
        def _clear_display():
            self.remaining_seconds = 0
            self.total_seconds = 0
            self.update_display()  # 先更新显示清除内容
            show_timer_in_statusbar(False)  # 再隐藏状态栏
            if self.circular_timer:
                self.circular_timer.set_progress(0, 1)  # 重置圆形计时器

        mw.progress.timer(10, _clear_display, False)

    def update_timer(self):
        """Called every second to decrease remaining time and check for finish."""
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_display()
        else:
            from .hooks import on_pomodoro_finished
            from .ui import show_timer_in_statusbar

            print("Pomodoro timer finished.")
            self.stop()  # Stop the QTimer itself
            show_timer_in_statusbar(False)  # 确保状态栏立即隐藏
            on_pomodoro_finished()  # Trigger the next action

    def update_display(self):
        def _update():
            from .ui import show_timer_in_statusbar
            from .constants import STATUSBAR_FORMAT, STATUSBAR_ICON

            label = get_timer_label()
            if label:
                if self.remaining_seconds > 0:
                    mins, secs = divmod(self.remaining_seconds, 60)
                    label.setText(
                        STATUSBAR_FORMAT.format(
                            icon=STATUSBAR_ICON, mins=mins, secs=secs
                        )
                    )
                    show_timer_in_statusbar(True)
                else:
                    label.setText(STATUSBAR_DEFAULT_TEXT)

            # 更新圆形计时器
            if self.circular_timer:
                self.circular_timer.set_progress(
                    self.remaining_seconds, self.total_seconds
                )

        # 确保在主线程执行UI更新
        mw.progress.timer(10, _update, False)
