from PyQt6.QtWidgets import QWidget, QDialog, QApplication
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QGradient,
    QLinearGradient,
    QConicalGradient,
    QBrush,
)
from aqt import mw
from ..config import get_config


class CircularTimer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(40, 40)  # 设置最小大小
        self.progress = 0  # 0 到 1 之间的值
        self.remaining_time = "00:00"  # 显示的时间文本
        self.current_seconds = 0  # 当前秒数

    def set_progress(self, current_seconds, total_seconds):
        """设置进度和剩余时间"""
        self.current_seconds = current_seconds
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
        bg_gradient = QLinearGradient(0, 0, 0, self.height())
        bg_gradient.setColorAt(0, QColor(60, 60, 60))
        bg_gradient.setColorAt(1, QColor(30, 30, 30))
        painter.setPen(QPen(QBrush(bg_gradient), 4))
        painter.setBrush(QBrush(bg_gradient))
        painter.drawEllipse(rect)

        # 绘制进度圆弧
        if self.progress > 0:
            progress_gradient = QConicalGradient(rect.center(), 90)
            progress_gradient.setColorAt(0, QColor(0, 180, 255))
            progress_gradient.setColorAt(1, QColor(0, 120, 212))

            # 添加辉光效果
            glow_pen = QPen(QColor(0, 150, 255, 100), 6)
            glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(glow_pen)
            painter.drawArc(rect, 90 * 16, -int(360 * self.progress) * 16)

            # 绘制主进度条
            pen = QPen(QBrush(progress_gradient), 4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(rect, 90 * 16, -int(360 * self.progress) * 16)

        # 绘制剩余时间文本
        font = painter.font()
        font.setPointSize(min(self.width(), self.height()) // 5)  # 自适应字体大小
        font.setBold(True)  # 加粗
        painter.setFont(font)

        # 添加文本阴影效果
        shadow_color = QColor(0, 0, 0, 50)
        painter.setPen(shadow_color)
        shadow_offset = 2
        painter.drawText(
            rect.adjusted(shadow_offset, shadow_offset, shadow_offset, shadow_offset),
            Qt.AlignmentFlag.AlignCenter,
            self.remaining_time,
        )

        # 创建彩虹渐变效果
        rainbow_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        rainbow_gradient.setColorAt(0.0, QColor(255, 0, 0))  # 红色
        rainbow_gradient.setColorAt(0.16, QColor(255, 127, 0))  # 橙色
        rainbow_gradient.setColorAt(0.33, QColor(255, 255, 0))  # 黄色
        rainbow_gradient.setColorAt(0.5, QColor(0, 255, 0))  # 绿色
        rainbow_gradient.setColorAt(0.66, QColor(0, 0, 255))  # 蓝色
        rainbow_gradient.setColorAt(0.83, QColor(75, 0, 130))  # 靛蓝
        rainbow_gradient.setColorAt(1.0, QColor(143, 0, 255))  # 紫色

        # 设置彩虹渐变位置
        rainbow_gradient.setStart(rect.left(), rect.top())
        rainbow_gradient.setFinalStop(rect.right(), rect.bottom())
        rainbow_gradient.setSpread(
            QGradient.Spread.ReflectSpread
        )  # 反射模式使颜色过渡更平滑

        # 更柔和的阴影效果
        shadow_offset = 1
        for i in range(3, 0, -1):
            shadow_color = QColor(0, 0, 0, 30 * i)
            painter.setPen(shadow_color)
            painter.drawText(
                rect.adjusted(
                    shadow_offset * i,
                    shadow_offset * i,
                    shadow_offset * i,
                    shadow_offset * i,
                ),
                Qt.AlignmentFlag.AlignCenter,
                self.remaining_time,
            )

        # 绘制主文本
        pen = QPen(QBrush(rainbow_gradient), 1)
        painter.setPen(pen)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.remaining_time)


class TimerWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("番茄钟计时器")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(100, 100)
        self.timer_widget = CircularTimer(self)
        self.resize(150, 150)

        # 窗口拖动相关变量
        self.drag_pos = None

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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint()
            self.move(self.pos() + new_pos - self.drag_pos)
            self.drag_pos = new_pos
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = None
            event.accept()

    def closeEvent(self, event):
        """确保窗口关闭时正确释放资源"""
        self.timer_widget.deleteLater()
        super().closeEvent(event)


def setup_circular_timer():
    """创建独立的计时器窗口"""
    config = get_config()
    if not config.get("enabled", True):
        return

    timer_window = TimerWindow(mw)
    timer_window.show()
    return timer_window.timer_widget
