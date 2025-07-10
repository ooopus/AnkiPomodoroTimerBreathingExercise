from typing import override

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
from ...config.types import DisplayPosition
from ...state import get_app_state, reload_config
from ...translator import _
from ..utils import get_screen_identifier
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
        screen = self.screen()
        if not screen:
            screen = QApplication.primaryScreen()
            if not screen:
                return

        config = reload_config()
        position = config.timer_position

        if position == TimerPosition.LAST_USED:
            identifier = get_screen_identifier(screen)
            if identifier in config.saved_timer_positions:
                saved_pos = config.saved_timer_positions[identifier]
                current_res = screen.size()
                current_dpi = (
                    screen.logicalDotsPerInchX(),
                    screen.logicalDotsPerInchY(),
                )

                if (
                    saved_pos.resolution == (current_res.width(), current_res.height())
                    and saved_pos.logical_dpi == current_dpi
                ):
                    self.move(saved_pos.pos[0], saved_pos.pos[1])
                    return

        margin = 20
        screen_rect = screen.availableGeometry()
        window_width, window_height = self.width(), self.height()

        x, y = screen_rect.x() + margin, screen_rect.y() + margin

        match position:
            case TimerPosition.TOP_RIGHT:
                x = screen_rect.right() - window_width - margin
            case TimerPosition.BOTTOM_LEFT:
                y = screen_rect.bottom() - window_height - margin
            case TimerPosition.BOTTOM_RIGHT:
                x = screen_rect.right() - window_width - margin
                y = screen_rect.bottom() - window_height - margin
            case TimerPosition.TOP_LEFT:
                pass

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

    def resizeEvent(self, a0: QResizeEvent | None):
        super().resizeEvent(a0)
        self._center_timer_widget()

    # 拖动功能
    def mousePressEvent(self, a0: QMouseEvent | None):
        if self._offset is not None and a0 and a0.button() == Qt.MouseButton.LeftButton:
            self._offset = a0.globalPosition() - QPointF(self.pos())
            a0.accept()
        else:
            super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: QMouseEvent | None):
        if self._offset is not None and a0 and a0.buttons() & Qt.MouseButton.LeftButton:
            new_pos = a0.globalPosition() - self._offset
            self.move(new_pos.toPoint())
            a0.accept()
        else:
            super().mouseMoveEvent(a0)

    def mouseReleaseEvent(self, a0: QMouseEvent | None):
        if self._offset is not None and a0 and a0.button() == Qt.MouseButton.LeftButton:
            screen = self.screen()
            if not screen:
                super().mouseReleaseEvent(a0)
                return

            identifier = get_screen_identifier(screen)

            app_state = get_app_state()
            pos = self.pos()
            current_res = screen.size()
            logical_dpi = (
                screen.logicalDotsPerInchX(),
                screen.logicalDotsPerInchY(),
            )

            display_pos = DisplayPosition(
                serial_number=identifier,  # 使用生成的标识符
                resolution=(current_res.width(), current_res.height()),
                logical_dpi=logical_dpi,
                pos=(pos.x(), pos.y()),
            )

            # 更新配置
            saved_positions = app_state.config.saved_timer_positions.copy()
            saved_positions[identifier] = display_pos
            app_state.update_config_value("saved_timer_positions", saved_positions)

            a0.accept()
        else:
            super().mouseReleaseEvent(a0)

    @override
    def closeEvent(self, a0: QCloseEvent | None):
        self.closed.emit()
        super().closeEvent(a0)


# 全局窗口实例
_timer_window_instance: TimerWindow | None = None


def setup_circular_timer(
    timer_widget_class: TimerClass, force_new: bool = False
) -> BaseCircularTimer | None:
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

        _timer_window_instance.closed.connect(on_closed)

    return _timer_window_instance.timer_widget if _timer_window_instance else None
