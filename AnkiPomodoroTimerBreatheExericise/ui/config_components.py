from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QSpinBox,
    QFrame,
    QGroupBox,
    QComboBox,
)
from ..constants import PHASES, DEFAULT_BREATHING_CYCLES


class GeneralSettings:
    """Handles UI components and logic for general settings"""

    def __init__(self, config):
        self.config = config
        self.widgets = {}

    def create_ui(self, parent):
        """Creates UI components for general settings section"""
        group = QGroupBox("常规设置")
        layout = QVBoxLayout()

        # Enable plugin checkbox
        self.widgets["enable"] = QCheckBox("启用番茄钟插件", parent)
        self.widgets["enable"].setChecked(self.config.get("enabled", True))
        layout.addWidget(self.widgets["enable"])

        # Display options
        display_layout = QVBoxLayout()
        self.widgets["show_timer"] = QCheckBox("显示圆形计时器", parent)
        self.widgets["show_timer"].setChecked(
            self.config.get("show_circular_timer", True)
        )
        display_layout.addWidget(self.widgets["show_timer"])

        # Window position
        position_layout = QHBoxLayout()
        position_label = QLabel("计时器窗口位置:", parent)
        self.widgets["position"] = QComboBox(parent)
        self.widgets["position"].addItems(["左上角", "右上角", "左下角", "右下角"])
        self.widgets["position"].setCurrentText(
            self.config.get("timer_position", "左上角")
        )
        position_layout.addWidget(position_label)
        position_layout.addWidget(self.widgets["position"])

        layout.addLayout(display_layout)
        layout.addLayout(position_layout)

        # Other general settings...

        group.setLayout(layout)
        return group

    def get_values(self):
        """Gets values from general settings"""
        return {
            "enabled": self.widgets["enable"].isChecked(),
            "show_circular_timer": self.widgets["show_timer"].isChecked(),
            "timer_position": self.widgets["position"].currentText(),
        }


class BreathingSettings:
    """Handles UI components and logic for breathing exercises"""

    def __init__(self, config):
        self.config = config
        self.widgets = {}
        self.phase_widgets = {}

    def create_ui(self, parent):
        """Creates UI components for breathing exercises section"""
        group = QGroupBox("呼吸训练设置")
        layout = QVBoxLayout()

        # Breathing cycles count
        cycles_layout = QHBoxLayout()
        cycles_label = QLabel("呼吸循环次数:", parent)
        self.widgets["cycles"] = QSpinBox(parent)
        self.widgets["cycles"].setMinimum(0)
        self.widgets["cycles"].setMaximum(50)
        self.widgets["cycles"].setValue(
            self.config.get("breathing_cycles", DEFAULT_BREATHING_CYCLES)
        )
        cycles_layout.addWidget(cycles_label)
        cycles_layout.addWidget(self.widgets["cycles"])
        layout.addLayout(cycles_layout)

        # Estimated time label
        self.widgets["estimated_time"] = QLabel("预计时间: --:--", parent)
        self.widgets["estimated_time"].setStyleSheet("font-style: italic; color: grey;")
        layout.addWidget(self.widgets["estimated_time"])

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        layout.addWidget(QLabel("每阶段设置:"))

        # Phase settings
        for phase in PHASES:
            key = phase["key"]
            phase_layout = QHBoxLayout()

            # Enable checkbox
            chk = QCheckBox(f"{phase['label']}", parent)
            chk.setChecked(self.config.get(f"{key}_enabled", phase["default_enabled"]))

            # Duration
            spn = QSpinBox(parent)
            spn.setMinimum(0)
            spn.setMaximum(60)
            spn.setValue(self.config.get(f"{key}_duration", phase["default_duration"]))
            phase_layout.addWidget(QLabel("秒", parent))

            # Set spinbox availability based on checkbox state
            spn.setEnabled(chk.isChecked())
            chk.toggled.connect(spn.setEnabled)

            phase_layout.addWidget(chk)
            phase_layout.addWidget(spn)

            layout.addLayout(phase_layout)
            self.phase_widgets[key] = {"checkbox": chk, "spinbox": spn}

        group.setLayout(layout)
        return group

    def get_values(self):
        """Gets values from breathing exercises settings"""
        values = {"breathing_cycles": self.widgets["cycles"].value()}

        for key, widgets in self.phase_widgets.items():
            values[f"{key}_enabled"] = widgets["checkbox"].isChecked()
            values[f"{key}_duration"] = widgets["spinbox"].value()

        return values
