from .translator import _

# 呼吸阶段定义

PHASES = [
    {
        "key": "inhale",
        "label": _("吸气"),
        "default_duration": 4,
        "default_enabled": True,
        "anim_phase": "INHALE",
    },
    {
        "key": "hold",
        "label": _("屏住"),
        "default_duration": 4,
        "default_enabled": False,
        "anim_phase": "HOLD",
    },
    {
        "key": "exhale",
        "label": _("呼气"),
        "default_duration": 6,
        "default_enabled": True,
        "anim_phase": "EXHALE",
    },
]

# 默认配置
DEFAULT_POMODORO_MINUTES = 25
DEFAULT_BREATHING_CYCLES = 30
# 状态栏显示格式已迁移到STATUSBAR_FORMATS类
# 使用STATUSBAR_FORMATS.NONE表示不显示状态栏
DEFAULT_SHOW_CIRCULAR_TIMER = True
DEFAULT_POMODOROS_BEFORE_LONG_BREAK = 4  # 默认完成4个番茄钟后提示长休息
DEFAULT_LONG_BREAK_MINUTES = 15  # 默认长休息时间15分钟
DEFAULT_MAX_BREAK_DURATION = 30  # 默认最大间隔时间30分钟
DEFAULT_STATUSBAR_FORMAT = "ICON_TIME_PROGRESS_WITH_TOTAL_TIME"  # 默认状态栏显示格式

# 状态栏显示相关常量
STATUSBAR_FILLED_TOMATO = "🍅"  # 已完成的番茄
STATUSBAR_EMPTY_TOMATO = "⭕"  # 未完成的番茄
STATUSBAR_BREAK_WARNING = _("⚠️距离连胜重置还有：" ) # 中断警告
STATUSBAR_DEFAULT_TEXT = f"{STATUSBAR_FILLED_TOMATO} --:--"
STATUSBAR_FORMAT = "{icon} {mins:02d}:{secs:02d} {progress}"  # 番茄状态显示格式


# 状态栏显示格式选项
class STATUSBAR_FORMATS:
    NONE = "NONE"  # 不显示
    ICON = "{icon}"  # 仅图标
    COUNTDOWN = "{mins:02d}:{secs:02d}"  # 仅时间
    PROGRESS = "{progress}"  # 仅进度
    ICON_COUNTDOWN_PROGRESS = (
        "{icon} {mins:02d}:{secs:02d} {progress}"  # 图标+时间+进度
    )
    ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME = "{icon} {mins:02d}:{secs:02d} {progress} " + _("累计使用：") + "{daily_mins:02d}:{daily_secs:02d}"  # 全部信息

# 状态栏显示格式选项的显示名称
STATUSBAR_FORMAT_NAMES = {
    "NONE": _("不显示",),
    "ICON": _("仅显示图标"),
    "COUNTDOWN": _("仅显示倒计时"),
    "PROGRESS": _("仅显示进度"),
    "ICON_COUNTDOWN_PROGRESS": _("显示图标+倒计时+进度"),
    "ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME": _("显示图标+倒计时+进度+累计使用时间"),
}
