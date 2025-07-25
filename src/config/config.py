import sys
from pathlib import Path

# Add the 'vendor' directory to Python's path
vendor_dir = Path(__file__).resolve().parent.parent / "vendor"
if str(vendor_dir) not in sys.path:
    sys.path.insert(0, str(vendor_dir))
# 由于anki使用自带的python，必须先导入外部依赖


import dataclasses
import json
from enum import Enum
from typing import Any

from koda_validate import Valid

from . import anki_config
from .enums import CircularTimerStyle, StatusBarFormat, TimerPosition
from .types import AppConfig, config_validator


class EnhancedJSONEncoder(json.JSONEncoder):
    """一个增强的JSON编码器,可以处理枚举类型。"""

    def default(self, o: Any):
        if isinstance(o, Enum):
            return o.value
        return super().default(o)


def get_default_config() -> AppConfig:
    """方便地获取一个包含所有默认值的 AppConfig 实例。"""
    return AppConfig()


def save_config(config: AppConfig):
    """
    将一个 AppConfig 实例保存到 Anki 的配置中。
    """
    config_dict = dataclasses.asdict(config)
    anki_config.write_anki_config(config_dict)


def _migrate_config_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    迁移旧的配置数据格式到新的枚举类型。
    """
    # 迁移 circular_timer_style
    if "circular_timer_style" in data and isinstance(data["circular_timer_style"], str):
        try:
            data["circular_timer_style"] = CircularTimerStyle(
                data["circular_timer_style"]
            )
        except ValueError:
            data["circular_timer_style"] = CircularTimerStyle.DEFAULT

    # 迁移 statusbar_format
    if "statusbar_format" in data and isinstance(data["statusbar_format"], str):
        try:
            data["statusbar_format"] = StatusBarFormat(data["statusbar_format"])
        except ValueError:
            data[
                "statusbar_format"
            ] = StatusBarFormat.ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME

    # 迁移 timer_position
    if "timer_position" in data and isinstance(data["timer_position"], str):
        try:
            data["timer_position"] = TimerPosition(data["timer_position"])
        except ValueError:
            data["timer_position"] = TimerPosition.TOP_RIGHT

    # 迁移 language
    if "language" in data and isinstance(data["language"], str):
        from .languages import LanguageCode

        try:
            data["language"] = LanguageCode(data["language"])
        except ValueError:
            data["language"] = LanguageCode.AUTO

    return data


def load_user_config() -> AppConfig:
    """
    从 Anki 的配置中加载、验证并返回用户配置。
    - 如果配置不存在，则创建一个包含默认值的配置。
    - 如果配置损坏或无效，则返回默认配置。
    - 如果配置缺少字段，则使用默认值填充。

    Returns:
        一个经过验证和完全填充的 AppConfig 实例。
    """
    # 首先，尝试从旧的 config.json 迁移
    anki_config.migrate_from_json_if_needed()

    loaded_data = anki_config.get_anki_config()

    if loaded_data is None:
        # No configuration found, create a new default one
        default_config = get_default_config()
        save_config(default_config)
        return default_config

    try:
        # 在验证之前进行数据迁移
        migrated_data = _migrate_config_data(loaded_data)

        # 使用从 types.py 导入的验证器进行验证和填充
        result = config_validator(migrated_data)

        if isinstance(result, Valid):
            config = result.val
            # 将可能已更新的配置回写
            save_config(config)
            return config
        else:
            # Validation failed, return default config
            return get_default_config()

    except (ValueError, TypeError) as e:
        # Some other error occurred, return default config
        print(f"Error loading config: {e}")
        return get_default_config()
