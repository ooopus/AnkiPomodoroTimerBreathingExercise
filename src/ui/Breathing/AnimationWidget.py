import time

from aqt import (
    QBrush,
    QColor,
    QDialog,
    QMainWindow,
    QPainter,
    QPaintEvent,
    QPointF,
    QSizePolicy,
    Qt,
    QTimer,
    QWidget,
    mw,
)

from ...config.enums import BreathingPhase


# --- Breathing Animation Widget ---
class BreathingAnimationWidget(QWidget):
    """Displays the expanding/contracting circle animation for breathing."""

    def __init__(self, parent: QMainWindow | QDialog = mw):
        super().__init__(parent)
        self._current_phase_key: BreathingPhase = BreathingPhase.INHALE
        self._phase_duration_ms = 4000
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._update_animation)
        self._start_time = time.time()
        self._progress = 0.0
        self._min_radius_ratio = 0.2
        self._max_radius_ratio = 0.8
        # Define colors using QColor constants or hex strings
        self._color_inhale = QColor("#87CEEB")  # Sky Blue
        self._color_hold = QColor("#ADD8E6")  # Light Blue
        self._color_exhale = QColor("#B0E0E6")  # Powder Blue
        self.setMinimumSize(150, 150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_phase(self, phase_key: BreathingPhase, duration_seconds: int):
        """Sets the current breathing phase and its duration."""
        self._current_phase_key = phase_key
        self._phase_duration_ms = duration_seconds * 1000
        self._start_time = time.time()
        self._progress = 0.0
        self._animation_timer.stop()  # Stop previous timer explicitly

        if self._phase_duration_ms > 33:
            # Start timer with a reasonable interval for smooth animation
            # (e.g., 33ms ~ 30fps)
            self._animation_timer.start(33)
            # Initial update to show the start state immediately
            self.update()
        else:
            # If duration is 0, set progress to 1 and update once
            self._progress = 1.0
            self.update()

    def stop_animation(self):
        """Stops the animation timer."""
        self._animation_timer.stop()

    def _update_animation(self):
        """Updates the animation progress based on elapsed time."""
        elapsed_ms = (time.time() - self._start_time) * 1000
        if self._phase_duration_ms > 0:
            self._progress = min(1.0, elapsed_ms / self._phase_duration_ms)
        else:
            # Should not be called if duration is 0 as timer isn't started,
            # but handle defensively
            self._progress = 1.0

        self.update()  # Request a repaint

        # Stop the timer precisely when progress reaches 1.0
        if self._progress >= 1.0:
            self._animation_timer.stop()

    def paintEvent(self, a0: QPaintEvent | None):
        """Paints the breathing circle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width, height = self.width(), self.height()
        center = QPointF(width / 2, height / 2)
        # Calculate radius based on the smaller dimension to fit circle
        max_available_radius = (
            min(width, height) / 2 * 0.9
        )  # Use 90% of available space
        min_radius = max_available_radius * self._min_radius_ratio
        max_radius = max_available_radius * self._max_radius_ratio
        radius_range = max_radius - min_radius

        current_radius = min_radius  # Default radius
        current_color = QColor(Qt.GlobalColor.gray)  # Default color

        # Determine radius and color based on phase and progress
        match self._current_phase_key:
            case BreathingPhase.INHALE:
                # Linear interpolation from min to max radius
                current_radius = min_radius + radius_range * self._progress
                current_color = self._color_inhale
            case BreathingPhase.HOLD_AFTER_INHALE:
                # Stays at max radius during hold
                current_radius = max_radius
                current_color = self._color_hold
            case BreathingPhase.EXHALE:
                # Linear interpolation from max to min radius
                current_radius = max_radius - radius_range * self._progress
                current_color = self._color_exhale
            case BreathingPhase.HOLD_AFTER_EXHALE:
                # Stays at min radius during hold
                current_radius = min_radius
                current_color = self._color_hold
            case _:
                current_radius = min_radius
                current_color = QColor(Qt.GlobalColor.gray)

        # Handle zero duration phases to show the final state immediately
        if self._phase_duration_ms <= 0:
            match self._current_phase_key:
                case BreathingPhase.INHALE | BreathingPhase.HOLD_AFTER_INHALE:
                    current_radius = max_radius
                case BreathingPhase.EXHALE | BreathingPhase.HOLD_AFTER_EXHALE:
                    current_radius = min_radius

        # Draw the circle
        painter.setBrush(QBrush(current_color))
        painter.setPen(Qt.PenStyle.NoPen)  # No border
        painter.drawEllipse(center, current_radius, current_radius)
