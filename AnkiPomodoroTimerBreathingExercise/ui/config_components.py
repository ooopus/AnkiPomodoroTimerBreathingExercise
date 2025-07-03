import os
from dataclasses import dataclass
from typing import Any, Optional, Union

from aqt import (
    QCheckBox,
    QComboBox,
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

from ..config import AppConfig
from ..config.enums import PHASES, StatusBarFormat, TimerPosition
from ..config.languages import LanguageCode
from ..translator import _
from .CircularTimer.timer_factory import list_timer_styles


class GeneralSettings:
    """处理常规设置的UI组件和逻辑"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.enable_checkbox: Optional[QCheckBox] = None
        self.work_across_decks_checkbox: Optional[QCheckBox] = None
        self.show_timer_checkbox: Optional[QCheckBox] = None
        self.circular_timer_style_combobox: Optional[QComboBox] = None
        self.timer_position_combobox: Optional[QComboBox] = None
        self.streak_spinbox: Optional[QSpinBox] = None
        self.pomodoro_spinbox: Optional[QSpinBox] = None
        self.long_break_minutes_spinbox: Optional[QSpinBox] = None
        self.max_break_spinbox: Optional[QSpinBox] = None
        self.language_combobox: Optional[QComboBox] = None
        self.statusbar_format_combobox: Optional[QComboBox] = None

    def create_ui(self, parent: QWidget) -> QGroupBox:
        """创建常规设置部分的UI组件"""
        group = QGroupBox(_("常规设置"))
        main_layout = QVBoxLayout()
        grid_layout = QGridLayout()
        grid_layout.setColumnStretch(1, 1)  # 让第二列（输入控件列）可以伸展
        grid_layout.setColumnMinimumWidth(0, 120)  # 给标签列一个最小宽度

        row = 0

        # 启用插件
        self.enable_checkbox = QCheckBox(_("启用番茄钟插件"), parent)
        self.enable_checkbox.setChecked(self.config.enabled)
        grid_layout.addWidget(self.enable_checkbox, row, 0, 1, 2)
        row += 1

        # 语言选择
        language_label = QLabel(_("语言:"), parent)
        self.language_combobox = QComboBox(parent)
        self.language_combobox.addItems([code.display_name for code in LanguageCode])
        self.language_combobox.setCurrentText(self.config.language.display_name)
        grid_layout.addWidget(language_label, row, 0)
        grid_layout.addWidget(self.language_combobox, row, 1)
        row += 1

        # 全局计时器
        self.work_across_decks_checkbox = QCheckBox(_("全局计时器"), parent)
        self.work_across_decks_checkbox.setChecked(self.config.work_across_decks)
        grid_layout.addWidget(self.work_across_decks_checkbox, row, 0, 1, 2)
        row += 1

        # 显示圆形计时器
        self.show_timer_checkbox = QCheckBox(_("显示圆形计时器"), parent)
        self.show_timer_checkbox.setChecked(self.config.show_circular_timer)
        grid_layout.addWidget(self.show_timer_checkbox, row, 0, 1, 2)
        row += 1

        # 圆形计时器样式
        circular_style_label = QLabel(_("圆形计时器样式:"), parent)
        self.circular_timer_style_combobox = QComboBox(parent)
        self.circular_timer_style_combobox.addItems(
            [style.value for style in list_timer_styles()]
        )
        self.circular_timer_style_combobox.setCurrentText(
            self.config.circular_timer_style
        )
        grid_layout.addWidget(circular_style_label, row, 0)
        grid_layout.addWidget(self.circular_timer_style_combobox, row, 1)
        row += 1

        # 计时器窗口位置
        position_label = QLabel(_("计时器窗口位置:"), parent)
        self.timer_position_combobox = QComboBox(parent)
        self.timer_position_combobox.addItems(
            [pos.display_name for pos in TimerPosition]
        )
        self.timer_position_combobox.setCurrentText(
            self.config.timer_position.display_name
        )
        grid_layout.addWidget(position_label, row, 0)
        grid_layout.addWidget(self.timer_position_combobox, row, 1)
        row += 1

        # 连胜上限
        streak_label = QLabel(_("连胜上限:"), parent)
        self.streak_spinbox = QSpinBox(parent)
        self.streak_spinbox.setMinimum(1)
        self.streak_spinbox.setMaximum(100)
        self.streak_spinbox.setValue(self.config.pomodoros_before_long_break)
        streak_unit_label = QLabel(_("个番茄钟"), parent)
        streak_layout = QHBoxLayout()
        streak_layout.addWidget(self.streak_spinbox)
        streak_layout.addWidget(streak_unit_label)
        grid_layout.addWidget(streak_label, row, 0)
        grid_layout.addLayout(streak_layout, row, 1)
        row += 1

        streak_hint = QLabel(_("连续完成指定数量的番茄钟后，将进行长休息"), parent)
        streak_hint.setStyleSheet("font-style: italic; color: grey;")
        grid_layout.addWidget(streak_hint, row, 1, 1, 1)
        row += 1

        # 番茄钟时长
        pomo_label = QLabel(_("番茄钟时长:"), parent)
        self.pomodoro_spinbox = QSpinBox(parent)
        self.pomodoro_spinbox.setMinimum(1)
        self.pomodoro_spinbox.setMaximum(180)
        self.pomodoro_spinbox.setValue(self.config.pomodoro_minutes)
        pomo_unit_label = QLabel(_("分钟"), parent)
        pomo_layout = QHBoxLayout()
        pomo_layout.addWidget(self.pomodoro_spinbox)
        pomo_layout.addWidget(pomo_unit_label)
        grid_layout.addWidget(pomo_label, row, 0)
        grid_layout.addLayout(pomo_layout, row, 1)
        row += 1

        # 长休息时长
        long_break_label = QLabel(_("长休息时长:"), parent)
        self.long_break_minutes_spinbox = QSpinBox(parent)
        self.long_break_minutes_spinbox.setMinimum(1)
        self.long_break_minutes_spinbox.setMaximum(60)
        self.long_break_minutes_spinbox.setValue(self.config.long_break_minutes)
        long_break_unit_label = QLabel(_("分钟"), parent)
        long_break_layout = QHBoxLayout()
        long_break_layout.addWidget(self.long_break_minutes_spinbox)
        long_break_layout.addWidget(long_break_unit_label)
        grid_layout.addWidget(long_break_label, row, 0)
        grid_layout.addLayout(long_break_layout, row, 1)
        row += 1

        # 休息时间上限
        max_break_label = QLabel(_("休息时间上限:"), parent)
        self.max_break_spinbox = QSpinBox(parent)
        self.max_break_spinbox.setMinimum(1)
        self.max_break_spinbox.setMaximum(120)
        self.max_break_spinbox.setValue(self.config.max_break_duration // 60)
        max_break_unit_label = QLabel(_("分钟"), parent)
        max_break_layout = QHBoxLayout()
        max_break_layout.addWidget(self.max_break_spinbox)
        max_break_layout.addWidget(max_break_unit_label)
        grid_layout.addWidget(max_break_label, row, 0)
        grid_layout.addLayout(max_break_layout, row, 1)
        row += 1

        max_break_hint = QLabel(_("超过休息时间上限后，累计的番茄钟将归零"), parent)
        max_break_hint.setStyleSheet("font-style: italic; color: grey;")
        grid_layout.addWidget(max_break_hint, row, 1, 1, 1)
        row += 1

        main_layout.addLayout(grid_layout)

        # 状态栏设置
        statusbar_group = QGroupBox(_("状态栏显示设置"))
        statusbar_layout = QHBoxLayout()
        statusbar_label = QLabel(_("选择状态栏显示格式："))
        self.statusbar_format_combobox = QComboBox()
        for format_option in StatusBarFormat:
            self.statusbar_format_combobox.addItem(
                format_option.display_name, format_option
            )

        current_format = self.config.statusbar_format
        index = self.statusbar_format_combobox.findData(current_format)
        if index >= 0:
            self.statusbar_format_combobox.setCurrentIndex(index)

        statusbar_layout.addWidget(statusbar_label)
        statusbar_layout.addWidget(self.statusbar_format_combobox)
        statusbar_group.setLayout(statusbar_layout)

        main_layout.addWidget(statusbar_group)
        main_layout.addStretch()

        group.setLayout(main_layout)
        return group

    def get_values(self) -> dict[str, Any]:
        """从常规设置获取值"""
        assert self.language_combobox is not None
        assert self.timer_position_combobox is not None
        assert self.enable_checkbox is not None
        assert self.show_timer_checkbox is not None
        assert self.circular_timer_style_combobox is not None
        assert self.streak_spinbox is not None
        assert self.pomodoro_spinbox is not None
        assert self.long_break_minutes_spinbox is not None
        assert self.max_break_spinbox is not None
        assert self.work_across_decks_checkbox is not None
        assert self.statusbar_format_combobox is not None

        position_map_rev = {pos.display_name: pos for pos in TimerPosition}
        selected_position_text = self.timer_position_combobox.currentText()
        position_key = position_map_rev.get(
            selected_position_text, TimerPosition.TOP_RIGHT
        )

        language_map = {lang.display_name: lang for lang in LanguageCode}
        selected_language_text = self.language_combobox.currentText()
        language_key = language_map.get(selected_language_text, LanguageCode.AUTO)

        return {
            "enabled": self.enable_checkbox.isChecked(),
            "show_circular_timer": self.show_timer_checkbox.isChecked(),
            "circular_timer_style": self.circular_timer_style_combobox.currentText(),
            "timer_position": position_key,
            "pomodoros_before_long_break": self.streak_spinbox.value(),
            "pomodoro_minutes": self.pomodoro_spinbox.value(),
            "long_break_minutes": self.long_break_minutes_spinbox.value(),
            "max_break_duration": self.max_break_spinbox.value() * 60,
            "work_across_decks": self.work_across_decks_checkbox.isChecked(),
            "language": language_key,
            "statusbar_format": self.statusbar_format_combobox.currentData(),
        }


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
        self.cycles_spinbox: Optional[QSpinBox] = None
        self.estimated_time_label: Optional[QLabel] = None
        self.phase_uis: dict[str, PhaseUI] = {}

    def create_ui(self, parent: QWidget) -> QGroupBox:
        """创建呼吸设置部分的UI组件"""
        group = QGroupBox(_("呼吸训练设置"))
        layout = QVBoxLayout()

        cycles_layout = QHBoxLayout()
        cycles_label = QLabel(_("目标循环次数:"), parent)
        self.cycles_spinbox = QSpinBox(parent)
        self.cycles_spinbox.setMinimum(1)
        self.cycles_spinbox.setMaximum(100)
        self.cycles_spinbox.setValue(self.config.breathing_cycles)
        cycles_layout.addWidget(cycles_label)
        cycles_layout.addWidget(self.cycles_spinbox)
        layout.addLayout(cycles_layout)

        phases_group = QGroupBox(_("呼吸阶段设置"))
        phases_layout = QGridLayout()
        phases_layout.setColumnStretch(5, 1)

        for i, phase_def in enumerate(PHASES):
            key = phase_def.key
            label_text = phase_def.label

            is_enabled = getattr(
                self.config, f"{key}_enabled", phase_def.default_enabled
            )
            duration = getattr(
                self.config, f"{key}_duration", phase_def.default_duration
            )
            audio = getattr(self.config, f"{key}_audio", phase_def.default_audio)

            checkbox = QCheckBox(label_text, parent)
            checkbox.setChecked(is_enabled)

            spinbox = QSpinBox(parent)
            spinbox.setMinimum(0)
            spinbox.setMaximum(60)
            spinbox.setValue(duration)
            spinbox.setEnabled(checkbox.isChecked())

            audio_button = QPushButton(_("选择音频"), parent)
            audio_label = QLabel(os.path.basename(audio) if audio else _("未选择"), parent)
            audio_label.setWordWrap(True)
            audio_label.setToolTip(audio)
            audio_label.setProperty("filePath", audio)
            audio_button.setEnabled(checkbox.isChecked())

            checkbox.toggled.connect(spinbox.setEnabled)
            checkbox.toggled.connect(audio_button.setEnabled)
            audio_button.clicked.connect(
                lambda _, k=key, lbl=audio_label: self._select_audio_file(k, lbl)
            )

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

    def _select_audio_file(self, phase_key: str, label_widget: QLabel):
        """打开文件对话框为某个阶段选择音频文件。"""
        file_path, __ = QFileDialog.getOpenFileName(
            None,
            _("选择 {phase_label} 阶段的音频文件").format(phase_label=phase_key),
            "",
            _("音频文件 (*.wav *.mp3 *.opus *.ogg);;所有文件 (*)"),
        )
        if file_path:
            file_name = os.path.basename(file_path)
            label_widget.setText(file_name)
            label_widget.setToolTip(file_path)
            label_widget.setProperty("filePath", file_path)
        else:
            label_widget.setText(_("未选择"))
            label_widget.setToolTip("")
            label_widget.setProperty("filePath", "")

    def get_values(self) -> dict[str, Any]:
        """从呼吸设置获取值"""
        assert self.cycles_spinbox is not None
        values: dict[str, Union[int, str, bool]] = {
            "breathing_cycles": self.cycles_spinbox.value()
        }
        for key, ui in self.phase_uis.items():
            values[f"{key}_enabled"] = ui.checkbox.isChecked()
            values[f"{key}_duration"] = ui.spinbox.value()
            audio_path = ui.audio_label.property("filePath") or ""
            values[f"{key}_audio"] = audio_path
        return values
