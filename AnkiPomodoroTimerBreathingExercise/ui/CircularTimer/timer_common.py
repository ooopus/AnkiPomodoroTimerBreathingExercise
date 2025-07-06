from typing import Optional

from aqt import (
    QApplication,
    QCloseEvent,
    QDialog,
    QMainWindow,
    QMouseEvent,
    QPointF,
    QResizeEvent,
    Qt,
    mw,
    pyqtSignal,
)

from ...config.enums import TimerPosition
from ...state import get_app_state, reload_config
from ...translator import _
from .timer_base import BaseCircularTimer, TimerClass


class TimerWindow(QDialog):
    """计时器窗口容器"""

    closed = pyqtSignal()
    timer_widget: BaseCircularTimer

    def __init__(self, timer_widget_class: TimerClass, parent: QMainWindow = mw):
        super().__init__(parent)

        use_frameless = True
        if use_frameless:
            self.setWindowFlags(
                Qt.WindowType.Tool
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.FramelessWindowHint
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self._offset = QPointF()
        else:
            self.setWindowFlags(
                Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint
            )
            self._offset = None

        self.setWindowTitle(_("番茄钟计时器"))
        self.setMinimumSize(100, 100)

        # 实例化计时器控件
        self.timer_widget = timer_widget_class(self)
        self.resize(150, 150)
        self.position_window()
        self._center_timer_widget()

    def position_window(self):
        """根据配置将窗口定位到屏幕的指定角落"""
        screen = QApplication.primaryScreen()
        if not screen:
            return

        config = reload_config()
        position = config.timer_position

        margin = 20
        screen_rect = screen.availableGeometry()
        window_width, window_height = self.width(), self.height()

        # 默认位置为左上角
        x, y = margin, margin

        if position == TimerPosition.TOP_RIGHT:
            x = screen_rect.width() - window_width - margin
        elif position == TimerPosition.BOTTOM_LEFT:
            y = screen_rect.height() - window_height - margin
        elif position == TimerPosition.BOTTOM_RIGHT:
            x = screen_rect.width() - window_width - margin
            y = screen_rect.height() - window_height - margin

        self.move(x, y)

    def _center_timer_widget(self):
        """将内部的计时器控件在窗口中居中"""
        dialog_w, dialog_h = self.width(), self.height()
        margin = 0 if (self.windowFlags() & Qt.WindowType.FramelessWindowHint) else 5

        widget_size = max(
            self.timer_widget.minimumSize().width(),
            min(dialog_w, dialog_h) - 2 * margin,
        )

        self.timer_widget.setFixedSize(widget_size, widget_size)
        widget_x = (dialog_w - widget_size) // 2
        widget_y = (dialog_h - widget_size) // 2
        self.timer_widget.move(widget_x, widget_y)

    def resizeEvent(self, a0: Optional[QResizeEvent]):
        super().resizeEvent(a0)
        self._center_timer_widget()

    # 拖动功能
    def mousePressEvent(self, a0: Optional[QMouseEvent]):
        if self._offset is not None and a0 and a0.button() == Qt.MouseButton.LeftButton:
            self._offset = a0.globalPosition() - QPointF(self.pos())
            a0.accept()
        else:
            super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: Optional[QMouseEvent]):
        if self._offset is not None and a0 and a0.buttons() & Qt.MouseButton.LeftButton:
            new_pos = a0.globalPosition() - self._offset
            self.move(new_pos.toPoint())
            a0.accept()
        else:
            super().mouseMoveEvent(a0)

    def mouseReleaseEvent(self, a0: Optional[QMouseEvent]):
        if self._offset is not None and a0 and a0.button() == Qt.MouseButton.LeftButton:
            a0.accept()
        else:
            super().mouseReleaseEvent(a0)

    def closeEvent(self, a0: Optional[QCloseEvent]):
        self.closed.emit()
        super().closeEvent(a0)


# 全局窗口实例
_timer_window_instance: Optional[TimerWindow] = None


def setup_circular_timer(
    timer_widget_class: TimerClass, force_new: bool = False
) -> Optional[BaseCircularTimer]:
    """
    创建或显示独立的计时器窗口。

    Args:
        timer_widget_class: 计时器类，必须是BaseCircularTimer的子类
        force_new: 是否强制创建新窗口

    Returns:
        计时器组件实例，如果创建失败则返回None
    """
    global _timer_window_instance

    config = get_app_state().config
    if not config.enabled:
        if _timer_window_instance:
            _timer_window_instance.close()
            _timer_window_instance = None
        return None

    # 检查现有窗口的样式是否与请求的样式匹配
    style_changed = False
    if (
        _timer_window_instance
        and hasattr(_timer_window_instance, "timer_widget")
        and not isinstance(_timer_window_instance.timer_widget, timer_widget_class)
    ):
        style_changed = True
        force_new = True

    if _timer_window_instance and not force_new:
        _timer_window_instance.position_window()
        _timer_window_instance.show()
        _timer_window_instance.raise_()
        _timer_window_instance.activateWindow()
    else:
        if _timer_window_instance and (force_new or style_changed):
            _timer_window_instance.close()
            _timer_window_instance = None

        _timer_window_instance = TimerWindow(timer_widget_class=timer_widget_class)
        _timer_window_instance.show()

        def on_closed():
            global _timer_window_instance
            _timer_window_instance = None

        _timer_window_instance.closed.connect(on_closed)  # type: ignore

    return _timer_window_instance.timer_widget if _timer_window_instance else None
