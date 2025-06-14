# 导入所有可用的计时器样式
from ...constants import Defaults
from .timer_style_default import CircularTimer as DefaultTimer
from .timer_style_rainbow import CircularTimer as RainbowTimer

# 默认样式
DEFAULT_TIMER_STYLE = Defaults.CIRCULAR_TIMER_STYLE

# 可用样式映射
TIMER_STYLES = {
    "default": DefaultTimer,
    "rainbow": RainbowTimer,
}


def get_timer_class(style_name=None):
    """根据样式名称获取对应的计时器类。

    Args:
        style_name: 计时器样式名称，如果为None则使用默认样式

    Returns:
        计时器类
    """
    if style_name is None:
        style_name = DEFAULT_TIMER_STYLE

    # 确保样式名称有效，如果无效则使用默认样式
    if style_name not in TIMER_STYLES:
        print(
            f"警告: 未知的计时器样式 '{style_name}'，"
            f"使用默认样式 '{DEFAULT_TIMER_STYLE}'"
        )
        style_name = DEFAULT_TIMER_STYLE

    return TIMER_STYLES[style_name]


def list_timer_styles():
    """列出所有可用的计时器样式。"""
    print("可用的计时器样式:")
    r = []
    for style_name in TIMER_STYLES:
        r += [style_name]
        print(f"- {style_name}")
    return r


def register_timer_style(style_name, timer_class):
    """注册新的计时器样式。

    Args:
        style_name: 样式名称
        timer_class: 计时器类
    """
    if style_name in TIMER_STYLES:
        print(f"警告: 计时器样式 '{style_name}' 已存在，将被覆盖")

    TIMER_STYLES[style_name] = timer_class
