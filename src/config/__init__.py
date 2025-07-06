# 配置模块初始化文件

# 从 types.py 导出数据类，以便外部可以直接使用类型注解
# 从 config.py 导出核心功能函数
from . import constants
from .config import get_default_config, load_user_config, save_config
from .types import AppConfig

# 定义包被 import * 时导出的内容
__all__ = [
    "AppConfig",
    "load_user_config",
    "save_config",
    "get_default_config",
    "constants",
]
