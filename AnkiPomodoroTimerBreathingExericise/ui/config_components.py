from aqt import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from ..constants import PHASES, Defaults
from ..translator import _
from .CircularTimer.timer_factory import list_timer_styles


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

        # Work across decks checkbox
        self.widgets["work_across_decks"] = QCheckBox(_("全局计时器"), parent)
        self.widgets["work_across_decks"].setChecked(
            self.config.get("work_across_decks", False)
        )
        layout.addWidget(self.widgets["work_across_decks"])

        # Display options
        display_layout = QVBoxLayout()
        self.widgets["show_timer"] = QCheckBox(_("显示圆形计时器"), parent)
        self.widgets["show_timer"].setChecked(
            self.config.get("show_circular_timer", True)
        )
        display_layout.addWidget(self.widgets["show_timer"])

        ## Circular timer style
        circular_style_label = QLabel(_("圆形计时器样式:"), parent)
        self.widgets["circular_timer_style"] = QComboBox(parent)
        self.widgets["circular_timer_style"].addItems(list_timer_styles())
        self.widgets["circular_timer_style"].setCurrentText(
            self.config.get("circular_timer_style", "default")
        )
        display_layout.addWidget(circular_style_label)
        display_layout.addWidget(self.widgets["circular_timer_style"])

        # Window position
        position_layout = QHBoxLayout()
        position_label = QLabel(_("计时器窗口位置:"), parent)
        self.widgets["position"] = QComboBox(parent)
        self.widgets["position"].addItems(
            [_("左上角"), _("右上角"), _("左下角"), _("右下角")]
        )
        self.widgets["position"].setCurrentText(
            self.config.get("timer_position", _("左上角"))
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
            self.config.get("pomodoro_minutes", Defaults.POMODORO_MINUTES)
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
            "circular_timer_style": self.widgets["circular_timer_style"].currentText(),
            "timer_position": self.widgets["position"].currentText(),
            "pomodoros_before_long_break": self.widgets["streak"].value(),
            "pomodoro_minutes": self.widgets["pomodoro"].value(),
            "max_break_duration": self.widgets["max_break"].value()
            * 60,  # Convert to seconds
            "work_across_decks": self.widgets["work_across_decks"].isChecked(),
        }


class BreathingSettings:
    """Handles UI components and logic for breathing settings"""

    def __init__(self, config):
        self.config = config
        self.widgets = {}
        self.phase_widgets = {}

    def create_ui(self, parent):
        """Creates UI components for breathing settings section"""
        group = QGroupBox(_("呼吸训练设置"))
        layout = QVBoxLayout()

        # Breathing cycles
        cycles_layout = QHBoxLayout()
        cycles_label = QLabel(_("目标循环次数:"), parent)
        self.widgets["cycles"] = QSpinBox(parent)
        self.widgets["cycles"].setMinimum(1)
        self.widgets["cycles"].setMaximum(100)
        self.widgets["cycles"].setValue(
            self.config.get("breathing_cycles", Defaults.BREATHING_CYCLES)
        )
        cycles_layout.addWidget(cycles_label)
        cycles_layout.addWidget(self.widgets["cycles"])
        layout.addLayout(cycles_layout)

        # Phase settings
        phases_group = QGroupBox(_("呼吸阶段设置"))
        phases_layout = QVBoxLayout()

        for phase_def in PHASES:
            key = phase_def["key"]
            label_text = phase_def["label"]
            default_enabled = phase_def["default_enabled"]
            default_duration = phase_def["default_duration"]
            default_audio = self.config.get(
                f"{key}_audio", phase_def.get("default_audio", "")
            )  # 获取默认音频

            phase_layout = QHBoxLayout()
            checkbox = QCheckBox(label_text, parent)
            checkbox.setChecked(self.config.get(f"{key}_enabled", default_enabled))

            spinbox = QSpinBox(parent)
            spinbox.setMinimum(0)  # Allow 0 duration
            spinbox.setMaximum(60)
            spinbox.setValue(self.config.get(f"{key}_duration", default_duration))
            spinbox.setEnabled(checkbox.isChecked())
            checkbox.toggled.connect(spinbox.setEnabled)

            audio_button = QPushButton(_("选择音频"), parent)
            audio_label = QLabel(
                default_audio or _("未选择"), parent
            )  # 显示当前选择或提示
            audio_label.setWordWrap(True)  # 允许换行
            audio_button.clicked.connect(
                lambda _, k=key, lbl=audio_label: self._select_audio_file(k, lbl)
            )
            audio_button.setEnabled(checkbox.isChecked())
            checkbox.toggled.connect(audio_button.setEnabled)

            phase_layout.addWidget(checkbox)
            phase_layout.addWidget(QLabel(_("持续时间:"), parent))
            phase_layout.addWidget(spinbox)
            phase_layout.addWidget(QLabel(_("秒"), parent))
            phase_layout.addWidget(audio_button)
            phase_layout.addWidget(audio_label)

            phases_layout.addLayout(phase_layout)

            self.phase_widgets[key] = {
                "checkbox": checkbox,
                "spinbox": spinbox,
                "audio_button": audio_button,
                "audio_label": audio_label,
            }

        phases_group.setLayout(phases_layout)
        layout.addWidget(phases_group)

        # Estimated time label
        self.widgets["estimated_time"] = QLabel(_("预计时间: --:--"), parent)
        self.widgets["estimated_time"].setStyleSheet("font-style: italic; color: grey;")
        layout.addWidget(self.widgets["estimated_time"])

        group.setLayout(layout)
        return group

    def _select_audio_file(self, phase_key, label_widget: QLabel):
        """Opens a file dialog to select an audio file for a phase."""
        # Anki's sound module primarily supports WAV and MP3
        file_path = QFileDialog.getOpenFileName(
            None,  # Parent
            _("选择 {phase_label} 阶段的音频文件").format(phase_label=phase_key),
            "",  # Start directory (empty means last used or default)
            _("音频文件 (*.wav *.mp3 *.opus *.ogg);;所有文件 (*)"),  # Filter
        )
        # getOpenFileName returns a tuple (filepath, filter)
        selected_file_path = file_path[0]
        if selected_file_path:
            label_widget.setText(selected_file_path)
            # Store the selected path temporarily until saved
            # We'll retrieve it in get_values
        else:
            # If user cancels, clear the selection
            label_widget.setText(_("未选择"))

    def get_values(self):
        """Gets values from breathing settings"""
        values = {
            "breathing_cycles": self.widgets["cycles"].value(),
        }
        for key, widgets in self.phase_widgets.items():
            values[f"{key}_enabled"] = widgets["checkbox"].isChecked()
            values[f"{key}_duration"] = widgets["spinbox"].value()

            audio_path = widgets["audio_label"].text()
            # Only save if a file is actually selected (not the default text)
            if audio_path != _("未选择"):
                values[f"{key}_audio"] = audio_path
            else:
                values[f"{key}_audio"] = ""  # Save empty string if no file selected

        return values
