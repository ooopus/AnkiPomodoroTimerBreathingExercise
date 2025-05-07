import json
import os
from typing import Any

from aqt.utils import tooltip

from .type import ConfigDict

# 配置文件路径
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"
)


def load_config_from_file() -> dict[str, Any]:
    """从JSON文件加载配置"""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, encoding="utf-8") as f:
                config_data = json.load(f)
                if not isinstance(config_data, dict):
                    raise ValueError("Invalid config format")
                return config_data
    except json.JSONDecodeError as e:
        tooltip(f"Configuration file format error: {e}", period=3000)
    except Exception as e:
        tooltip(f"Error loading configuration file: {e}", period=3000)
    return {}


def save_config(config: dict[str, Any], force: bool = False) -> None:
    """将配置保存到JSON文件

    Args:
        config: 要保存的配置字典
        force: 如果为True，则在出错时强制覆盖配置文件
    """
    if not config and not force:
        tooltip("Cannot save config: No configuration loaded.", period=3000)
        return

    try:
        if not isinstance(config, dict) and not force:
            raise ValueError("Configuration data must be a dictionary")

        config_dir = os.path.dirname(CONFIG_PATH)
        os.makedirs(config_dir, exist_ok=True)

        # 直接写入配置文件
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            f.flush()

    except Exception as e:
        if force:
            # 强制模式下，尝试再次保存
            try:
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
            except Exception as force_e:
                tooltip(f"强制保存配置也失败: {force_e}", period=3000)
        tooltip(f"保存配置时出错: {e}", period=3000)


def get_default_config() -> ConfigDict:
    """获取默认配置"""
    # 从config.example.json加载默认配置
    example_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "config.example.json"
    )
    try:
        if os.path.exists(example_path):
            with open(example_path, encoding="utf-8") as f:
                default_config = json.load(f)
                return default_config
    except Exception as e:
        tooltip(f"Error loading default configuration: {e}", period=3000)

    # 如果无法加载示例配置，返回空字典
    return {}
