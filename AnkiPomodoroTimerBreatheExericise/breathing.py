import time

from aqt import (
    QBrush,
    QColor,
    QDialog,
    QLabel,
    QPainter,
    QPointF,
    QPushButton,
    QSizePolicy,
    Qt,
    QTimer,
    QVBoxLayout,
    QWidget,
    mw,
)

from .constants import PHASES
from .state import get_app_state
from .translator import _


# --- Breathing Animation Widget ---
class BreathingAnimationWidget(QWidget):
    """Displays the expanding/contracting circle animation for breathing."""

    INHALE = "INHALE"
    HOLD = "HOLD"
    EXHALE = "EXHALE"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_phase_key = self.INHALE
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

    def set_phase(self, phase_key: str, duration_seconds: int):
        """Sets the current breathing phase and its duration."""
        self._current_phase_key = phase_key
        self._phase_duration_ms = duration_seconds * 1000
        self._start_time = time.time()
        self._progress = 0.0
        self._animation_timer.stop()  # Stop previous timer explicitly

        if self._phase_duration_ms > 0:
            # Start timer with a reasonable interval for smooth animation (e.g., 33ms ~ 30fps)
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
            # Should not be called if duration is 0 as timer isn't started, but handle defensively
            self._progress = 1.0

        self.update()  # Request a repaint

        # Stop the timer precisely when progress reaches 1.0
        if self._progress >= 1.0:
            self._animation_timer.stop()

    def paintEvent(self, event):
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
        if self._current_phase_key == self.INHALE:
            # Linear interpolation from min to max radius
            current_radius = min_radius + radius_range * self._progress
            current_color = self._color_inhale
        elif self._current_phase_key == self.HOLD:
            # Stays at max radius during hold
            current_radius = max_radius
            current_color = self._color_hold
        elif self._current_phase_key == self.EXHALE:
            # Linear interpolation from max to min radius
            current_radius = max_radius - radius_range * self._progress
            current_color = self._color_exhale

        # Handle zero duration phases to show the final state immediately
        if self._phase_duration_ms <= 0:
            if self._current_phase_key == self.INHALE:
                current_radius = max_radius
            elif self._current_phase_key == self.HOLD:
                current_radius = max_radius  # Hold starts at max
            elif self._current_phase_key == self.EXHALE:
                current_radius = min_radius

        # Draw the circle
        painter.setBrush(QBrush(current_color))
        painter.setPen(Qt.PenStyle.NoPen)  # No border
        painter.drawEllipse(center, current_radius, current_radius)


# --- Breathing Logic (Cycle-based) ---
class BreathingDialog(QDialog):
    """Dialog window for the guided breathing exercise based on cycles."""

    def __init__(self, target_cycles: int, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle(_("呼吸训练"))
        self.setModal(True)
        self.target_cycles = max(1, target_cycles)  # Ensure at least one cycle
        self.completed_cycles = 0
        self._phase_timer = QTimer(self)
        self._phase_timer.setSingleShot(True)  # 仍然是单次触发，但拥有实例
        self._phase_timer.timeout.connect(self._advance_to_next_phase)

        # Use AppState
        app_state = get_app_state()
        config = app_state.config

        # --- Dynamically build active phases from config ---
        self.active_phases = []
        for phase_def in PHASES:
            key = phase_def["key"]
            is_enabled = config.get(f"{key}_enabled", phase_def["default_enabled"])
            duration = config.get(f"{key}_duration", phase_def["default_duration"])
            if is_enabled:
                self.active_phases.append(
                    {
                        "label": phase_def["label"],
                        "duration": duration,
                        "anim_phase": phase_def["anim_phase"],
                    }
                )

        if not self.active_phases:
            QTimer.singleShot(0, self.reject)
            return

        self.current_phase_index = -1

        # --- UI Elements ---
        layout = QVBoxLayout()
        self.animation_widget = BreathingAnimationWidget(self)
        layout.addWidget(self.animation_widget, 1)

        self.instruction_label = QLabel(_("准备..."), self)
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; margin-top: 10px;"
        )

        self.cycle_label = QLabel(
            _("循环: {current} / {total}").format(
                current=self.completed_cycles + 1, total=self.target_cycles
            ),
            self,
        )
        self.cycle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cycle_label.setStyleSheet("font-size: 16px; margin-bottom: 10px;")

        self.skip_button = QPushButton(_("跳过训练"), self)

        layout.addWidget(self.instruction_label)
        layout.addWidget(self.cycle_label)
        layout.addWidget(self.skip_button)
        self.setLayout(layout)

        self.resize(300, 350)

        # --- Connections ---
        self.skip_button.clicked.connect(self.reject)

        # --- Start the process ---
        self._advance_to_next_phase()

    def _advance_to_next_phase(self):
        """Handles logic for moving to the next phase or completing the exercise."""

        # Determine next phase index and if a cycle was just completed
        next_phase_index = (self.current_phase_index + 1) % len(self.active_phases)
        just_completed_cycle = (
            next_phase_index == 0 and self.current_phase_index != -1
        )  # True if wrapping around

        # Increment cycle count *after* completing the last phase of a cycle
        if just_completed_cycle:
            self.completed_cycles += 1
            self.cycle_label.setText(
                _("循环: {current} / {total}").format(
                    current=min(self.completed_cycles + 1, self.target_cycles),
                    total=self.target_cycles,
                )
            )

            # Check if target cycles are reached
            if self.completed_cycles >= self.target_cycles:
                self.accept()
                return

        self.current_phase_index = next_phase_index
        current_phase_data = self.active_phases[self.current_phase_index]
        duration = current_phase_data["duration"]
        label = current_phase_data["label"]
        anim_phase_key = current_phase_data["anim_phase"]

        # Update UI for the current phase
        self.instruction_label.setText(f"{label} ({duration}s)")
        self.animation_widget.set_phase(anim_phase_key, duration)
        self.cycle_label.setText(
            _("循环: {current} / {total}").format(
                current=self.completed_cycles + 1, total=self.target_cycles
            )
        )

        if duration > 0:
            self._phase_timer.start(duration * 1000)
        else:
            # If duration is 0, advance immediately (with a tiny delay for event loop)
            self._phase_timer.start(10)

    def stop_all_timers(self):
        """Stops the animation and phase advancement timer."""
        self.animation_widget.stop_animation()

    def closeEvent(self, event):
        """Called when the dialog is closed (e.g., by window manager)."""
        self.stop_all_timers()
        super().closeEvent(event)

    def accept(self):
        """Called when the exercise completes successfully."""
        self.stop_all_timers()
        super().accept()

    def reject(self):
        """Called when the dialog is skipped or closed prematurely."""
        self.stop_all_timers()
        super().reject()
