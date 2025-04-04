# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import QWidget, QDialog, QApplication
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from aqt import (
    mw,
    theme,
    QPainter,
    QColor,
    QPen,
    QLinearGradient,
    QRadialGradient,
    QBrush,
    QFont,
    QPaintEvent,
    QResizeEvent,
)
from ..config import get_config

# --- Constants (Unchanged) ---
# Light Mode Colors
BG_COLOR_START_LIGHT = QColor(230, 230, 230, 200)
BG_COLOR_END_LIGHT = QColor(200, 200, 200, 220)
PROGRESS_COLOR_START_LIGHT = QColor(0, 150, 255)
PROGRESS_COLOR_END_LIGHT = QColor(0, 100, 200)
TEXT_COLOR_START_LIGHT = QColor(50, 50, 50)
TEXT_COLOR_END_LIGHT = QColor(80, 80, 80)
SHADOW_COLOR_LIGHT = QColor(0, 0, 0, 40)

# Dark Mode Colors (Night Mode)
BG_COLOR_START_DARK = QColor(70, 70, 80, 200)
BG_COLOR_END_DARK = QColor(50, 50, 60, 220)
PROGRESS_COLOR_START_DARK = QColor(20, 180, 255)
PROGRESS_COLOR_END_DARK = QColor(10, 130, 220)
TEXT_COLOR_START_DARK = QColor(220, 220, 220)
TEXT_COLOR_END_DARK = QColor(240, 240, 240)
SHADOW_COLOR_DARK = QColor(0, 0, 0, 70)


# --- Improved CircularTimer ---


class CircularTimer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(50, 50)
        self._progress = 0.0
        self._remaining_time = "00:00"

        # --- Detect Theme and Select Colors ---
        self._dark_mode = theme.theme_manager.night_mode
        self._load_colors()

        # --- Pre-create Painter Resources ---
        self._bg_pen = QPen()
        self._bg_pen.setCapStyle(Qt.PenCapStyle.FlatCap)

        self._progress_pen = QPen()
        self._progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        # Text pens - color comes from brush gradient
        self._text_pen = QPen()
        self._shadow_pen = QPen(self._shadow_color)  # Shadow color is fixed per theme
        self._shadow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        # Brushes (Gradients defined/updated later)
        self._bg_brush = QBrush()
        self._progress_brush = QBrush()
        self._text_brush = QBrush()

        # Font
        self._text_font = QFont()
        self._text_font.setBold(True)

        # Initial update of size-dependent resources
        self._update_dynamic_resources()

    def _load_colors(self):
        """Load color variables based on detected theme."""
        if self._dark_mode:
            self._bg_start_color = BG_COLOR_START_DARK
            self._bg_end_color = BG_COLOR_END_DARK
            self._progress_start_color = PROGRESS_COLOR_START_DARK
            self._progress_end_color = PROGRESS_COLOR_END_DARK
            self._text_start_color = TEXT_COLOR_START_DARK
            self._text_end_color = TEXT_COLOR_END_DARK
            self._shadow_color = SHADOW_COLOR_DARK
        else:
            self._bg_start_color = BG_COLOR_START_LIGHT
            self._bg_end_color = BG_COLOR_END_LIGHT
            self._progress_start_color = PROGRESS_COLOR_START_LIGHT
            self._progress_end_color = PROGRESS_COLOR_END_LIGHT
            self._text_start_color = TEXT_COLOR_START_LIGHT
            self._text_end_color = TEXT_COLOR_END_LIGHT
            self._shadow_color = SHADOW_COLOR_LIGHT

        # Update pen colors that are set directly
        if hasattr(self, "_shadow_pen"):  # Check if pen exists (during init)
            self._shadow_pen.setColor(self._shadow_color)

    def set_progress(self, current_seconds, total_seconds):
        """Set the progress of the timer."""
        if total_seconds > 0:
            self._progress = max(0.0, min(1.0, 1.0 - (current_seconds / total_seconds)))
        else:
            self._progress = 0.0

        display_seconds = max(0, current_seconds)
        mins, secs = divmod(display_seconds, 60)
        new_time = f"{mins:02d}:{secs:02d}"

        if (
            self._progress != getattr(self, "_last_progress", -1)
            or self._remaining_time != new_time
        ):
            self._remaining_time = new_time
            self._last_progress = self._progress
            self.update()

    def _update_dynamic_resources(self):
        """Update resources that depend on the widget's size."""
        width = self.width()
        height = self.height()
        size = min(width, height)

        self._pen_width = max(2, int(size * 0.06))
        self._padding = self._pen_width / 2 + max(1, int(size * 0.04))
        self._shadow_offset = max(1, int(size * 0.02))

        self._bg_pen.setWidth(self._pen_width)
        self._progress_pen.setWidth(self._pen_width)

        self._text_pen.setWidth(1)
        self._shadow_pen.setWidth(1)

        font_size = max(6, int(size * 0.18))
        self._text_font.setPointSize(font_size)

    def update_theme(self):
        """Update the theme of the timer. Always caused by Anki theme change."""
        self._dark_mode = theme.theme_manager.get_night_mode()
        self._load_colors()
        self.update()

    def resizeEvent(self, event: QResizeEvent):
        """Handle widget resize."""
        super().resizeEvent(event)
        self._update_dynamic_resources()

    def paintEvent(self, event: QPaintEvent):
        """Paint the circular timer using theme-appropriate colors."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        center = QPointF(width / 2.0, height / 2.0)
        radius = min(width, height) / 2.0 - self._padding

        rect = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)

        if not rect.isValid() or radius <= 0:
            return

        # --- 1. Draw Background ---
        bg_gradient = QRadialGradient(center, radius + self._pen_width)
        bg_gradient.setColorAt(0.8, self._bg_start_color)
        bg_gradient.setColorAt(1.0, self._bg_end_color)
        self._bg_brush = QBrush(bg_gradient)

        self._bg_pen.setBrush(self._bg_brush)
        painter.setPen(self._bg_pen)
        painter.drawEllipse(rect)

        # --- 2. Draw Progress Arc ---
        if self._progress > 0:
            progress_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            progress_gradient.setColorAt(0, self._progress_start_color)
            progress_gradient.setColorAt(1, self._progress_end_color)
            self._progress_brush = QBrush(progress_gradient)

            self._progress_pen.setBrush(self._progress_brush)
            painter.setPen(self._progress_pen)

            start_angle = 90 * 16
            span_angle = -int(self._progress * 360 * 16)
            painter.drawArc(rect, start_angle, span_angle)

        # --- 3. Draw Remaining Time Text ---
        painter.setFont(self._text_font)

        # 3a. Draw Shadow Text
        shadow_rect = rect.adjusted(
            self._shadow_offset,
            self._shadow_offset,
            self._shadow_offset,
            self._shadow_offset,
        )
        painter.setPen(self._shadow_pen)
        painter.drawText(
            shadow_rect, Qt.AlignmentFlag.AlignCenter, self._remaining_time
        )

        # 3b. Draw Main Text with Gradient
        text_gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        text_gradient.setColorAt(0, self._text_start_color)
        text_gradient.setColorAt(1, self._text_end_color)
        self._text_brush = QBrush(text_gradient)

        self._text_pen.setBrush(self._text_brush)
        painter.setPen(self._text_pen)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._remaining_time)


# --- TimerWindow (Container Dialog - Fixes for Ruff E701) ---


class TimerWindow(QDialog):
    closed = pyqtSignal()

    def __init__(self, parent=None):  # parent is usually mw
        super().__init__(parent)

        # Use _anki_context flag set earlier
        use_frameless = True  # Default to frameless

        if use_frameless:
            self.setWindowFlags(
                Qt.WindowType.Tool
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.FramelessWindowHint
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            # Enable dragging for frameless
            self._offset = QPointF()  # Initialize for type checking
        else:  # Fallback or testing
            self.setWindowFlags(
                Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint
            )
            # Disable dragging if not frameless
            self._offset = None  # Explicitly set to None

        self.setWindowTitle("番茄钟计时器")
        self.setMinimumSize(100, 100)
        self.timer_widget = CircularTimer(self)
        self.resize(150, 150)
        self._position_window()
        self._center_timer_widget()

    def _position_window(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return  # Ruff Fix: Added return for clarity
        margin = 20
        screen_rect = screen.availableGeometry()
        config = get_config()
        position = config.get("timer_position", "右上角")
        window_width, window_height = self.width(), self.height()
        x, y = margin, margin
        if position == "右上角":
            x = screen_rect.width() - window_width - margin
            y = margin  # Ruff Fix: Keep y assignment for clarity if needed elsewhere
        elif position == "左下角":
            # x = margin # x is already margin
            y = screen_rect.height() - window_height - margin
        elif position == "右下角":
            x = screen_rect.width() - window_width - margin
            y = screen_rect.height() - window_height - margin
        # Implicit 'else' covers "左上角" (x=margin, y=margin)
        self.move(x, y)

    def _center_timer_widget(self):
        dialog_w, dialog_h = self.width(), self.height()
        widget_size = min(dialog_w, dialog_h)
        # Ruff Fix: Use ternary operator for conciseness if preferred, or keep if/else
        # margin = 0 if (self.windowFlags() & Qt.WindowType.FramelessWindowHint) else 5
        if self.windowFlags() & Qt.WindowType.FramelessWindowHint:
            margin = 0
        else:
            margin = 5

        widget_size = max(
            self.timer_widget.minimumSize().width(), widget_size - 2 * margin
        )
        self.timer_widget.setFixedSize(widget_size, widget_size)
        widget_x = (dialog_w - widget_size) // 2
        widget_y = (dialog_h - widget_size) // 2
        self.timer_widget.move(widget_x, widget_y)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self._center_timer_widget()

    # --- Frameless Window Dragging Methods (Fixes for Ruff E701) ---
    def mousePressEvent(self, event):
        # Check if dragging is enabled (_offset is not None) and it's the left button
        if self._offset is not None and event.button() == Qt.MouseButton.LeftButton:
            # Calculate the offset from the window's top-left corner
            self._offset = event.globalPosition() - QPointF(
                self.pos()
            )  # Convert pos() to QPointF
            event.accept()
        else:
            # Ensure base class handler is called if not dragging
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Check if dragging is active (_offset is not None) and left button is pressed
        if self._offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            # Move the window based on the stored offset
            new_pos = event.globalPosition() - self._offset
            self.move(new_pos.toPoint())  # Convert QPointF back to QPoint for move
            event.accept()
        else:
            # Pass event to base class if not dragging
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # Check if it was the left button being released while dragging was possible
        if self._offset is not None and event.button() == Qt.MouseButton.LeftButton:
            # Reset offset when mouse is released (or mark dragging as finished)
            # Keeping self._offset as a QPointF allows re-pressing without re-init
            # If you want to signify "not currently dragging", you might reset differently,
            # but the mousePressEvent logic handles re-init correctly.
            # For clarity that *this specific drag* finished, we don't strictly need to reset _offset here
            # unless _offset being non-None implies "currently dragging".
            # Let's keep it simple: offset stores the drag start diff.
            event.accept()
        else:
            # Pass event to base class
            super().mouseReleaseEvent(event)

    # --- Close Event (Unchanged) ---
    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


# --- Setup Function ---
_timer_window_instance = None


def setup_circular_timer(force_new=False):
    """创建或显示独立的计时器窗口"""
    global _timer_window_instance

    config = get_config()
    if not config.get("enabled", True):
        if _timer_window_instance:
            _timer_window_instance.close()
            _timer_window_instance = None
        return None  # Explicitly return None if disabled

    if _timer_window_instance and not force_new:
        _timer_window_instance._position_window()  # Reposition based on current config
        _timer_window_instance.show()
        _timer_window_instance.raise_()
        _timer_window_instance.activateWindow()
    else:
        if _timer_window_instance and force_new:
            _timer_window_instance.close()
            # _timer_window_instance should become None via on_closed or set here
            _timer_window_instance = None

        _timer_window_instance = TimerWindow(mw)
        _timer_window_instance.show()

        # Define nested function for clarity
        def on_closed():
            global _timer_window_instance
            _timer_window_instance = None
            # print("Timer window closed.") # Debugging

        _timer_window_instance.closed.connect(on_closed)

    # Ensure we return the widget even if reusing the window
    return _timer_window_instance.timer_widget
