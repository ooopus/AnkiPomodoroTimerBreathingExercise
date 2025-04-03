from PyQt6.QtWidgets import QWidget, QDialog, QApplication
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QLinearGradient, QBrush
from aqt import mw
from ..config import get_config


class CircularTimer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(40, 40)  # Set minimum size
        self.progress = 0  # Value between 0 and 1
        self.remaining_time = "00:00"  # Displayed time text

    def set_progress(self, current_seconds, total_seconds):
        """
        Set the progress of the timer.
        Parameters:
        - current_seconds (int): Current time in seconds.
        - total_seconds (int): Total time in seconds.
        """
        if total_seconds > 0:
            self.progress = 1 - (current_seconds / total_seconds)
        else:
            self.progress = 0

        mins, secs = divmod(current_seconds, 60)
        self.remaining_time = f"{mins:02d}:{secs:02d}"
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Set circular area
        rect = QRectF(4, 4, self.width() - 8, self.height() - 8)

        # Draw background circle
        painter.setPen(QPen(QColor(200, 200, 200), 3))
        painter.drawEllipse(rect)

        # Draw progress arc
        if self.progress > 0:
            painter.setPen(QPen(QColor(0, 120, 212), 3))
            span_angle = -int(360 * self.progress)
            painter.drawArc(rect, 90 * 16, span_angle * 16)

        # Draw remaining time text
        font = painter.font()
        font.setPointSize(min(self.width(), self.height()) // 5)  # Auto-adjust font size
        font.setBold(True)  # Bold text
        painter.setFont(font)

        # Add text shadow effect
        shadow_color = QColor(0, 0, 0, 50)
        painter.setPen(shadow_color)
        shadow_offset = 2
        painter.drawText(
            rect.adjusted(shadow_offset, shadow_offset, shadow_offset, shadow_offset),
            Qt.AlignmentFlag.AlignCenter,
            self.remaining_time,
        )

        # Draw main text
        text_gradient = QLinearGradient(0, 0, 0, self.height())
        text_gradient.setColorAt(0, QColor(30, 30, 30))
        text_gradient.setColorAt(1, QColor(70, 70, 70))
        painter.setPen(QPen(QBrush(text_gradient), 1))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.remaining_time)


class TimerWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("番茄钟计时器")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumSize(100, 100)
        self.timer_widget = CircularTimer(self)
        self.resize(150, 150)

        # Set window position based on configuration
        screen = QApplication.primaryScreen()
        if screen:
            margin = 20  # Set margin
            screen_rect = screen.availableGeometry()
            position = get_config().get("timer_position", "左上角")

            if position == "左上角":
                self.move(margin, margin)
            elif position == "右上角":
                self.move(screen_rect.width() - self.width() - margin, margin)
            elif position == "左下角":
                self.move(margin, screen_rect.height() - self.height() - margin)
            elif position == "右下角":
                self.move(
                    screen_rect.width() - self.width() - margin,
                    screen_rect.height() - self.height() - margin,
                )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = min(self.width(), self.height())
        self.timer_widget.setFixedSize(size - 20, size - 20)
        self.timer_widget.move(10, 10)


def setup_circular_timer():
    """创建独立的计时器窗口"""
    config = get_config()
    if not config.get("enabled", True):
        return

    timer_window = TimerWindow(mw)
    timer_window.show()
    return timer_window.timer_widget