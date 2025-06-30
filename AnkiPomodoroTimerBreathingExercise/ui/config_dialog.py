import dataclasses

from aqt import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    mw,
)
from aqt.utils import tooltip

from ..config import AppConfig
from ..constants import StatusBarFormat
from ..state import get_pomodoro_manager, reload_config, update_and_save_config
from ..translator import _
from .config_components import BreathingSettings, GeneralSettings


class ConfigDialog(QDialog):
    """用于番茄钟和呼吸设置的配置对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent or mw)

        # 每次打开对话框时，都从文件强制重新加载配置
        # 这确保了UI显示的是最新的设置
        self.config = reload_config()

        self.setWindowTitle(_("番茄钟/呼吸训练设置"))
        self._main_layout = QVBoxLayout(self)

        # 初始化UI组件，并传入最新的配置对象
        self.general_settings = GeneralSettings(self.config)
        self.breathing_settings = BreathingSettings(self.config)

        # 创建并添加UI组件
        self._main_layout.addWidget(self.general_settings.create_ui(self))

        self.statusbar_format_group = QGroupBox(_("状态栏显示设置"))
        self.statusbar_format_layout = QVBoxLayout()

        self.statusbar_format_combo = QComboBox()
        for format_option in StatusBarFormat:
            self.statusbar_format_combo.addItem(
                format_option.display_name, format_option
            )

        current_format = self.config.statusbar_format
        index = self.statusbar_format_combo.findData(current_format)
        if index >= 0:
            self.statusbar_format_combo.setCurrentIndex(index)

        self.statusbar_format_layout.addWidget(QLabel(_("选择状态栏显示格式：")))
        self.statusbar_format_layout.addWidget(self.statusbar_format_combo)
        self.statusbar_format_group.setLayout(self.statusbar_format_layout)
        self._main_layout.addWidget(self.statusbar_format_group)

        self._main_layout.addWidget(self.breathing_settings.create_ui(self))

        # 对话框按钮 (保存/取消)
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

    def _update_estimated_time(self):
        """计算并更新呼吸练习的预计时间标签。"""
        # 在UI组件（如estimated_time_label）完全初始化之前，不要执行此函数。
        # hasattr 检查确保在尝试访问属性之前，属性已经存在。
        if not hasattr(self.breathing_settings, "estimated_time_label") or not hasattr(
            self.breathing_settings, "phase_uis"
        ):
            return

        try:
            # 确保 estimated_time_label 不是 None
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

    def accept(self):
        """当点击“保存”时，收集UI值，更新全局状态并保存到文件。"""
        try:
            # 1. 从UI组件获取更新后的值
            general_values = self.general_settings.get_values()
            breathing_values = self.breathing_settings.get_values()

            # 2. 合并所有设置到一个字典中
            config_dict = dataclasses.asdict(self.config)
            config_dict.update(general_values)
            config_dict.update(breathing_values)
            config_dict["statusbar_format"] = self.statusbar_format_combo.currentData()

            # 3. 过滤掉字典中不属于 AppConfig 的键 (安全措施)
            app_config_fields = {field.name for field in dataclasses.fields(AppConfig)}
            filtered_config_dict = {
                k: v for k, v in config_dict.items() if k in app_config_fields
            }

            # 4. 从更新后的字典创建一个新的 AppConfig 实例
            config_to_save = AppConfig(**filtered_config_dict)

            # 5. 使用新的状态管理函数来更新内存并保存到文件
            update_and_save_config(config_to_save)
            tooltip(_("配置已保存"))

            # 6. 立即更新UI显示（如状态栏）
            pomodoro_manager = get_pomodoro_manager()
            if pomodoro_manager:
                # Trigger UI update through the manager's UI updater
                pomodoro_manager.ui_updater.update(pomodoro_manager.timer_manager)

            super().accept()
        except Exception as e:
            tooltip(_("保存配置时出错: {}").format(e))
