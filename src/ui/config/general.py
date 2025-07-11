from typing import Any

from aqt import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...config import AppConfig
from ...config.enums import StatusBarFormat, TimerPosition
from ...config.languages import LanguageCode
from ...translator import _
from ..CircularTimer.core.factory import list_timer_styles


class GeneralSettings:
    """处理常规设置的UI组件和逻辑"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.enable_checkbox: QCheckBox | None = None
        self.work_across_decks_checkbox: QCheckBox | None = None
        self.show_timer_checkbox: QCheckBox | None = None
        self.circular_timer_style_combobox: QComboBox | None = None
        self.timer_position_combobox: QComboBox | None = None
        self.streak_spinbox: QSpinBox | None = None
        self.pomodoro_spinbox: QSpinBox | None = None
        self.long_break_minutes_spinbox: QSpinBox | None = None
        self.max_break_spinbox: QSpinBox | None = None
        self.language_combobox: QComboBox | None = None
        self.statusbar_format_combobox: QComboBox | None = None

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
