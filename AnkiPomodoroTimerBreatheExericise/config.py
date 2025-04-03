import json
import os
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QLabel
from .constants import (
    PHASES,
    DEFAULT_POMODORO_MINUTES,
    DEFAULT_BREATHING_CYCLES,
    DEFAULT_SHOW_CIRCULAR_TIMER,
    DEFAULT_POMODOROS_BEFORE_LONG_BREAK,
    DEFAULT_LONG_BREAK_MINUTES,
    DEFAULT_MAX_BREAK_DURATION,
    DEFAULT_STATUSBAR_FORMAT,
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
                    config = json.load(f)
                    # 验证配置完整性
                    if not isinstance(config, dict):
                        raise ValueError("Invalid config format")
                    return config
        except json.JSONDecodeError as e:
            print(f"配置文件格式错误: {e}")
            # 记录错误到Anki日志系统
        except Exception as e:
            print(f"加载配置文件时出错: {e}")
        return {}

    def _save_config_to_file(self) -> None:
        """保存配置到JSON文件"""
        try:
            # 验证配置数据
            if not isinstance(self._config, dict):
                raise ValueError("配置数据必须是字典类型")
                
            # 确保目录存在
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            
            # 创建临时文件
            temp_path = CONFIG_PATH + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
                
            # 原子性替换
            if os.path.exists(temp_path):
                os.replace(temp_path, CONFIG_PATH)
                
        except ValueError as e:  # JSON encoding error
            print(f"配置序列化失败: {e}")
        except OSError as e:
            print(f"保存配置文件时出错: {e}")
        except Exception as e:
            print(f"保存配置时发生意外错误: {e}")

    @property
    def config(self) -> Dict[str, Any]:
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> Dict[str, Any]:
        """加载配置并设置默认值"""
        config = self._load_config_from_file()

        if "pomodoro_minutes" not in config:
            config["pomodoro_minutes"] = DEFAULT_POMODORO_MINUTES
        if "breathing_cycles" not in config:
            config["breathing_cycles"] = DEFAULT_BREATHING_CYCLES
        if "enabled" not in config:
            config["enabled"] = True
        if "show_circular_timer" not in config:
            config["show_circular_timer"] = DEFAULT_SHOW_CIRCULAR_TIMER
        if "completed_pomodoros" not in config:
            config["completed_pomodoros"] = 0
        if "daily_pomodoro_seconds" not in config:
            config["daily_pomodoro_seconds"] = 0
        if "pomodoros_before_long_break" not in config:
            config["pomodoros_before_long_break"] = DEFAULT_POMODOROS_BEFORE_LONG_BREAK
        if "long_break_minutes" not in config:
            config["long_break_minutes"] = DEFAULT_LONG_BREAK_MINUTES
        if "max_break_duration" not in config:
            config["max_break_duration"] = DEFAULT_MAX_BREAK_DURATION * 60  # 转换为秒
        if "statusbar_format" not in config:
            config["statusbar_format"] = DEFAULT_STATUSBAR_FORMAT

        # 对每个呼吸阶段做同样处理
        for phase in PHASES:
            key_duration = f"{phase['key']}_duration"
            key_enabled = f"{phase['key']}_enabled"
            if key_duration not in config:
                config[key_duration] = phase["default_duration"]
            if key_enabled not in config:
                config[key_enabled] = phase["default_enabled"]

        # Ensure correct types
        try:
            config["pomodoro_minutes"] = int(
                config.get("pomodoro_minutes", DEFAULT_POMODORO_MINUTES)
            )
            config["breathing_cycles"] = int(
                config.get("breathing_cycles", DEFAULT_BREATHING_CYCLES)
            )
            config["enabled"] = bool(config.get("enabled", True))
            config["statusbar_format"] = str(
                config.get("statusbar_format", DEFAULT_STATUSBAR_FORMAT)
            )
            config["show_circular_timer"] = bool(
                config.get("show_circular_timer", DEFAULT_SHOW_CIRCULAR_TIMER)
            )
            config["completed_pomodoros"] = int(config.get("completed_pomodoros", 0))
            config["pomodoros_before_long_break"] = int(
                config.get(
                    "pomodoros_before_long_break", DEFAULT_POMODOROS_BEFORE_LONG_BREAK
                )
            )
            config["long_break_minutes"] = int(
                config.get("long_break_minutes", DEFAULT_LONG_BREAK_MINUTES)
            )
            for phase in PHASES:
                config[f"{phase['key']}_duration"] = int(
                    config.get(f"{phase['key']}_duration", phase["default_duration"])
                )
                config[f"{phase['key']}_enabled"] = bool(
                    config.get(f"{phase['key']}_enabled", phase["default_enabled"])
                )
        except (ValueError, TypeError) as e:
            print(
                f"Pomodoro Addon: Error loading config, resetting to defaults. Error: {e}"
            )
            # Reset to defaults on error
            config = {
                "pomodoro_minutes": DEFAULT_POMODORO_MINUTES,
                "breathing_cycles": DEFAULT_BREATHING_CYCLES,
                "enabled": True,
                "statusbar_format": DEFAULT_STATUSBAR_FORMAT,
                "show_circular_timer": DEFAULT_SHOW_CIRCULAR_TIMER,
                "completed_pomodoros": 0,
                "pomodoros_before_long_break": DEFAULT_POMODOROS_BEFORE_LONG_BREAK,
                "long_break_minutes": DEFAULT_LONG_BREAK_MINUTES,
            }
            for phase in PHASES:
                config[f"{phase['key']}_duration"] = phase["default_duration"]
                config[f"{phase['key']}_enabled"] = phase["default_enabled"]
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


def get_timer_label() -> Optional[QLabel]:
    """返回当前计时器标签实例"""
    return get_state()._timer_label
