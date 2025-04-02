from aqt import mw
import time
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QBrush
from PyQt6.QtWidgets import (
    QWidget,
    QDialog,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QPushButton,
)
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPainter, QColor
from .constants import PHASES
from .config import get_config  # Changed from direct config import


# --- 呼吸训练动画 Widget ---
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
        # print(f"Animation: Setting phase {phase_key} for {duration_seconds}s") # Debug print
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
        # print("Animation: Stopped") # Debug print

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
            # print("Animation: Phase complete") # Debug print
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


# --- 呼吸训练逻辑 (基于循环次数) ---
class BreathingDialog(QDialog):
    """Dialog window for the guided breathing exercise based on cycles."""

    def __init__(self, target_cycles: int, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("呼吸训练")
        self.setModal(True)
        self.target_cycles = max(1, target_cycles)  # Ensure at least one cycle
        self.completed_cycles = 0
        # Timer used via singleShot to trigger phase changes
        self._phase_advance_timer = QTimer(self)
        self._pending_single_shot = None  # Keep track if needed

        print(f"BreathingDialog: Initialized for {self.target_cycles} cycles.")

        # --- Dynamically build active phases from config ---
        self.active_phases = []
        for phase_def in PHASES:
            key = phase_def["key"]
            is_enabled = get_config().get(
                f"{key}_enabled", phase_def["default_enabled"]
            )
            duration = get_config().get(
                f"{key}_duration", phase_def["default_duration"]
            )
            if is_enabled:
                self.active_phases.append(
                    {
                        "label": phase_def["label"],
                        "duration": duration,
                        "anim_phase": phase_def["anim_phase"],
                    }
                )
                print(
                    f"BreathingDialog: Added active phase '{phase_def['label']}' ({duration}s)"
                )

        if not self.active_phases:
            # This case should be prevented by the check in show_breathing_dialog
            print("BreathingDialog Error: No active phases configured. Closing.")
            # Schedule closing after the constructor finishes
            QTimer.singleShot(0, self.reject)
            return

        self.current_phase_index = (
            -1
        )  # Start at -1 so first call to update sets index 0

        # --- UI Elements ---
        self._main_layout = QVBoxLayout(self)
        self.animation_widget = BreathingAnimationWidget(self)
        self._main_layout.addWidget(
            self.animation_widget, 1
        )  # 使用新的变量名

        self.instruction_label = QLabel("准备...", self)
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; margin-top: 10px;"
        )

        # Cycle Counter Label
        self.cycle_label = QLabel(
            f"循环: {self.completed_cycles + 1} / {self.target_cycles}", self
        )
        self.cycle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cycle_label.setStyleSheet("font-size: 16px; margin-bottom: 10px;")

        self.skip_button = QPushButton("跳过训练", self)  # Changed label slightly

        self.layout.addWidget(self.instruction_label)
        self.layout.addWidget(self.cycle_label)
        self.layout.addWidget(self.skip_button)
        self.setLayout(self._main_layout)  # 使用 setLayout 而不是直接赋值

        # Resize dialog to be reasonable
        self.resize(300, 350)

        # --- Connections ---
        self.skip_button.clicked.connect(self.reject)  # Skip closes the dialog

        # --- Start the process ---
        print("BreathingDialog: Starting first phase...")
        self._advance_to_next_phase()  # Start the first phase

    def _advance_to_next_phase(self):
        """Handles logic for moving to the next phase or completing the exercise."""
        self._pending_single_shot = None  # Clear flag

        # Determine next phase index and if a cycle was just completed
        next_phase_index = (self.current_phase_index + 1) % len(self.active_phases)
        just_completed_cycle = (
            next_phase_index == 0 and self.current_phase_index != -1
        )  # True if wrapping around

        # Increment cycle count *after* completing the last phase of a cycle
        if just_completed_cycle:
            self.completed_cycles += 1
            print(
                f"BreathingDialog: Completed cycle {self.completed_cycles}/{self.target_cycles}"
            )
            self.cycle_label.setText(
                f"循环: {min(self.completed_cycles + 1, self.target_cycles)} / {self.target_cycles}"
            )  # Update label, cap first number

            # Check if target cycles are reached
            if self.completed_cycles >= self.target_cycles:
                print("BreathingDialog: Target cycles reached. Finishing.")
                self.accept()  # Finish successfully
                return  # Stop processing

        # Set the index for the *upcoming* phase
        self.current_phase_index = next_phase_index
        current_phase_data = self.active_phases[self.current_phase_index]
        duration = current_phase_data["duration"]
        label = current_phase_data["label"]
        anim_phase_key = current_phase_data["anim_phase"]

        # Update UI for the current phase
        self.instruction_label.setText(f"{label} ({duration}s)")
        self.animation_widget.set_phase(anim_phase_key, duration)
        # Ensure cycle label reflects the *current* cycle number
        self.cycle_label.setText(
            f"循环: {self.completed_cycles + 1} / {self.target_cycles}"
        )

        print(
            f"BreathingDialog: Starting phase {self.current_phase_index + 1}/{len(self.active_phases)} ('{label}', {duration}s) of cycle {self.completed_cycles + 1}"
        )

        # Schedule the next call to _advance_to_next_phase after the current phase duration
        if duration > 0:
            # Use singleShot to call this method again after the delay
            self._pending_single_shot = QTimer.singleShot(
                duration * 1000, self._advance_to_next_phase
            )
        else:
            # If duration is 0, advance immediately (with a tiny delay for event loop)
            self._pending_single_shot = QTimer.singleShot(
                10, self._advance_to_next_phase
            )

    def stop_all_timers(self):
        """Stops the animation and any pending phase advancement."""
        print("BreathingDialog: Stopping timers and animation.")
        self.animation_widget.stop_animation()
        # Attempt to cancel the pending singleShot if it exists and hasn't fired
        # QTimer.singleShot returns None, so we can't easily cancel it.
        # Stopping the underlying timer might work if the singleShot hasn't triggered yet.
        self._phase_advance_timer.stop()  # Stop the timer used for singleShot
        # It's usually sufficient that the dialog closing prevents further execution.

    # Override closing methods to ensure timers are stopped
    def closeEvent(self, event):
        """Called when the dialog is closed (e.g., by window manager)."""
        print("BreathingDialog: closeEvent triggered.")
        self.stop_all_timers()
        super().closeEvent(event)

    def accept(self):
        """Called when the exercise completes successfully."""
        print("BreathingDialog: Accepted (finished).")
        self.stop_all_timers()
        super().accept()

    def reject(self):
        """Called when the dialog is skipped or closed prematurely."""
        print("BreathingDialog: Rejected (skipped/closed).")
        self.stop_all_timers()
        super().reject()
