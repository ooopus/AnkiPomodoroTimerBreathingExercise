from .translator import _

# 呼吸阶段定义

PHASES = [
    {
        "key": "inhale",
        "label": _("吸气"),
        "default_enabled": True,
        "default_duration": 4,
        "default_audio": "",
    },
    {
        "key": "hold_after_inhale",
        "label": _("屏气 (吸气后)"),
        "default_enabled": True,
        "default_duration": 1,
        "default_audio": "",
    },
    {
        "key": "exhale",
        "label": _("呼气"),
        "default_enabled": True,
        "default_duration": 8,
        "default_audio": "",
    },
    {
        "key": "hold_after_exhale",
        "label": _("屏气 (呼气后)"),
        "default_enabled": False,
        "default_duration": 4,
        "default_audio": "",
    },
]


# --- 默认配置值 ---
class Defaults:
    POMODORO_MINUTES = 25
    BREATHING_CYCLES = 30
    SHOW_CIRCULAR_TIMER = True
    CIRCULAR_TIMER_STYLE = "default"
    POMODOROS_BEFORE_LONG_BREAK = 4
    LONG_BREAK_MINUTES = 15
    MAX_BREAK_DURATION = 30

    # 状态栏显示相关常量
    class StatusBar:
        FILLED_TOMATO = "🍅"  # 已完成的番茄
        EMPTY_TOMATO = "⭕"  # 未完成的番茄
        BREAK_WARNING = _("⚠️距离连胜重置还有：")  # 中断警告
        TEXT = f"{FILLED_TOMATO} --:--"
        FORMAT = "ICON_TIME_PROGRESS_WITH_TOTAL_TIME"


# 状态栏显示格式选项
class STATUSBAR_FORMATS:
    NONE = "NONE"  # 不显示
    ICON = "{icon}"  # 仅图标
    COUNTDOWN = "{mins:02d}:{secs:02d}"  # 仅时间
    PROGRESS = "{progress}"  # 仅进度
    ICON_COUNTDOWN_PROGRESS = (
        "{icon} {mins:02d}:{secs:02d} {progress}"  # 图标+时间+进度
    )
    ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME = (
        "{icon} {mins:02d}:{secs:02d} {progress} "
        + _("今日累计使用：")
        + "{daily_mins:02d}:{daily_secs:02d}"
    )  # 全部信息


# 状态栏显示格式选项的显示名称
STATUSBAR_FORMAT_NAMES = {
    "NONE": _(
        "不显示",
    ),
    "ICON": _("仅显示图标"),
    "COUNTDOWN": _("仅显示倒计时"),
    "PROGRESS": _("仅显示进度"),
    "ICON_COUNTDOWN_PROGRESS": _("显示图标+倒计时+进度"),
    "ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME": _("显示图标+倒计时+进度+累计使用时间"),
}
