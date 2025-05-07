"""
圆形计时器模块

这个包包含了不同样式的圆形计时器实现，使用工厂模式来选择合适的样式。
可用的样式包括：
- default: 默认样式
- rainbow: 彩虹样式，使用动态变化的彩虹色文本

使用方法：
1. 通过配置文件设置 timer_style 参数选择样式
2. 调用 ui.circular_timer.setup_circular_timer() 创建计时器
"""

from .timer_common import setup_circular_timer
from .timer_factory import get_timer_class as get_timer_class
from .timer_factory import register_timer_style as register_timer_style

__all__ = ["get_timer_class", "register_timer_style", "setup_circular_timer"]
