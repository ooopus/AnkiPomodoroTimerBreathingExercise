# 移除 mw 导入
import json
import os
from typing import Dict, Any, Optional
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel
from .constants import (
    DEFAULT_POMODORO_MINUTES,
    DEFAULT_REST_MINUTES,
    DEFAULT_SHOW_STATUSBAR_TIMER,
    DEFAULT_SOUND_EFFECT_ENABLED,
    DEFAULT_SOUND_EFFECT_FILE,
    DEFAULT_MEDITATION_SESSIONS,
    DEFAULT_SMART_TIMER_REMINDER,
    DEFAULT_SMART_TIMER_REMINDER_MINUTES,
    STATUSBAR_ICON,
)

# Update CONFIG_PATH to use Anki's addon folder
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


class AddonState:
    def __init__(self):
        self._config = None
        self._pomodoro_timer = None
        self._timer_label = None
        # Initialize config immediately
        self._config = self._load_config()

    def _load_config_from_file(self) -> Dict[str, Any]:
        """从JSON文件加载配置"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config file: {e}")
        return {}

    def _save_config_to_file(self) -> None:
        """保存配置到JSON文件"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config file: {e}")

    @property
    def config(self) -> Dict[str, Any]:
        if self._config is None:
            self._config = self._load_config()
        return self._config

    @property
    def pomodoro_timer(self) -> Optional[QTimer]:
        return self._pomodoro_timer

    @pomodoro_timer.setter
    def pomodoro_timer(self, value: QTimer):
        self._pomodoro_timer = value

    @property
    def timer_label(self) -> Optional[QLabel]:
        return self._timer_label

    @timer_label.setter
    def timer_label(self, value: QLabel):
        self._timer_label = value

    def _load_config(self) -> Dict[str, Any]:
        """加载配置并设置默认值"""
        config = self._load_config_from_file()

        # 设置默认值
        if "pomodoro_minutes" not in config:
            config["pomodoro_minutes"] = DEFAULT_POMODORO_MINUTES
        if "rest_minutes" not in config:
            config["rest_minutes"] = DEFAULT_REST_MINUTES
        if "enabled" not in config:
            config["enabled"] = True
        if "show_statusbar_timer" not in config:
            config["show_statusbar_timer"] = DEFAULT_SHOW_STATUSBAR_TIMER
        # 添加倒计时相关配置项默认值
        if "countdown_target_date" not in config:
            config["countdown_target_date"] = ""
        if "countdown_target_name" not in config:
            config["countdown_target_name"] = ""
        if "consecutive_focus_days" not in config:
            config["consecutive_focus_days"] = 0
        if "last_focus_date" not in config:
            config["last_focus_date"] = ""
        # 添加自动播放音乐配置项
        if "auto_play_music" not in config:
            config["auto_play_music"] = False
        # 添加音效配置项
        if "sound_effect_enabled" not in config:
            config["sound_effect_enabled"] = DEFAULT_SOUND_EFFECT_ENABLED
        if "sound_effect_file" not in config:
            config["sound_effect_file"] = DEFAULT_SOUND_EFFECT_FILE
        # 添加状态栏图标配置项
        if "statusbar_icon" not in config:
            config["statusbar_icon"] = STATUSBAR_ICON
        # 添加冥想训练列表配置项
        if "meditation_sessions" not in config:
            config["meditation_sessions"] = DEFAULT_MEDITATION_SESSIONS
        # 添加智能提醒开始番茄计时配置项
        if "smart_timer_reminder" not in config:
            config["smart_timer_reminder"] = DEFAULT_SMART_TIMER_REMINDER
        if "smart_timer_reminder_minutes" not in config:
            config["smart_timer_reminder_minutes"] = DEFAULT_SMART_TIMER_REMINDER_MINUTES

        # Ensure correct types
        try:
            config["pomodoro_minutes"] = int(
                config.get("pomodoro_minutes", DEFAULT_POMODORO_MINUTES)
            )
            config["rest_minutes"] = int(
                config.get("rest_minutes", DEFAULT_REST_MINUTES)
            )
            config["enabled"] = bool(config.get("enabled", True))
            config["show_statusbar_timer"] = bool(
                config.get("show_statusbar_timer", DEFAULT_SHOW_STATUSBAR_TIMER)
            )
            config["consecutive_focus_days"] = int(
                config.get("consecutive_focus_days", 0)
            )
            config["auto_play_music"] = bool(
                config.get("auto_play_music", False)
            )
            config["sound_effect_enabled"] = bool(
                config.get("sound_effect_enabled", DEFAULT_SOUND_EFFECT_ENABLED)
            )
            config["smart_timer_reminder"] = bool(
                config.get("smart_timer_reminder", DEFAULT_SMART_TIMER_REMINDER)
            )
            config["smart_timer_reminder_minutes"] = int(
                config.get("smart_timer_reminder_minutes", DEFAULT_SMART_TIMER_REMINDER_MINUTES)
            )
        except (ValueError, TypeError) as e:
            print(
                f"Pomodoro Addon: Error loading config, resetting to defaults. Error: {e}"
            )
            # Reset to defaults on error
            config = {
                "pomodoro_minutes": DEFAULT_POMODORO_MINUTES,
                "rest_minutes": DEFAULT_REST_MINUTES,
                "enabled": True,
                "show_statusbar_timer": DEFAULT_SHOW_STATUSBAR_TIMER,
                "countdown_target_date": "",
                "countdown_target_name": "",
                "consecutive_focus_days": 0,
                "last_focus_date": "",
                "auto_play_music": False,
                "sound_effect_enabled": DEFAULT_SOUND_EFFECT_ENABLED,
                "sound_effect_file": DEFAULT_SOUND_EFFECT_FILE,
                "statusbar_icon": STATUSBAR_ICON,
                "meditation_sessions": DEFAULT_MEDITATION_SESSIONS,
                "smart_timer_reminder": DEFAULT_SMART_TIMER_REMINDER,
                "smart_timer_reminder_minutes": DEFAULT_SMART_TIMER_REMINDER_MINUTES,
            }
            self._config = config
            self._save_config_to_file()  # 直接使用类方法保存

        # 保存配置到文件
        self._config = config
        self._save_config_to_file()
        return config


def load_config() -> Dict[str, Any]:
    """现在只是get_state()的包装"""
    return get_state().config


def save_config() -> None:
    """保存当前配置到文件"""
    state = get_state()
    if state._config is not None:
        state._save_config_to_file()


_state_instance = None


def get_state() -> AddonState:
    global _state_instance
    if _state_instance is None:
        _state_instance = AddonState()
    return _state_instance


def get_config() -> Dict[str, Any]:
    return get_state().config


def get_pomodoro_timer() -> Optional[QTimer]:
    return get_state().pomodoro_timer


def get_timer_label() -> Optional[QLabel]:
    return get_state().timer_label


def set_pomodoro_timer(timer: QTimer) -> None:
    get_state().pomodoro_timer = timer


def set_timer_label(label: QLabel) -> None:
    get_state().timer_label = label


def get_active_timer_values() -> tuple:
    """获取当前激活的番茄钟和休息时长配置
    
    Returns:
        tuple: (pomodoro_minutes, rest_minutes)
    """
    config = get_config()
    active_group = config.get("active_timer_group", 0)
    
    if active_group == 0:
        return (
            config.get("pomodoro_minutes", DEFAULT_POMODORO_MINUTES),
            config.get("rest_minutes", DEFAULT_REST_MINUTES)
        )
    elif active_group == 1:
        return (
            config.get("pomodoro_minutes_2", 25),
            config.get("rest_minutes_2", 5)
        )
    elif active_group == 2:
        return (
            config.get("pomodoro_minutes_3", 50),
            config.get("rest_minutes_3", 10)
        )
    else:
        # Default to first group
        return (
            config.get("pomodoro_minutes", DEFAULT_POMODORO_MINUTES),
            config.get("rest_minutes", DEFAULT_REST_MINUTES)
        )
