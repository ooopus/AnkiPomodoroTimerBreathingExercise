import os
from dataclasses import dataclass
from typing import Any

from aqt import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    Qt,
    QVBoxLayout,
    QWidget,
)

from ...config import AppConfig
from ...config.enums import PHASES
from ...translator import _


@dataclass
class PhaseUI:
    """存储单个呼吸阶段的UI组件"""

    checkbox: QCheckBox
    spinbox: QSpinBox
    audio_button: QPushButton
    audio_label: QLabel


class BreathingSettings:
    """处理呼吸设置的UI组件和逻辑"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.cycles_spinbox: QSpinBox | None = None
        self.estimated_time_label: QLabel | None = None
        self.phase_uis: dict[str, PhaseUI] = {}
        self.audio_paths: dict[str, str] = {}

    def create_ui(self, parent: QWidget) -> QGroupBox:
        """创建呼吸设置部分的UI组件"""
        group = QGroupBox(_("呼吸训练设置"))
        layout = QVBoxLayout()

        cycles_layout = QHBoxLayout()
        cycles_label = QLabel(_("目标循环次数:"), parent)
        self.cycles_spinbox = QSpinBox(parent)
        self.cycles_spinbox.setMinimum(1)
        self.cycles_spinbox.setMaximum(100)
        self.cycles_spinbox.setValue(self.config.breathing_cycles or 1)
        cycles_layout.addWidget(cycles_label)
        cycles_layout.addWidget(self.cycles_spinbox)
        layout.addLayout(cycles_layout)

        phases_group = QGroupBox(_("呼吸阶段设置"))
        phases_layout = QGridLayout()
        phases_layout.setColumnStretch(5, 1)

        for i, phase_def in enumerate(PHASES):
            key = phase_def.key.value
            label_text = phase_def.label

            is_enabled = getattr(
                self.config, f"{key}_enabled", phase_def.default_enabled
            )
            duration = getattr(
                self.config, f"{key}_duration", phase_def.default_duration
            )
            audio = getattr(self.config, f"{key}_audio", phase_def.default_audio)
            self.audio_paths[key] = audio or ""

            checkbox = QCheckBox(label_text, parent)
            checkbox.setChecked(is_enabled)

            spinbox = QSpinBox(parent)
            spinbox.setMinimum(0)
            spinbox.setMaximum(60)
            spinbox.setValue(duration)
            spinbox.setEnabled(checkbox.isChecked())

            audio_button = QPushButton(_("选择音频"), parent)
            audio_label = QLabel(
                os.path.basename(audio) if audio else _("未选择"), parent
            )
            audio_label.setWordWrap(True)
            audio_label.setToolTip(audio)
            audio_button.setEnabled(checkbox.isChecked())

            checkbox.toggled.connect(spinbox.setEnabled)
            checkbox.toggled.connect(audio_button.setEnabled)
            self._connect_audio_button(audio_button, key, audio_label)

            duration_label = QLabel(_("持续时间:"))
            duration_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )

            phases_layout.addWidget(checkbox, i, 0)
            phases_layout.addWidget(duration_label, i, 1)
            phases_layout.addWidget(spinbox, i, 2)
            phases_layout.addWidget(QLabel(_("秒")), i, 3)
            phases_layout.addWidget(audio_button, i, 4)
            phases_layout.addWidget(audio_label, i, 5)

            self.phase_uis[key] = PhaseUI(
                checkbox=checkbox,
                spinbox=spinbox,
                audio_button=audio_button,
                audio_label=audio_label,
            )

        self.estimated_time_label = QLabel(_("预计时间: --:--"), parent)
        self.estimated_time_label.setStyleSheet("font-style: italic; color: grey;")
        phases_layout.addWidget(
            self.estimated_time_label,
            phases_layout.rowCount(),
            0,
            1,
            -1,
            Qt.AlignmentFlag.AlignRight,
        )

        phases_group.setLayout(phases_layout)
        layout.addWidget(phases_group)
        layout.addStretch()

        group.setLayout(layout)
        return group

    def _connect_audio_button(
        self, button: QPushButton, phase_key: str, label_widget: QLabel
    ):
        """Connects the audio button's clicked signal to the file selection logic."""

        def on_click():
            self._select_audio_file(phase_key, label_widget)

        button.clicked.connect(on_click)

    def _select_audio_file(self, phase_key: str, label_widget: QLabel):
        """打开文件对话框为某个阶段选择音频文件。"""
        file_path, __ = QFileDialog.getOpenFileName(
            None,
            _("为 {phase_key} 阶段选择音频文件").format(phase_key=phase_key),
            "",
            _("音频文件 (*.wav *.mp3 *.opus *.ogg);;所有文件 (*)"),
        )
        if file_path:
            file_name = os.path.basename(file_path)
            label_widget.setText(file_name)
            label_widget.setToolTip(file_path)
            self.audio_paths[phase_key] = file_path
        else:
            label_widget.setText(_("未选择"))
            label_widget.setToolTip("")
            self.audio_paths[phase_key] = ""

    def get_values(self) -> dict[str, Any]:
        """从呼吸设置获取值"""
        assert self.cycles_spinbox is not None
        values: dict[str, int | str | bool] = {
            "breathing_cycles": self.cycles_spinbox.value()
        }
        for key, ui in self.phase_uis.items():
            values[f"{key}_enabled"] = ui.checkbox.isChecked()
            values[f"{key}_duration"] = ui.spinbox.value()
            values[f"{key}_audio"] = self.audio_paths.get(key, "")
        return values
