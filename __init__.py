# __init__.py (插件主文件 - PyQt6 & Cycle-based Breathing)

import time
import math
from anki.hooks import addHook, wrap # Keep original Anki hooks
from aqt import mw, gui_hooks
from aqt.utils import showInfo, tooltip

# Import necessary Qt6 components explicitly
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox,
    QSpinBox, QSizePolicy, QDialogButtonBox, QFrame, QGroupBox, QApplication # Added QApplication for clipboard if needed later
)
from PyQt6.QtCore import (
    QTimer, QPointF, Qt, QObject, pyqtSignal # Added QObject, pyqtSignal if needed later
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QAction
)

# --- 全局变量 ---
pomodoro_timer = None
config = None
timer_label = None # Status bar label

# --- Phase Definition ---
PHASES = [
    {"key": "inhale", "label": "吸气", "default_duration": 4, "default_enabled": True, "anim_phase": "INHALE"},
    {"key": "hold", "label": "屏住", "default_duration": 4, "default_enabled": False, "anim_phase": "HOLD"},
    {"key": "exhale", "label": "呼气", "default_duration": 6, "default_enabled": True, "anim_phase": "EXHALE"}
]

# --- 默认配置 ---
DEFAULT_POMODORO_MINUTES = 25
DEFAULT_BREATHING_CYCLES = 30 # Default number of cycles (Replaced seconds)
DEFAULT_SHOW_STATUSBAR_TIMER = True

# --- 配置管理 ---
def load_config():
    """Loads configuration from Anki, setting defaults if necessary."""
    global config
    config = mw.addonManager.getConfig(__name__)
    if config is None:
        config = {}

    # Set defaults for core settings
    config.setdefault("pomodoro_minutes", DEFAULT_POMODORO_MINUTES)
    config.setdefault("breathing_cycles", DEFAULT_BREATHING_CYCLES) # Use cycles
    config.setdefault("enabled", True)
    config.setdefault("show_statusbar_timer", DEFAULT_SHOW_STATUSBAR_TIMER)

    # Set defaults for each breathing phase
    for phase in PHASES:
        config.setdefault(f"{phase['key']}_duration", phase['default_duration'])
        config.setdefault(f"{phase['key']}_enabled", phase['default_enabled'])

    # Ensure correct types
    try:
        config["pomodoro_minutes"] = int(config.get("pomodoro_minutes", DEFAULT_POMODORO_MINUTES))
        config["breathing_cycles"] = int(config.get("breathing_cycles", DEFAULT_BREATHING_CYCLES)) # Use cycles
        config["enabled"] = bool(config.get("enabled", True))
        config["show_statusbar_timer"] = bool(config.get("show_statusbar_timer", DEFAULT_SHOW_STATUSBAR_TIMER))
        for phase in PHASES:
            config[f"{phase['key']}_duration"] = int(config.get(f"{phase['key']}_duration", phase['default_duration']))
            config[f"{phase['key']}_enabled"] = bool(config.get(f"{phase['key']}_enabled", phase['default_enabled']))
    except (ValueError, TypeError) as e:
        print(f"Pomodoro Addon: Error loading config, resetting to defaults. Error: {e}")
        # Reset to defaults on error
        config = {
            "pomodoro_minutes": DEFAULT_POMODORO_MINUTES,
            "breathing_cycles": DEFAULT_BREATHING_CYCLES,
            "enabled": True,
            "show_statusbar_timer": DEFAULT_SHOW_STATUSBAR_TIMER,
        }
        for phase in PHASES:
            config[f"{phase['key']}_duration"] = phase['default_duration']
            config[f"{phase['key']}_enabled"] = phase['default_enabled']
        save_config() # Save the reset defaults


    # If config was initially None, write the defaults back
    if mw.addonManager.getConfig(__name__) is None:
         mw.addonManager.writeConfig(__name__, config)
    return config

def save_config():
    """Saves the current configuration to Anki."""
    if config is not None:
        mw.addonManager.writeConfig(__name__, config)

# --- 番茄钟逻辑 ---
class PomodoroTimer(QTimer):
    """Handles the countdown for the Pomodoro session."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.remaining_seconds = 0
        self.timeout.connect(self.update_timer)

    def start_timer(self, minutes):
        """Starts the Pomodoro timer for the given number of minutes."""
        if not config.get("enabled", True):
            print("Pomodoro timer disabled in config.")
            return
        if minutes <= 0:
            print(f"Invalid Pomodoro duration: {minutes} minutes. Timer not started.")
            return
        self.remaining_seconds = minutes * 60
        print(f"Pomodoro timer started for {minutes} minutes.")
        self.update_display()
        self.start(1000) # Tick every second
        show_timer_in_statusbar(True)

    def stop_timer(self):
        """Stops the Pomodoro timer and resets the display."""
        if self.isActive():
            print("Pomodoro timer stopped.")
            self.stop()
        self.remaining_seconds = 0
        # Update display to clear timer *before* hiding the label
        self.update_display()
        show_timer_in_statusbar(False)


    def update_timer(self):
        """Called every second to decrease remaining time and check for finish."""
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_display()
            # print(f"Timer tick: {self.remaining_seconds}s left") # Debug print
        else:
            print("Pomodoro timer finished.")
            self.stop() # Stop the QTimer itself
            on_pomodoro_finished() # Trigger the next action

    def update_display(self):
        """Updates the status bar label with the remaining time."""
        if timer_label:
            if self.remaining_seconds > 0:
                mins, secs = divmod(self.remaining_seconds, 60)
                timer_label.setText(f"🍅 {mins:02d}:{secs:02d}")
            else:
                 timer_label.setText("🍅 --:--") # Show blank when stopped


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
        self._color_inhale = QColor("#87CEEB") # Sky Blue
        self._color_hold = QColor("#ADD8E6")   # Light Blue
        self._color_exhale = QColor("#B0E0E6") # Powder Blue
        self.setMinimumSize(150, 150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_phase(self, phase_key: str, duration_seconds: int):
        """Sets the current breathing phase and its duration."""
        # print(f"Animation: Setting phase {phase_key} for {duration_seconds}s") # Debug print
        self._current_phase_key = phase_key
        self._phase_duration_ms = duration_seconds * 1000
        self._start_time = time.time()
        self._progress = 0.0
        self._animation_timer.stop() # Stop previous timer explicitly

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

        self.update() # Request a repaint

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
        max_available_radius = min(width, height) / 2 * 0.9 # Use 90% of available space
        min_radius = max_available_radius * self._min_radius_ratio
        max_radius = max_available_radius * self._max_radius_ratio
        radius_range = max_radius - min_radius

        current_radius = min_radius # Default radius
        current_color = QColor(Qt.GlobalColor.gray) # Default color

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
             if self._current_phase_key == self.INHALE: current_radius = max_radius
             elif self._current_phase_key == self.HOLD: current_radius = max_radius # Hold starts at max
             elif self._current_phase_key == self.EXHALE: current_radius = min_radius

        # Draw the circle
        painter.setBrush(QBrush(current_color))
        painter.setPen(Qt.PenStyle.NoPen) # No border
        painter.drawEllipse(center, current_radius, current_radius)


# --- 呼吸训练逻辑 (基于循环次数) ---
class BreathingDialog(QDialog):
    """Dialog window for the guided breathing exercise based on cycles."""

    def __init__(self, target_cycles: int, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("呼吸训练")
        self.setModal(True)
        self.target_cycles = max(1, target_cycles) # Ensure at least one cycle
        self.completed_cycles = 0
        # Timer used via singleShot to trigger phase changes
        self._phase_advance_timer = QTimer(self)
        self._pending_single_shot = None # Keep track if needed

        print(f"BreathingDialog: Initialized for {self.target_cycles} cycles.")

        # --- Dynamically build active phases from config ---
        self.active_phases = []
        for phase_def in PHASES:
            key = phase_def["key"]
            is_enabled = config.get(f"{key}_enabled", phase_def["default_enabled"])
            duration = config.get(f"{key}_duration", phase_def["default_duration"])
            if is_enabled:
                self.active_phases.append({
                    "label": phase_def["label"],
                    "duration": duration,
                    "anim_phase": phase_def["anim_phase"]
                })
                print(f"BreathingDialog: Added active phase '{phase_def['label']}' ({duration}s)")

        if not self.active_phases:
             # This case should be prevented by the check in show_breathing_dialog
             print("BreathingDialog Error: No active phases configured. Closing.")
             # Schedule closing after the constructor finishes
             QTimer.singleShot(0, self.reject)
             return

        self.current_phase_index = -1 # Start at -1 so first call to update sets index 0

        # --- UI Elements ---
        self.layout = QVBoxLayout(self)
        self.animation_widget = BreathingAnimationWidget(self)
        self.layout.addWidget(self.animation_widget, 1) # Give animation widget stretch factor

        self.instruction_label = QLabel("准备...", self)
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-top: 10px;")

        # Cycle Counter Label
        self.cycle_label = QLabel(f"循环: {self.completed_cycles + 1} / {self.target_cycles}", self)
        self.cycle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cycle_label.setStyleSheet("font-size: 16px; margin-bottom: 10px;")

        self.skip_button = QPushButton("跳过训练", self) # Changed label slightly

        self.layout.addWidget(self.instruction_label)
        self.layout.addWidget(self.cycle_label)
        self.layout.addWidget(self.skip_button)
        self.setLayout(self.layout)

        # Resize dialog to be reasonable
        self.resize(300, 350)

        # --- Connections ---
        self.skip_button.clicked.connect(self.reject) # Skip closes the dialog

        # --- Start the process ---
        print("BreathingDialog: Starting first phase...")
        self._advance_to_next_phase() # Start the first phase

    def _advance_to_next_phase(self):
        """Handles logic for moving to the next phase or completing the exercise."""
        self._pending_single_shot = None # Clear flag

        # Determine next phase index and if a cycle was just completed
        next_phase_index = (self.current_phase_index + 1) % len(self.active_phases)
        just_completed_cycle = (next_phase_index == 0 and self.current_phase_index != -1) # True if wrapping around

        # Increment cycle count *after* completing the last phase of a cycle
        if just_completed_cycle:
            self.completed_cycles += 1
            print(f"BreathingDialog: Completed cycle {self.completed_cycles}/{self.target_cycles}")
            self.cycle_label.setText(f"循环: {min(self.completed_cycles + 1, self.target_cycles)} / {self.target_cycles}") # Update label, cap first number

            # Check if target cycles are reached
            if self.completed_cycles >= self.target_cycles:
                print("BreathingDialog: Target cycles reached. Finishing.")
                self.accept() # Finish successfully
                return # Stop processing

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
        self.cycle_label.setText(f"循环: {self.completed_cycles + 1} / {self.target_cycles}")

        print(f"BreathingDialog: Starting phase {self.current_phase_index + 1}/{len(self.active_phases)} ('{label}', {duration}s) of cycle {self.completed_cycles + 1}")

        # Schedule the next call to _advance_to_next_phase after the current phase duration
        if duration > 0:
            # Use singleShot to call this method again after the delay
            self._pending_single_shot = QTimer.singleShot(duration * 1000, self._advance_to_next_phase)
        else:
            # If duration is 0, advance immediately (with a tiny delay for event loop)
            self._pending_single_shot = QTimer.singleShot(10, self._advance_to_next_phase)


    def stop_all_timers(self):
        """Stops the animation and any pending phase advancement."""
        print("BreathingDialog: Stopping timers and animation.")
        self.animation_widget.stop_animation()
        # Attempt to cancel the pending singleShot if it exists and hasn't fired
        # QTimer.singleShot returns None, so we can't easily cancel it.
        # Stopping the underlying timer might work if the singleShot hasn't triggered yet.
        self._phase_advance_timer.stop() # Stop the timer used for singleShot
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


# --- Anki 钩子函数 ---

def on_reviewer_did_start(reviewer):
    """Starts the Pomodoro timer when the reviewer screen is shown."""
    global pomodoro_timer
    if not config.get("enabled", True): return

    # Initialize timer if it doesn't exist
    if pomodoro_timer is None:
        print("Initializing PomodoroTimer...")
        pomodoro_timer = PomodoroTimer(mw) # Parent to main window

    # Start timer only if it's not already running
    if not pomodoro_timer.isActive():
         pomo_minutes = config.get("pomodoro_minutes", DEFAULT_POMODORO_MINUTES)
         print(f"Reviewer started, starting Pomodoro for {pomo_minutes} minutes.")
         pomodoro_timer.start_timer(pomo_minutes)
    else:
        print("Reviewer started, but Pomodoro timer is already active.")


def on_state_did_change(new_state: str, old_state: str):
    """Stops the Pomodoro timer when leaving the reviewer state."""
    global pomodoro_timer
    # Stop only if moving *away* from review and the timer exists and is active
    if old_state == "review" and new_state != "review":
        if pomodoro_timer and pomodoro_timer.isActive() and config.get("enabled", True):
            print(f"Left reviewer state ({old_state} -> {new_state}). Stopping Pomodoro timer.")
            pomodoro_timer.stop_timer()
            tooltip("番茄钟已暂停。", period=2000) # "Pomodoro paused"

def on_pomodoro_finished():
    """Called when the Pomodoro timer reaches zero."""
    tooltip("番茄钟时间到！休息一下。", period=3000) # "Pomodoro time's up! Take a break."
    # Ensure we are on the main thread before changing state or showing dialog
    mw.progress.timer(100, lambda: _after_pomodoro_finish_tasks(), False)


def _after_pomodoro_finish_tasks():
    """Actions to perform after the Pomodoro finishes (runs on main thread)."""
    # Return to deck browser
    if mw.state == "review":
        print("Returning to deck browser after Pomodoro.")
        mw.moveToState("deckBrowser")

    # Show breathing dialog after a short delay
    QTimer.singleShot(200, show_breathing_dialog) # Delay allows state change to settle

def show_breathing_dialog():
    """Checks config and shows the BreathingDialog if appropriate."""
    if not config.get("enabled", True):
        print("Skipping breathing dialog: Plugin disabled.")
        return

    # Check if *any* breathing phase is enabled
    any_phase_enabled = any(
        config.get(f"{p['key']}_enabled", p['default_enabled']) for p in PHASES
    )
    if not any_phase_enabled:
        tooltip("呼吸训练已跳过 (无启用阶段)。", period=3000) # "Breathing skipped (no enabled phases)."
        print("Skipping breathing dialog: No phases enabled.")
        return

    # Get configured number of cycles
    target_cycles = config.get("breathing_cycles", DEFAULT_BREATHING_CYCLES)
    if target_cycles <= 0:
        tooltip("呼吸训练已跳过 (循环次数为 0)。", period=3000) # "Breathing skipped (cycles set to 0)."
        print(f"Skipping breathing dialog: Target cycles is {target_cycles}.")
        return

    # Ensure main window is visible before showing modal dialog
    if mw and mw.isVisible():
        print(f"Showing breathing dialog for {target_cycles} cycles.")
        # Pass target_cycles to the dialog
        dialog = BreathingDialog(target_cycles, mw)
        result = dialog.exec() # Show modally
        if result == QDialog.DialogCode.Accepted:
            print("Breathing exercise completed.")
            tooltip("呼吸训练完成！", period=2000) # "Breathing exercise complete!"
        else:
            print("Breathing exercise skipped or closed.")
            tooltip("呼吸训练已跳过。", period=2000) # "Breathing exercise skipped."
    else:
        print("Skipping breathing dialog: Main window not visible.")


# --- UI 辅助函数 ---

def show_timer_in_statusbar(show: bool):
    """Adds or removes the timer label from the Anki status bar."""
    global timer_label
    # Check addon enabled and status bar display enabled in config
    show_configured = config.get("show_statusbar_timer", True)
    addon_enabled = config.get("enabled", True)

    if show and addon_enabled and show_configured:
        if not timer_label:
            # Ensure executed on the main thread if called from hooks
            def add_widget():
                global timer_label
                if not timer_label: # Double check inside lambda
                    timer_label = QLabel("🍅 --:--")
                    try:
                        # addPermanentWidget takes widget, stretch factor (0=no stretch)
                        mw.statusBar().addPermanentWidget(timer_label, 0)
                        timer_label.show()
                        print("Status bar timer label added.")
                        # Update display immediately after adding
                        if pomodoro_timer: pomodoro_timer.update_display()
                    except Exception as e:
                        print(f"Error adding timer widget to status bar: {e}")
                        timer_label = None # Reset if failed
            # Schedule the UI update on the main thread
            mw.progress.timer(0, add_widget, False)

        # If label exists, ensure timer display is updated (might be needed if config changed)
        elif timer_label and pomodoro_timer and pomodoro_timer.isActive():
             pomodoro_timer.update_display()

    elif timer_label:
        # Ensure executed on the main thread
        def remove_widget():
            global timer_label
            if timer_label:
                try:
                    mw.statusBar().removeWidget(timer_label)
                    timer_label.deleteLater() # Schedule for deletion
                    print("Status bar timer label removed.")
                except Exception as e:
                    print(f"Error removing timer widget from status bar: {e}")
                finally:
                    timer_label = None # Clear reference
        # Schedule the UI update on the main thread
        mw.progress.timer(0, remove_widget, False)


# --- 配置窗口 (显示循环次数和预计时间) ---
class ConfigDialog(QDialog):
    """Configuration dialog for Pomodoro and Breathing settings."""
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("番茄钟 & 呼吸设置")
        self.layout = QVBoxLayout(self)
        self.phase_widgets = {} # Store phase widgets {key: {"checkbox": QCheckBox, "spinbox": QSpinBox}}

        # --- General Settings ---
        general_group = QGroupBox("常规设置")
        general_layout = QVBoxLayout()

        self.enable_checkbox = QCheckBox("启用番茄钟插件", self)
        self.enable_checkbox.setChecked(config.get("enabled", True))
        general_layout.addWidget(self.enable_checkbox)

        self.show_timer_checkbox = QCheckBox("在状态栏显示计时器", self)
        self.show_timer_checkbox.setChecked(config.get("show_statusbar_timer", True))
        general_layout.addWidget(self.show_timer_checkbox)

        pomo_layout = QHBoxLayout()
        pomo_label = QLabel("番茄钟时长 (分钟):", self)
        self.pomo_spinbox = QSpinBox(self)
        self.pomo_spinbox.setMinimum(1)
        self.pomo_spinbox.setMaximum(180) # Increased max
        self.pomo_spinbox.setValue(config.get("pomodoro_minutes", DEFAULT_POMODORO_MINUTES))
        pomo_layout.addWidget(pomo_label)
        pomo_layout.addWidget(self.pomo_spinbox)
        general_layout.addLayout(pomo_layout)

        general_group.setLayout(general_layout)
        self.layout.addWidget(general_group)

        # --- Breathing Settings ---
        breathing_group = QGroupBox("呼吸训练设置")
        breathing_layout = QVBoxLayout()

        # Number of Cycles Input
        cycles_layout = QHBoxLayout()
        cycles_label = QLabel("呼吸循环次数:", self) # Changed label
        self.cycles_spinbox = QSpinBox(self)
        self.cycles_spinbox.setMinimum(0) # Allow 0 cycles to disable breathing part
        self.cycles_spinbox.setMaximum(50) # Set a reasonable max
        self.cycles_spinbox.setValue(config.get("breathing_cycles", DEFAULT_BREATHING_CYCLES))
        cycles_layout.addWidget(cycles_label)
        cycles_layout.addWidget(self.cycles_spinbox)
        breathing_layout.addLayout(cycles_layout)

        # Estimated Time Label
        self.estimated_time_label = QLabel("预计时间: --:--", self)
        self.estimated_time_label.setStyleSheet("font-style: italic; color: grey;")
        breathing_layout.addWidget(self.estimated_time_label)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        breathing_layout.addWidget(line)

        breathing_layout.addWidget(QLabel("每阶段设置:")) # Header for phases

        # Per-phase settings (Inhale, Hold, Exhale)
        for phase in PHASES:
            key = phase["key"]
            phase_layout = QHBoxLayout()

            # Checkbox to enable/disable the phase
            chk = QCheckBox(f"{phase['label']}", self)
            chk.setChecked(config.get(f"{key}_enabled", phase['default_enabled']))

            # Spinbox for phase duration
            spn = QSpinBox(self)
            spn.setMinimum(0) # Allow 0 second duration for a phase
            spn.setMaximum(60)
            spn.setValue(config.get(f"{key}_duration", phase['default_duration']))
            spn.setSuffix(" 秒") # " seconds" suffix

            # Enable/disable spinbox based on checkbox state
            spn.setEnabled(chk.isChecked())
            chk.toggled.connect(spn.setEnabled)

            phase_layout.addWidget(chk)
            phase_layout.addWidget(spn)
            # phase_layout.addWidget(QLabel("秒")) # Suffix added to spinbox instead

            breathing_layout.addLayout(phase_layout)
            self.phase_widgets[key] = {"checkbox": chk, "spinbox": spn}

            # Connect changes in this phase's controls to update the estimated time
            chk.toggled.connect(self._update_estimated_time)
            spn.valueChanged.connect(self._update_estimated_time)

        # Connect cycles spinbox change to update estimated time
        self.cycles_spinbox.valueChanged.connect(self._update_estimated_time)

        breathing_group.setLayout(breathing_layout)
        self.layout.addWidget(breathing_group)

        # --- Dialog Buttons (Save/Cancel) ---
        # Use standard buttons for consistency
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self
        )
        button_box.accepted.connect(self.accept) # Save triggers accept
        button_box.rejected.connect(self.reject) # Cancel triggers reject
        self.layout.addWidget(button_box)

        self.setLayout(self.layout)

        # Set initial estimated time based on loaded config
        self._update_estimated_time()

    def _update_estimated_time(self):
        """Calculates and updates the estimated breathing time label."""
        try:
            target_cycles = self.cycles_spinbox.value()
            single_cycle_duration = 0
            any_phase_active = False

            # Calculate duration of one cycle based on *currently selected* values
            for key, widgets in self.phase_widgets.items():
                if widgets["checkbox"].isChecked():
                    single_cycle_duration += widgets["spinbox"].value()
                    any_phase_active = True

            if not any_phase_active or target_cycles <= 0:
                self.estimated_time_label.setText("预计时间: --:-- (无启用阶段或循环)")
                return

            total_seconds = single_cycle_duration * target_cycles
            mins, secs = divmod(total_seconds, 60)
            self.estimated_time_label.setText(f"预计时间: {mins:02d}:{secs:02d}")

        except Exception as e:
            # Log error and show feedback in the UI
            print(f"Error updating estimated time: {e}")
            self.estimated_time_label.setText("预计时间: 计算错误")


    def accept(self):
        """Saves the configuration and closes the dialog."""
        print("Saving configuration...")
        # Save general settings
        config["enabled"] = self.enable_checkbox.isChecked()
        config["show_statusbar_timer"] = self.show_timer_checkbox.isChecked()
        config["pomodoro_minutes"] = self.pomo_spinbox.value()
        config["breathing_cycles"] = self.cycles_spinbox.value() # Save cycles

        # Save phase settings
        for key, widgets in self.phase_widgets.items():
            config[f"{key}_enabled"] = widgets["checkbox"].isChecked()
            config[f"{key}_duration"] = widgets["spinbox"].value()

        save_config()
        print("Configuration saved.")

        # Apply changes immediately
        # Update status bar visibility based on new config
        show_timer_in_statusbar(pomodoro_timer and pomodoro_timer.isActive())

        # If plugin was just disabled, stop the timer if it's running
        if not config["enabled"] and pomodoro_timer and pomodoro_timer.isActive():
             print("Plugin disabled, stopping active Pomodoro timer.")
             pomodoro_timer.stop_timer()
        # If plugin was just enabled and we are in review, start the timer
        elif config["enabled"] and mw.state == "review" and pomodoro_timer and not pomodoro_timer.isActive():
            print("Plugin enabled while in review, starting timer.")
            pomodoro_timer.start_timer(config.get("pomodoro_minutes", DEFAULT_POMODORO_MINUTES))


        super().accept() # Close the dialog

    # No special action needed on reject, just close
    # def reject(self):
    #     super().reject()


def show_config_dialog():
    """Creates and shows the configuration dialog."""
    # Ensure config is loaded before showing dialog
    if config is None:
        load_config()
    dialog = ConfigDialog(mw)
    dialog.exec() # Show modally


# --- 初始化和注册 ---
def setup_plugin():
    """Loads config, sets up hooks, and adds menu item."""
    global config
    print("Setting up Pomodoro & Breathing Addon...")
    config = load_config()

    # Register hooks
    # Note: Use reviewer_will_start_review is often better than did_show_question
    # as it fires once per review session start. did_show_question fires per card.
    # Let's stick with did_show_question for now as per original code, but consider changing.
    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_start)
    gui_hooks.state_did_change.append(on_state_did_change)

    # Add menu item
    action = QAction("番茄钟 & 呼吸设置...", mw) # "Pomodoro & Breathing Settings..."
    action.triggered.connect(show_config_dialog)
    if hasattr(mw, 'form') and hasattr(mw.form, 'menuTools'):
        mw.form.menuTools.addAction(action)
        print("Menu item added to Tools menu.")
    else:
        print("Warning: Could not add Pomodoro menu item (menuTools not found).")

    # Initial status bar setup if enabled and timer exists (e.g., addon reloaded)
    if pomodoro_timer and pomodoro_timer.isActive():
        show_timer_in_statusbar(True)
    elif timer_label: # If label exists but timer shouldn't be shown, remove it
        show_timer_in_statusbar(False)

    print("Pomodoro & Breathing Addon setup complete.")


# --- 启动插件 ---
# This code runs when Anki loads the addon
if __name__ != "__main__":
    # Use mw.progress.timer to ensure setup runs after Anki is fully initialized
    mw.progress.timer(100, setup_plugin, False) # Run once after 100ms delay