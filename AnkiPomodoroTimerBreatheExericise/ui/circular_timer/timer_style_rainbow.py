# -*- coding: utf-8 -*-
import time  # Added for time-based color cycling

from aqt import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPaintEvent,
    QPen,
    QPointF,
    QRadialGradient,
    QRectF,
    QResizeEvent,
    Qt,
    QTimer,
    QWidget,
    theme,
)

# Import common elements NEEDED by this style
from .timer_common import (
    BG_COLOR_END_DARK,
    BG_COLOR_END_LIGHT,
    BG_COLOR_START_DARK,
    # Import specific colors used by this style (BG, Progress, Shadow)
    BG_COLOR_START_LIGHT,
    PROGRESS_COLOR_END_DARK,
    PROGRESS_COLOR_END_LIGHT,
    PROGRESS_COLOR_START_DARK,
    PROGRESS_COLOR_START_LIGHT,
    SHADOW_COLOR_DARK,
    SHADOW_COLOR_LIGHT,
)


# --- Rainbow Text CircularTimer ---
class CircularTimer(QWidget):
    """Circular Timer implementation with dynamic Rainbow Text."""

    RAINBOW_CYCLE_DURATION_S = 6.0
    ANIMATION_UPDATE_INTERVAL_MS = 50  # ~20 FPS

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(50, 50)
        self._progress = 0.0
        self._remaining_time = "00:00"

        self._dark_mode = theme.theme_manager.night_mode  # Detect initial theme
        self._load_colors()  # Load BG, Progress, Shadow colors

        # Pens and Brushes specific to this style
        self._bg_pen = QPen()
        self._bg_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        self._progress_pen = QPen()
        self._progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self._text_pen = QPen()  # Pen for rainbow text (color set dynamically)
        self._text_pen.setWidth(1)
        self._text_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self._shadow_pen = QPen(self._shadow_color)  # Shadow color from common
        self._shadow_pen.setWidth(1)
        self._shadow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        self._bg_brush = QBrush()
        self._progress_brush = QBrush()
        # No _text_brush needed for this style

        self._text_font = QFont()
        self._text_font.setBold(True)

        self._update_dynamic_resources()

        # Animation Timer for Rainbow Effect
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._update_animation)
        self._animation_timer.start(self.ANIMATION_UPDATE_INTERVAL_MS)

    def _update_animation(self):
        """Triggers a repaint to update the rainbow text color."""
        self.update()

    def _load_colors(self):
        """Load color variables based on detected theme."""
        # Uses colors imported from timer_common
        if self._dark_mode:
            self._bg_start_color = BG_COLOR_START_DARK
            self._bg_end_color = BG_COLOR_END_DARK
            self._progress_start_color = PROGRESS_COLOR_START_DARK
            self._progress_end_color = PROGRESS_COLOR_END_DARK
            self._shadow_color = SHADOW_COLOR_DARK
        else:
            self._bg_start_color = BG_COLOR_START_LIGHT
            self._bg_end_color = BG_COLOR_END_LIGHT
            self._progress_start_color = PROGRESS_COLOR_START_LIGHT
            self._progress_end_color = PROGRESS_COLOR_END_LIGHT
            self._shadow_color = SHADOW_COLOR_LIGHT

        # Update shadow pen color directly
        if hasattr(self, "_shadow_pen"):
            self._shadow_pen.setColor(self._shadow_color)

    def set_progress(self, current_seconds, total_seconds):
        """Set the progress of the timer."""
        # Identical logic to other version
        if total_seconds > 0:
            self._progress = max(0.0, min(1.0, 1.0 - (current_seconds / total_seconds)))
        else:
            self._progress = 0.0

        display_seconds = max(0, current_seconds)
        mins, secs = divmod(display_seconds, 60)
        new_time = f"{mins:02d}:{secs:02d}"

        # Update check is still needed for text content change
        if (
            self._progress != getattr(self, "_last_progress", -1)
            or self._remaining_time != new_time
        ):
            self._remaining_time = new_time
            self._last_progress = self._progress
            self.update()  # Update needed for text content change

    def _update_dynamic_resources(self):
        """Update resources that depend on the widget's size."""
        # Identical logic to other version
        width = self.width()
        height = self.height()
        size = min(width, height)

        self._pen_width = max(2, int(size * 0.06))
        self._padding = self._pen_width / 2 + max(1, int(size * 0.04))
        self._shadow_offset = max(1, int(size * 0.02))

        self._bg_pen.setWidth(self._pen_width)
        self._progress_pen.setWidth(self._pen_width)
        # Text/Shadow pen width already set

        font_size = max(6, int(size * 0.18))
        self._text_font.setPointSize(font_size)

    def resizeEvent(self, event: QResizeEvent):
        """Handle widget resize."""
        # Identical logic to other version
        super().resizeEvent(event)
        self._update_dynamic_resources()

    def paintEvent(self, event: QPaintEvent):
        """Paint the circular timer with rainbow text."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        center = QPointF(width / 2.0, height / 2.0)
        radius = min(width, height) / 2.0 - self._padding
        rect = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)

        if not rect.isValid() or radius <= 0:
            return

        # --- 1. Draw Background (Uses common colors) ---
        bg_gradient = QRadialGradient(center, radius + self._pen_width)
        bg_gradient.setColorAt(0.8, self._bg_start_color)
        bg_gradient.setColorAt(1.0, self._bg_end_color)
        self._bg_brush = QBrush(bg_gradient)
        self._bg_pen.setBrush(self._bg_brush)
        painter.setPen(self._bg_pen)
        painter.drawEllipse(rect)

        # --- 2. Draw Progress Arc (Uses common colors) ---
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

        # --- 3. Draw Remaining Time Text (Rainbow Style) ---
        painter.setFont(self._text_font)

        # 3a. Draw Shadow Text (Uses common shadow color)
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

        # 3b. Draw Main Text with DYNAMIC RAINBOW COLOR
        current_time = time.time()
        hue = (
            current_time % self.RAINBOW_CYCLE_DURATION_S
        ) / self.RAINBOW_CYCLE_DURATION_S
        rainbow_color = QColor.fromHsvF(hue, 1.0, 1.0)
        self._text_pen.setColor(rainbow_color)  # Set pen color directly
        painter.setPen(self._text_pen)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._remaining_time)

    def __del__(self):
        """Clean up the animation timer."""
        if hasattr(self, "_animation_timer") and self._animation_timer:
            try:
                self._animation_timer.stop()
                # Optional: disconnect to be sure
                # self._animation_timer.timeout.disconnect(self._update_animation)
                print("Rainbow animation timer stopped.")
            except RuntimeError:
                # Timer might already be deleted if parent QObject is destroyed first
                pass
            self._animation_timer = None  # Help garbage collection
