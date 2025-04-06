import json
import os
from typing import Any, Dict, Optional

from aqt import QLabel, QTimer
from aqt.utils import tooltip

from .constants import (
    DEFAULT_BREATHING_CYCLES,
    DEFAULT_LONG_BREAK_MINUTES,
    DEFAULT_MAX_BREAK_DURATION,
    DEFAULT_POMODORO_MINUTES,
    DEFAULT_POMODOROS_BEFORE_LONG_BREAK,
    DEFAULT_SHOW_CIRCULAR_TIMER,
    DEFAULT_STATUSBAR_FORMAT,
    PHASES,
)

# Configuration file path within the addon folder
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


class AppState:
    def __init__(self):
        self._config: Optional[Dict[str, Any]] = None
        self._pomodoro_timer: Optional[QTimer] = None
        self._timer_label: Optional[QLabel] = None
        # Initialize config immediately
        self._config = self._load_config()

    # --- Configuration Management ---

    @property
    def config(self) -> Dict[str, Any]:
        """Gets the current configuration, loading if necessary."""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config_from_file(self) -> Dict[str, Any]:
        """Loads configuration from the JSON file."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    if not isinstance(config_data, dict):
                        raise ValueError("Invalid config format")
                    return config_data
        except json.JSONDecodeError as e:
            tooltip(f"Configuration file format error: {e}", period=3000)
        except Exception as e:
            tooltip(f"Error loading configuration file: {e}", period=3000)
        return {}

    def _load_config(self) -> Dict[str, Any]:
        """Loads configuration and sets default values if missing or invalid."""
        config = self._load_config_from_file()

        # Set defaults for missing keys
        defaults = {
            "pomodoro_minutes": DEFAULT_POMODORO_MINUTES,
            "breathing_cycles": DEFAULT_BREATHING_CYCLES,
            "enabled": True,
            "show_circular_timer": DEFAULT_SHOW_CIRCULAR_TIMER,
            "completed_pomodoros": 0,
            "daily_pomodoro_seconds": 0,
            "pomodoros_before_long_break": DEFAULT_POMODOROS_BEFORE_LONG_BREAK,
            "long_break_minutes": DEFAULT_LONG_BREAK_MINUTES,
            "max_break_duration": DEFAULT_MAX_BREAK_DURATION
            * 60,  # Convert minutes to seconds
            "statusbar_format": DEFAULT_STATUSBAR_FORMAT,
            "last_pomodoro_time": 0,
            "last_date": "",
        }
        for key, default_value in defaults.items():
            if key not in config:
                config[key] = default_value

        # Set defaults for breathing phases
        for phase in PHASES:
            key_duration = f"{phase['key']}_duration"
            key_enabled = f"{phase['key']}_enabled"
            if key_duration not in config:
                config[key_duration] = phase["default_duration"]
            if key_enabled not in config:
                config[key_enabled] = phase["default_enabled"]

        # Ensure correct types, reset to defaults on error
        try:
            config["pomodoro_minutes"] = int(config["pomodoro_minutes"])
            config["breathing_cycles"] = int(config["breathing_cycles"])
            config["enabled"] = bool(config["enabled"])
            config["statusbar_format"] = str(config["statusbar_format"])
            config["show_circular_timer"] = bool(config["show_circular_timer"])
            config["completed_pomodoros"] = int(config["completed_pomodoros"])
            config["pomodoros_before_long_break"] = int(
                config["pomodoros_before_long_break"]
            )
            config["long_break_minutes"] = int(config["long_break_minutes"])
            config["max_break_duration"] = int(config["max_break_duration"])
            config["daily_pomodoro_seconds"] = int(config["daily_pomodoro_seconds"])
            config["last_pomodoro_time"] = float(config.get("last_pomodoro_time", 0))
            config["last_date"] = str(config.get("last_date", ""))

            for phase in PHASES:
                config[f"{phase['key']}_duration"] = int(
                    config[f"{phase['key']}_duration"]
                )
                config[f"{phase['key']}_enabled"] = bool(
                    config[f"{phase['key']}_enabled"]
                )

        except (ValueError, TypeError) as e:
            tooltip(
                f"Pomodoro Addon: Error validating config, resetting to defaults. Error: {e}",
                period=3000,
            )
            # Reset to defaults
            config = {
                "pomodoro_minutes": DEFAULT_POMODORO_MINUTES,
                "breathing_cycles": DEFAULT_BREATHING_CYCLES,
                "enabled": True,
                "statusbar_format": DEFAULT_STATUSBAR_FORMAT,
                "show_circular_timer": DEFAULT_SHOW_CIRCULAR_TIMER,
                "completed_pomodoros": 0,
                "daily_pomodoro_seconds": 0,
                "pomodoros_before_long_break": DEFAULT_POMODOROS_BEFORE_LONG_BREAK,
                "long_break_minutes": DEFAULT_LONG_BREAK_MINUTES,
                "max_break_duration": DEFAULT_MAX_BREAK_DURATION * 60,
                "last_pomodoro_time": 0,
                "last_date": "",
            }
            for phase in PHASES:
                config[f"{phase['key']}_duration"] = phase["default_duration"]
                config[f"{phase['key']}_enabled"] = phase["default_enabled"]
            self._config = config
            self.save_config()  # Save the reset defaults

        return config

    def save_config(self) -> None:
        """Saves the current configuration state to the JSON file atomically."""
        if self._config is None:
            tooltip("Cannot save config: No configuration loaded.", period=3000)
            return

        try:
            if not isinstance(self._config, dict):
                raise ValueError("Configuration data must be a dictionary")

            config_dir = os.path.dirname(CONFIG_PATH)
            os.makedirs(config_dir, exist_ok=True)

            # Use a unique temporary filename
            temp_path = f"{CONFIG_PATH}.{os.getpid()}.tmp"

            # Write to temporary file first
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # Ensure write to disk

            # Atomic replace
            os.replace(temp_path, CONFIG_PATH)

        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as remove_e:
                    tooltip(
                        f"Error cleaning up temporary file: {remove_e}", period=3000
                    )
            tooltip(f"Error saving configuration: {e}", period=3000)

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


def get_config() -> Dict[str, Any]:
    """Convenience function to get the configuration dictionary."""
    return get_app_state().config


def save_config() -> None:
    """Convenience function to save the current configuration."""
    get_app_state().save_config()


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
    get_app_state().timer_label
