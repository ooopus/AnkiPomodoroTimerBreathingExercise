import dataclasses
from typing import override

from aqt import (
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    mw,
)
from aqt.utils import tooltip

from ..config import AppConfig
from ..state import get_pomodoro_manager, reload_config, update_and_save_config
from ..translator import _, set_language
from .config_components import BreathingSettings, GeneralSettings


class ConfigDialog(QDialog):
    """用于番茄钟和呼吸设置的配置对话框。"""

    def __init__(self, parent: QWidget = mw):
        super().__init__(parent or mw)

        self.config = reload_config()
        self.setWindowTitle(_("番茄钟/呼吸训练设置"))
        self._main_layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.general_tab = QWidget()
        self.breathing_tab = QWidget()

        self.tabs.addTab(self.general_tab, _("常规设置"))
        self.tabs.addTab(self.breathing_tab, _("呼吸训练"))

        self.setup_general_tab()
        self.setup_breathing_tab()

        self._main_layout.addWidget(self.tabs)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self._main_layout.addWidget(button_box)

        self.setLayout(self._main_layout)

        self._update_estimated_time()

        # 连接信号以实时更新预计时间
        for phase_ui in self.breathing_settings.phase_uis.values():
            phase_ui.checkbox.toggled.connect(self._update_estimated_time)
            phase_ui.spinbox.valueChanged.connect(self._update_estimated_time)
        assert self.breathing_settings.cycles_spinbox is not None
        self.breathing_settings.cycles_spinbox.valueChanged.connect(
            self._update_estimated_time
        )

    def setup_general_tab(self):
        """设置常规选项卡"""
        layout = QVBoxLayout(self.general_tab)
        self.general_settings = GeneralSettings(self.config)
        layout.addWidget(self.general_settings.create_ui(self))

    def setup_breathing_tab(self):
        """设置呼吸选项卡"""
        layout = QVBoxLayout(self.breathing_tab)
        self.breathing_settings = BreathingSettings(self.config)
        layout.addWidget(self.breathing_settings.create_ui(self))

    def _update_estimated_time(self):
        """计算并更新呼吸练习的预计时间标签。"""
        if not hasattr(self.breathing_settings, "estimated_time_label") or not hasattr(
            self.breathing_settings, "phase_uis"
        ):
            return

        try:
            if self.breathing_settings.estimated_time_label is None:
                return

            breathing_values = self.breathing_settings.get_values()
            target_cycles = breathing_values["breathing_cycles"]
            single_cycle_duration = sum(
                breathing_values.get(f"{key}_duration", 0)
                for key in self.breathing_settings.phase_uis
                if breathing_values.get(f"{key}_enabled", False)
            )

            if single_cycle_duration == 0 or target_cycles <= 0:
                self.breathing_settings.estimated_time_label.setText(
                    _("预计时间: --:-- (未启用或周期为0)")
                )
                return

            total_seconds = single_cycle_duration * target_cycles
            mins, secs = divmod(total_seconds, 60)
            self.breathing_settings.estimated_time_label.setText(
                _("预计时间: {mins:02d}:{secs:02d}").format(mins=mins, secs=secs)
            )
        except Exception as e:
            tooltip(f"Error updating estimated time: {e}")
            if self.breathing_settings.estimated_time_label:
                self.breathing_settings.estimated_time_label.setText(
                    _("预计时间: 计算错误")
                )

    @override
    def accept(self):
        """当点击“保存”时，收集UI值，更新全局状态并保存到文件。"""
        try:
            general_values = self.general_settings.get_values()
            breathing_values = self.breathing_settings.get_values()

            config_dict = dataclasses.asdict(self.config)
            config_dict.update(general_values)
            config_dict.update(breathing_values)

            app_config_fields = {field.name for field in dataclasses.fields(AppConfig)}
            filtered_config_dict = {
                k: v for k, v in config_dict.items() if k in app_config_fields
            }

            config_to_save = AppConfig(**filtered_config_dict)

            update_and_save_config(config_to_save)
            set_language(config_to_save.language)
            tooltip(_("配置已保存"))

            pomodoro_manager = get_pomodoro_manager()
            if pomodoro_manager:
                pomodoro_manager.ui_updater.update(pomodoro_manager.timer_manager)

            super().accept()
        except Exception as e:
            tooltip(_("保存配置时出错: {}").format(e))
