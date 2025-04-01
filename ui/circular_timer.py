from PyQt6.QtWidgets import QWidget, QDialog, QApplication
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen
from aqt import mw
from ..config import get_config


class CircularTimer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(40, 40)  # 设置最小大小
        self.progress = 0  # 0 到 1 之间的值
        self.remaining_time = "00:00"  # 显示的时间文本

    def set_progress(self, current_seconds, total_seconds):
        """设置进度和剩余时间"""
        if total_seconds > 0:
            self.progress = 1 - (current_seconds / total_seconds)
        else:
            self.progress = 0

        mins, secs = divmod(current_seconds, 60)
        self.remaining_time = f"{mins:02d}:{secs:02d}"
        self.update()  # 触发重绘

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 设置圆形区域
        rect = QRectF(4, 4, self.width() - 8, self.height() - 8)

        # 绘制背景圆
        painter.setPen(QPen(QColor(200, 200, 200), 3))
        painter.drawEllipse(rect)

        # 绘制进度圆弧
        if self.progress > 0:
            painter.setPen(QPen(QColor(0, 120, 212), 3))
            span_angle = -int(360 * self.progress)
            painter.drawArc(rect, 90 * 16, span_angle * 16)

        # 绘制剩余时间文本
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.remaining_time)


class TimerWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("番茄钟计时器")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumSize(100, 100)
        self.timer_widget = CircularTimer(self)
        self.resize(150, 150)

        # 根据配置设置窗口位置
        screen = QApplication.primaryScreen()
        if screen:
            margin = 20  # 设置边距
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
