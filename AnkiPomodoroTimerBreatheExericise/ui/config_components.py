from aqt import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from ..constants import DEFAULT_BREATHING_CYCLES, DEFAULT_POMODORO_MINUTES, PHASES
from ..translator import _


class GeneralSettings:
    """Handles UI components and logic for general settings"""

    def __init__(self, config):
        self.config = config
        self.widgets = {}

    def create_ui(self, parent):
        """Creates UI components for general settings section"""
        group = QGroupBox(_("常规设置"))
        layout = QVBoxLayout()

        # Enable plugin checkbox
        self.widgets["enable"] = QCheckBox(_("启用番茄钟插件"), parent)
        self.widgets["enable"].setChecked(self.config.get("enabled", True))
        layout.addWidget(self.widgets["enable"])

        # Display options
        display_layout = QVBoxLayout()
        self.widgets["show_timer"] = QCheckBox(_("显示圆形计时器"), parent)
        self.widgets["show_timer"].setChecked(
            self.config.get("show_circular_timer", True)
        )
        display_layout.addWidget(self.widgets["show_timer"])

        # Window position
        position_layout = QHBoxLayout()
        position_label = QLabel(_("计时器窗口位置:"), parent)
        self.widgets["position"] = QComboBox(parent)
        self.widgets["position"].addItems(
            [_("左上角"), _("右上角"), _("左下角"), _("右下角")]
        )
        self.widgets["position"].setCurrentText(
            self.config.get("timer_position", "左上角")
        )
        position_layout.addWidget(position_label)
        position_layout.addWidget(self.widgets["position"])

        # Pomodoro streak settings
        streak_layout = QHBoxLayout()
        streak_label = QLabel(_("连胜上限:"), parent)
        self.widgets["streak"] = QSpinBox(parent)
        self.widgets["streak"].setMinimum(1)
        self.widgets["streak"].setMaximum(10)
        self.widgets["streak"].setValue(
            self.config.get("pomodoros_before_long_break", 4)
        )
        streak_label_unit = QLabel(_("个番茄钟"), parent)
        streak_layout.addWidget(streak_label)
        streak_layout.addWidget(self.widgets["streak"])
        streak_layout.addWidget(streak_label_unit)

        # Pomodoro duration
        pomo_layout = QHBoxLayout()
        pomo_label = QLabel(_("番茄钟时长:"), parent)
        self.widgets["pomodoro"] = QSpinBox(parent)
        self.widgets["pomodoro"].setMinimum(1)
        self.widgets["pomodoro"].setMaximum(180)
        self.widgets["pomodoro"].setValue(
            self.config.get("pomodoro_minutes", DEFAULT_POMODORO_MINUTES)
        )
        pomo_label_unit = QLabel(_("分钟"), parent)
        pomo_layout.addWidget(pomo_label)
        pomo_layout.addWidget(self.widgets["pomodoro"])
        pomo_layout.addWidget(pomo_label_unit)

        # Max break duration
        max_break_layout = QHBoxLayout()
        max_break_label = QLabel(_("休息时间上限:"), parent)
        self.widgets["max_break"] = QSpinBox(parent)
        self.widgets["max_break"].setMinimum(1)
        self.widgets["max_break"].setMaximum(120)
        self.widgets["max_break"].setValue(
            self.config.get("max_break_duration", 30 * 60) // 60
        )
        max_break_label_unit = QLabel(_("分钟"), parent)
        max_break_layout.addWidget(max_break_label)
        max_break_layout.addWidget(self.widgets["max_break"])
        max_break_layout.addWidget(max_break_label_unit)

        # Add hint labels
        streak_hint = QLabel(_("连续完成指定数量的番茄钟后，将进行长休息"), parent)
        streak_hint.setStyleSheet("font-style: italic; color: grey;")

        max_break_hint = QLabel(_("超过休息时间上限后，累计的番茄钟将归零"), parent)
        max_break_hint.setStyleSheet("font-style: italic; color: grey;")

        # Add all layouts
        layout.addLayout(display_layout)
        layout.addLayout(position_layout)
        layout.addLayout(streak_layout)
        layout.addWidget(streak_hint)
        layout.addLayout(pomo_layout)
        layout.addLayout(max_break_layout)
        layout.addWidget(max_break_hint)

        group.setLayout(layout)
        return group

    def get_values(self):
        """Gets values from general settings"""
        return {
            "enabled": self.widgets["enable"].isChecked(),
            "show_circular_timer": self.widgets["show_timer"].isChecked(),
            "timer_position": self.widgets["position"].currentText(),
            "pomodoros_before_long_break": self.widgets["streak"].value(),
            "pomodoro_minutes": self.widgets["pomodoro"].value(),
            "max_break_duration": self.widgets["max_break"].value()
            * 60,  # Convert to seconds
        }


class BreathingSettings:
    """Handles UI components and logic for breathing exercises"""

    def __init__(self, config):
        self.config = config
        self.widgets = {}
        self.phase_widgets = {}

    def create_ui(self, parent):
        """Creates UI components for breathing exercises section"""
        group = QGroupBox(_("呼吸训练设置"))
        layout = QVBoxLayout()

        # Breathing cycles count
        cycles_layout = QHBoxLayout()
        cycles_label = QLabel(_("呼吸循环次数:"), parent)
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
        self.widgets["estimated_time"] = QLabel(_("预计时间: --:--"), parent)
        self.widgets["estimated_time"].setStyleSheet("font-style: italic; color: grey;")
        layout.addWidget(self.widgets["estimated_time"])

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        layout.addWidget(QLabel(_("每阶段设置:")))

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
            phase_layout.addWidget(QLabel(_("秒"), parent))

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
