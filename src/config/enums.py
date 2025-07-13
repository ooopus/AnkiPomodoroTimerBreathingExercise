import dataclasses
from enum import Enum

from ..translator import _


class TimerPosition(str, Enum):
    _display_name: str

    def __new__(cls, value: str, display_name: str):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._display_name = display_name
        return obj

    @property
    def display_name(self) -> str:
        return self._display_name

    # Define members with their display names
    TOP_LEFT = "top_left", _("左上角")
    TOP_RIGHT = "top_right", _("右上角")
    BOTTOM_LEFT = "bottom_left", _("左下角")
    BOTTOM_RIGHT = "bottom_right", _("右下角")
    LAST_USED = "last_used", _("上次使用的位置")


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


@dataclasses.dataclass
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
        default_duration=6,
    ),
    BreathingPhaseInfo(
        key=BreathingPhase.HOLD_AFTER_EXHALE,
        label=_("屏气 (呼气后)"),
        default_enabled=False,
        default_duration=4,
    ),
)


class StatusBarFormat(str, Enum):
    _display_name: str

    def __new__(cls, value: str, display_name: str):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._display_name = display_name
        return obj

    @property
    def display_name(self) -> str:
        return self._display_name

    # Define members with their display names
    NONE = "NONE", _("不显示")
    ICON = "{icon}", _("仅显示图标")
    COUNTDOWN = "{mins:02d}:{secs:02d}", _("仅显示倒计时")
    PROGRESS = "{progress}", _("仅显示进度")
    ICON_COUNTDOWN_PROGRESS = (
        "{icon} {mins:02d}:{secs:02d} {progress}",
        _("显示图标+倒计时+进度"),
    )
    ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME = (
        "{icon} {mins:02d}:{secs:02d} {progress}  🕒 {daily_hours}h {daily_mins}m",
        _("显示图标+倒计时+进度+累计使用时间"),
    )
