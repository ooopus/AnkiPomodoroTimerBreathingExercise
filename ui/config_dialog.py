from aqt import mw
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QSpinBox, QDialogButtonBox, QFrame, QGroupBox, QComboBox
)
from ..constants import (
    PHASES, 
    DEFAULT_POMODORO_MINUTES, 
    DEFAULT_BREATHING_CYCLES
)
from ..config import save_config, get_config, get_pomodoro_timer
from .statusbar import show_timer_in_statusbar

class ConfigDialog(QDialog):
    """Configuration dialog for Pomodoro and Breathing settings."""
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        
        # Use our config system instead of Anki's
        config = get_config()
        
        self.setWindowTitle("番茄钟 & 呼吸设置")
        self.layout = QVBoxLayout(self)
        self.phase_widgets = {} # Store phase widgets {key: {"checkbox": QCheckBox, "spinbox": QSpinBox}}

        # --- General Settings ---
        general_group = QGroupBox("常规设置")
        general_layout = QVBoxLayout()

        self.enable_checkbox = QCheckBox("启用番茄钟插件", self)
        self.enable_checkbox.setChecked(config.get("enabled", True))
        general_layout.addWidget(self.enable_checkbox)

        # 显示选项布局
        display_layout = QVBoxLayout()
        self.show_timer_checkbox = QCheckBox("在状态栏显示计时器", self)
        self.show_timer_checkbox.setChecked(config.get("show_statusbar_timer", True))
        self.show_circular_timer_checkbox = QCheckBox("显示圆形计时器", self)
        self.show_circular_timer_checkbox.setChecked(config.get("show_circular_timer", True))
        display_layout.addWidget(self.show_timer_checkbox)
        display_layout.addWidget(self.show_circular_timer_checkbox)
        
        # 窗口位置选项
        position_layout = QHBoxLayout()
        position_label = QLabel("计时器窗口位置:", self)
        self.position_combo = QComboBox(self)
        self.position_combo.addItems(["左上角", "右上角", "左下角", "右下角"])
        self.position_combo.setCurrentText(config.get("timer_position", "左上角"))
        position_layout.addWidget(position_label)
        position_layout.addWidget(self.position_combo)
        
        general_layout.addLayout(display_layout)
        general_layout.addLayout(position_layout)

        pomo_layout = QHBoxLayout()
        pomo_label = QLabel("番茄钟时长:", self)
        self.pomo_spinbox = QSpinBox(self)
        self.pomo_spinbox.setMinimum(1)
        self.pomo_spinbox.setMaximum(180)
        self.pomo_spinbox.setValue(config.get("pomodoro_minutes", DEFAULT_POMODORO_MINUTES))
        pomo_label_unit = QLabel("分钟", self)
        pomo_layout.addWidget(pomo_label)
        pomo_layout.addWidget(self.pomo_spinbox)
        pomo_layout.addWidget(pomo_label_unit)
        general_layout.addLayout(pomo_layout)

        general_group.setLayout(general_layout)
        self.layout.addWidget(general_group)

        # --- Breathing Settings ---
        breathing_group = QGroupBox("呼吸训练设置")
        breathing_layout = QVBoxLayout()

        # Number of Cycles Input
        cycles_layout = QHBoxLayout()
        cycles_label = QLabel("呼吸循环次数:", self)
        self.cycles_spinbox = QSpinBox(self)
        self.cycles_spinbox.setMinimum(0)
        self.cycles_spinbox.setMaximum(50)
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

        breathing_layout.addWidget(QLabel("每阶段设置:"))

        # Per-phase settings (Inhale, Hold, Exhale)
        for phase in PHASES:
            key = phase["key"]
            phase_layout = QHBoxLayout()

            # Checkbox to enable/disable the phase
            chk = QCheckBox(f"{phase['label']}", self)
            chk.setChecked(config.get(f"{key}_enabled", phase['default_enabled']))

            # Spinbox for phase duration
            spn = QSpinBox(self)
            spn.setMinimum(0)
            spn.setMaximum(60)
            spn.setValue(config.get(f"{key}_duration", phase['default_duration']))
            phase_layout.addWidget(QLabel("秒", self))

            # Enable/disable spinbox based on checkbox state
            spn.setEnabled(chk.isChecked())
            chk.toggled.connect(spn.setEnabled)

            phase_layout.addWidget(chk)
            phase_layout.addWidget(spn)

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
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
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
            print(f"Error updating estimated time: {e}")
            self.estimated_time_label.setText("预计时间: 计算错误")

    def accept(self):
        """Saves the configuration and closes the dialog."""
        print("Saving configuration...")
        config = get_config()
        
        # Save general settings
        config["enabled"] = self.enable_checkbox.isChecked()
        config["show_statusbar_timer"] = self.show_timer_checkbox.isChecked()
        config["show_circular_timer"] = self.show_circular_timer_checkbox.isChecked()
        config["timer_position"] = self.position_combo.currentText()
        config["pomodoro_minutes"] = self.pomo_spinbox.value()
        config["breathing_cycles"] = self.cycles_spinbox.value()
    
        # Save phase settings
        for key, widgets in self.phase_widgets.items():
            config[f"{key}_enabled"] = widgets["checkbox"].isChecked()
            config[f"{key}_duration"] = widgets["spinbox"].value()
    
        save_config()
        print("Configuration saved.")
    
        # Apply changes immediately
        timer = get_pomodoro_timer()
        show_timer_in_statusbar(timer and timer.isActive())
    
        if not config["enabled"] and timer and timer.isActive():
            print("Plugin disabled, stopping active Pomodoro timer.")
            timer.stop_timer()
        elif config["enabled"] and mw.state == "review" and timer and not timer.isActive():
            print("Plugin enabled while in review, starting timer.")
            timer.start_timer(config.get("pomodoro_minutes", DEFAULT_POMODORO_MINUTES))
    
        super().accept()