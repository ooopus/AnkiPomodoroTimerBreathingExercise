from typing import Optional, cast

from ...constants import CircularTimerStyle, Defaults
from .timer_base import TimerClass
from .timer_style_default import CircularTimer as DefaultTimer
from .timer_style_rainbow import CircularTimer as RainbowTimer

# 类型安全的样式映射
TIMER_STYLES: dict[CircularTimerStyle, TimerClass] = {
    CircularTimerStyle.DEFAULT: cast(TimerClass, DefaultTimer),
    CircularTimerStyle.RAINBOW: cast(TimerClass, RainbowTimer),
}


def get_timer_class(style_name: Optional[CircularTimerStyle] = None) -> TimerClass:
    """
    根据样式名称获取对应的计时器类。

    Args:
        style_name: 计时器样式，如果为None则使用默认样式

    Returns:
        计时器类，保证是BaseCircularTimer的子类
    """
    if style_name is None:
        style_name = Defaults.CIRCULAR_TIMER_STYLE

    if style_name not in TIMER_STYLES:
        print(
            f"警告: 未知的计时器样式 '{style_name}'，"
            f"使用默认样式 '{Defaults.CIRCULAR_TIMER_STYLE}'"
        )
        style_name = Defaults.CIRCULAR_TIMER_STYLE

    return TIMER_STYLES[style_name]


def register_timer_style(
    style_name: CircularTimerStyle, timer_class: TimerClass
) -> None:
    """
    注册新的计时器样式。

    Args:
        style_name: 样式名称
        timer_class: 计时器类，必须是BaseCircularTimer的子类
    """
    # 编译时类型检查已经保证了类型安全
    if style_name in TIMER_STYLES:
        print(f"警告: 计时器样式 '{style_name}' 已存在，将被覆盖")

    TIMER_STYLES[style_name] = timer_class


def list_timer_styles() -> list[CircularTimerStyle]:
    """列出所有可用的计时器样式"""
    return list(TIMER_STYLES.keys())
