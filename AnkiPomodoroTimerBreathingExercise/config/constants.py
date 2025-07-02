from typing import Literal

from ..translator import _
from .enums import BreathingPhase, CircularTimerStyle, StatusBarFormat
from .languages import LanguageCode

# Defines the audio filenames for different languages and breathing phases.
# This structure makes it easy to add new languages or audio files.
AUDIO_FILENAMES = {
    LanguageCode.ENGLISH: {
        BreathingPhase.INHALE: "inhale.opus",
        BreathingPhase.EXHALE: "exhale.opus",
    },
    LanguageCode.GERMAN: {
        BreathingPhase.INHALE: "einatmen.opus",
        BreathingPhase.EXHALE: "ausatmen.opus",
    },
    LanguageCode.CHINESE_SIMPLIFIED: {
        BreathingPhase.INHALE: "吸气.opus",
        BreathingPhase.EXHALE: "呼气.opus",
    },
}


from enum import Enum


class AnkiStates(Enum):
    STARTUP = "startup"
    DECK_BROWSER = "deckBrowser"
    OVERVIEW = "overview"
    REVIEW = "review"
    RESET_REQUIRED = "resetRequired"
    PROFILE_MANAGER = "profileManager"


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
