from typing import TypedDict


class ConfigDict(TypedDict, total=False):
    """类型定义：配置字典类型"""

    pomodoro_minutes: int
    breathing_cycles: int
    enabled: bool
    show_circular_timer: bool
    circular_timer_style: str
    completed_pomodoros: int
    daily_pomodoro_seconds: int
    pomodoros_before_long_break: int
    long_break_minutes: int
    max_break_duration: int
    statusbar_format: str
    last_pomodoro_time: float
    last_date: str
    # 呼吸阶段配置
    inhale_duration: int
    inhale_enabled: bool
    hold_duration: int
    hold_enabled: bool
    exhale_duration: int
    exhale_enabled: bool
    exhale_audio: str
    hold_after_inhale_duration: int
    hold_after_inhale_enabled: bool
    hold_after_inhale_audio: str
    hold_after_exhale_duration: int
    hold_after_exhale_enabled: bool
    hold_after_exhale_audio: str
    work_across_decks: bool
