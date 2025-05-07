from ..state import get_app_state
from .CircularTimer.timer_common import setup_circular_timer as setup_timer_common
from .CircularTimer.timer_factory import get_timer_class

# --- 设置函数 ---


def setupCircularTimer(force_new=False):
    """创建或显示独立的计时器窗口，根据配置选择合适的样式。

    Args:
        force_new: 是否强制创建新窗口

    Returns:
        计时器小部件实例
    """
    # 从配置中获取计时器样式
    config = get_app_state().config
    circular_timer_style = config.get("circular_timer_style", "default")

    # 获取对应的计时器类
    timer_class = get_timer_class(circular_timer_style)

    # 使用通用的setup函数创建计时器
    return setup_timer_common(timer_class, force_new)
