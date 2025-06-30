from dataclasses import dataclass
from enum import Enum

from .translator import _


class TimerPosition(str, Enum):
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


class CircularTimerStyle(str, Enum):
    DEFAULT = "default"
    RAINBOW = "rainbow"


class PomodoroPhase(Enum):
    POMODORO = "pomodoro"
    LONG_BREAK = "long_break"


class BreathingPhase(str, Enum):
    INHALE = "inhale"
    HOLD_AFTER_INHALE = "hold_after_inhale"
    EXHALE = "exhale"
    HOLD_AFTER_EXHALE = "hold_after_exhale"


@dataclass
class BreathingPhaseInfo:
    key: BreathingPhase
    label: str
    default_enabled: bool
    default_duration: int
    default_audio: str = ""


# 呼吸阶段定义
PHASES: tuple[BreathingPhaseInfo, ...] = (
    BreathingPhaseInfo(
        key=BreathingPhase.INHALE,
        label=_("吸气"),
        default_enabled=True,
        default_duration=4,
    ),
    BreathingPhaseInfo(
        key=BreathingPhase.HOLD_AFTER_INHALE,
        label=_("屏气 (吸气后)"),
        default_enabled=True,
        default_duration=1,
    ),
    BreathingPhaseInfo(
        key=BreathingPhase.EXHALE,
        label=_("呼气"),
        default_enabled=True,
        default_duration=8,
    ),
    BreathingPhaseInfo(
        key=BreathingPhase.HOLD_AFTER_EXHALE,
        label=_("屏气 (呼气后)"),
        default_enabled=False,
        default_duration=4,
    ),
)


# 状态栏显示格式选项
class StatusBarFormat(str, Enum):
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

    @property
    def display_name(self) -> str:
        """返回此格式的本地化显示名称。"""
        return STATUSBAR_FORMAT_NAMES.get(self, "")


# --- 默认配置值 ---
class AnkiStates:
    REVIEW = "review"
    DECK_BROWSER = "deckBrowser"


class Defaults:
    POMODORO_MINUTES = 25

    BREATHING_CYCLES = 30
    SHOW_CIRCULAR_TIMER = True
    CIRCULAR_TIMER_STYLE = CircularTimerStyle.DEFAULT
    POMODOROS_BEFORE_LONG_BREAK = 4
    LONG_BREAK_MINUTES = 15
    MAX_BREAK_DURATION = 30

    # 状态栏显示相关常量
    class StatusBar:
        FILLED_TOMATO = "🍅"  # 已完成的番茄
        EMPTY_TOMATO = "⭕"  # 未完成的番茄
        BREAK_WARNING = _("⏳休息中：")  # 中断警告
        MAX_BREAK_WARNING = _("⚠️休息上限：")  # 最长休息时间警告
        TEXT = f"{FILLED_TOMATO} --:--"
        FORMAT = StatusBarFormat.ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME


# 状态栏显示格式选项的显示名称
STATUSBAR_FORMAT_NAMES = {
    StatusBarFormat.NONE: _("不显示"),
    StatusBarFormat.ICON: _("仅显示图标"),
    StatusBarFormat.COUNTDOWN: _("仅显示倒计时"),
    StatusBarFormat.PROGRESS: _("仅显示进度"),
    StatusBarFormat.ICON_COUNTDOWN_PROGRESS: _("显示图标+倒计时+进度"),
    StatusBarFormat.ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME: _(
        "显示图标+倒计时+进度+累计使用时间"
    ),
}

TIMER_POSITION_NAMES = {
    TimerPosition.TOP_LEFT: _("左上角"),
    TimerPosition.TOP_RIGHT: _("右上角"),
    TimerPosition.BOTTOM_LEFT: _("左下角"),
    TimerPosition.BOTTOM_RIGHT: _("右下角"),
}
