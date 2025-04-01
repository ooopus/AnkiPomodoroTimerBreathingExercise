# 呼吸阶段定义
PHASES = [
    {"key": "inhale", "label": "吸气", "default_duration": 4, "default_enabled": True, "anim_phase": "INHALE"},
    {"key": "hold", "label": "屏住", "default_duration": 4, "default_enabled": False, "anim_phase": "HOLD"},
    {"key": "exhale", "label": "呼气", "default_duration": 6, "default_enabled": True, "anim_phase": "EXHALE"}
]

# 默认配置
DEFAULT_POMODORO_MINUTES = 25
DEFAULT_BREATHING_CYCLES = 30
DEFAULT_SHOW_STATUSBAR_TIMER = True
DEFAULT_SHOW_CIRCULAR_TIMER = True


# 状态栏显示相关常量
STATUSBAR_ICON = "🍅"
STATUSBAR_DEFAULT_TEXT = f"{STATUSBAR_ICON} --:--"
STATUSBAR_FORMAT = "{icon} {mins:02d}:{secs:02d}"