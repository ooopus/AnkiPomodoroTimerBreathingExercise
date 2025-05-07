from typing import Any, Optional

from aqt import QLabel, QTimer
from aqt.utils import tooltip

from .config.config import get_default_config, load_config_from_file, save_config
from .constants import PHASES


class AppState:
    def __init__(self):
        self._config: Optional[dict[str, Any]] = None
        self._pomodoro_timer: Optional[QTimer] = None
        self._timer_label: Optional[QLabel] = None
        # Initialize config immediately
        self._config = self._load_config()

    # --- Configuration Management ---

    @property
    def config(self) -> dict[str, Any]:
        """Gets the current configuration, loading if necessary."""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> dict[str, Any]:
        """加载配置并设置缺失或无效值的默认值"""
        config = load_config_from_file()
        default_config = get_default_config()

        # 设置缺失键的默认值
        for key, default_value in default_config.items():
            if key not in config:
                config[key] = default_value

        # Ensure correct types, reset to defaults on error
        try:
            config["pomodoro_minutes"] = int(config["pomodoro_minutes"])
            config["breathing_cycles"] = int(config["breathing_cycles"])
            config["enabled"] = bool(config["enabled"])
            config["statusbar_format"] = str(config["statusbar_format"])
            config["show_circular_timer"] = bool(config["show_circular_timer"])
            config["circular_timer_style"] = str(config["circular_timer_style"])
            config["completed_pomodoros"] = int(config["completed_pomodoros"])
            config["pomodoros_before_long_break"] = int(
                config["pomodoros_before_long_break"]
            )
            config["long_break_minutes"] = int(config["long_break_minutes"])
            config["max_break_duration"] = int(config["max_break_duration"])
            config["daily_pomodoro_seconds"] = int(config["daily_pomodoro_seconds"])
            config["last_pomodoro_time"] = float(config.get("last_pomodoro_time", 0))
            config["last_date"] = str(config.get("last_date", ""))
            config["work_across_decks"] = bool(config.get("work_across_decks", False))

            # Ensure breathing phase keys exist and have correct types
            for phase in PHASES:
                duration_key = f"{phase['key']}_duration"
                enabled_key = f"{phase['key']}_enabled"
                audio_key = (
                    f"{phase['key']}_audio"  # Assuming audio key follows this pattern
                )

                # Validate and cast types
                try:
                    config[duration_key] = int(config[duration_key])
                except (ValueError, TypeError):
                    config[duration_key] = phase["default_duration"]  # Reset on error

                try:
                    config[enabled_key] = bool(config[enabled_key])
                except (ValueError, TypeError):
                    config[enabled_key] = phase["default_enabled"]  # Reset on error

                try:  # Validate audio path as string
                    config[audio_key] = str(config[audio_key])
                except (ValueError, TypeError):
                    config[audio_key] = phase.get("default_audio", "")  # Reset on error

        except (ValueError, TypeError) as e:
            tooltip(
                f"Pomodoro Addon: Error validating config, resetting to defaults. "
                f"Error: {e}",
                period=3000,
            )
            # 重置为默认值
            config = default_config
            self._config = config
            self.save_config()  # Save the reset defaults

        return config

    def save_config(self) -> None:
        """保存当前配置状态到JSON文件"""
        if self._config is None:
            tooltip("Cannot save config: No configuration loaded.", period=3000)
            return

        save_config(self._config)

    def update_config_value(self, key: str, value: Any) -> None:
        """Updates a specific configuration value and saves the config."""
        if self._config is not None:
            self._config[key] = value
            self.save_config()
        else:
            tooltip("Cannot update config: No configuration loaded.", period=3000)

    # --- Timer and Label State ---

    @property
    def pomodoro_timer(self) -> Optional[QTimer]:
        return self._pomodoro_timer

    @pomodoro_timer.setter
    def pomodoro_timer(self, value: Optional[QTimer]):
        self._pomodoro_timer = value

    @property
    def timer_label(self) -> Optional[QLabel]:
        return self._timer_label

    @timer_label.setter
    def timer_label(self, value: Optional[QLabel]):
        self._timer_label = value


# --- Singleton Accessor ---

_app_state_instance: Optional[AppState] = None


def get_app_state() -> AppState:
    """Gets the singleton instance of the AppState."""
    global _app_state_instance
    if _app_state_instance is None:
        _app_state_instance = AppState()
    return _app_state_instance


# --- Convenience Accessors ---


def get_config() -> dict[str, Any]:
    """Convenience function to get the configuration dictionary."""
    return get_app_state().config


def update_config_value(key: str, value: Any) -> None:
    """Convenience function to update a specific config value."""
    get_app_state().update_config_value(key, value)


def get_pomodoro_timer() -> Optional[QTimer]:
    """Convenience function to get the Pomodoro timer instance."""
    return get_app_state().pomodoro_timer


def set_pomodoro_timer(timer: Optional[QTimer]) -> None:
    """Convenience function to set the Pomodoro timer instance."""
    get_app_state().pomodoro_timer = timer


def get_timer_label() -> Optional[QLabel]:
    """Convenience function to get the timer label instance."""
    return get_app_state().timer_label


def set_timer_label(label: Optional[QLabel]) -> None:
    """Convenience function to set the timer label instance."""
    get_app_state().timer_label = label
