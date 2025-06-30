from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aqt import QLabel
from aqt.utils import tooltip

from .config import AppConfig, load_user_config, save_config

# 仅为类型检查导入 PomodoroManager，以避免循环导入
if TYPE_CHECKING:
    from .pomodoro.pomodoro_manager import PomodoroManager


class AppState:
    """管理应用程序所有运行时状态的单例类。"""

    def __init__(self):
        self._config: AppConfig | None = None
        self._pomodoro_manager: PomodoroManager | None = None
        self._timer_label: QLabel | None = None
        self._pending_break_type: bool = False
        # 应用程序启动时立即加载配置
        self._config = self._load_config()

    # --- 配置管理 ---

    @property
    def config(self) -> AppConfig:
        """获取当前内存中的配置对象。"""
        if self._config is None:
            # 这是一个备用逻辑，正常情况下在 __init__ 中已加载
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> AppConfig:
        """内部方法，从文件加载用户配置。"""
        return load_user_config()

    def reload_config(self) -> AppConfig:
        """
        强制从文件重新加载配置。
        这能确保获取到最新的、已保存的设置。
        """
        self._config = self._load_config()
        return self.config

    def save_config(self) -> None:
        """将当前内存中的配置保存到 JSON 文件。"""
        if self._config is None:
            tooltip("无法保存配置：没有加载任何配置。", period=3000)
            return
        save_config(self._config)

    def update_and_save_config(self, new_config: AppConfig) -> None:
        """
        用新的配置对象更新内存状态，并将其保存到文件。
        这是更新整个配置的首选方法。
        """
        self._config = new_config
        self.save_config()

    def update_config_value(self, key: str, value: Any) -> None:
        """更新单个配置值并立即保存。"""
        if self._config is not None:
            if hasattr(self._config, key):
                setattr(self._config, key, value)
                self.save_config()
            else:
                tooltip(f"无法更新配置：未找到键 '{key}'。", period=3000)
        else:
            tooltip("无法更新配置：没有加载任何配置。", period=3000)

    # --- 计时器和标签状态 ---

    @property
    def pomodoro_manager(self) -> PomodoroManager | None:
        """获取番茄钟管理器实例。"""
        return self._pomodoro_manager

    @pomodoro_manager.setter
    def pomodoro_manager(self, value: PomodoroManager | None):
        """设置番茄钟管理器实例。"""
        self._pomodoro_manager = value

    @property
    def timer_label(self) -> QLabel | None:
        """获取状态栏标签实例。"""
        return self._timer_label

    @timer_label.setter
    def timer_label(self, value: QLabel | None):
        """设置状态栏标签实例。"""
        self._timer_label = value

    @property
    def pending_break_type(self) -> bool:
        """获取待处理的休息类型 (True: 长休息, False: 无)。"""
        return self._pending_break_type

    @pending_break_type.setter
    def pending_break_type(self, value: bool):
        """设置待处理的休息类型。"""
        self._pending_break_type = value


# --- 单例访问器 ---

_app_state_instance: AppState | None = None


def get_app_state() -> AppState:
    """获取 AppState 的单例实例。"""
    global _app_state_instance
    if _app_state_instance is None:
        _app_state_instance = AppState()
    return _app_state_instance


# --- 便捷访问器函数 ---


def get_config() -> AppConfig:
    """获取当前内存中的配置对象。"""
    return get_app_state().config


def reload_config() -> AppConfig:
    """强制从文件重新加载配置并返回。"""
    return get_app_state().reload_config()


def update_and_save_config(new_config: AppConfig) -> None:
    """更新内存中的配置并保存到文件。"""
    get_app_state().update_and_save_config(new_config)


def update_config_value(key: str, value: Any) -> None:
    """更新单个配置值并保存。"""
    get_app_state().update_config_value(key, value)


def get_pomodoro_manager() -> PomodoroManager | None:
    """获取番茄钟管理器实例。"""
    return get_app_state().pomodoro_manager


def set_pomodoro_manager(manager: PomodoroManager | None) -> None:
    """设置番茄钟管理器实例。"""
    get_app_state().pomodoro_manager = manager


def get_timer_label() -> QLabel | None:
    """获取计时器标签实例。"""
    return get_app_state().timer_label


def set_timer_label(label: QLabel | None) -> None:
    """设置计时器标签实例。"""
    get_app_state().timer_label = label
