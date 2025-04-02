# 呼吸阶段定义
PHASES = [
    {
        "key": "inhale",
        "label": "吸气",
        "default_duration": 4,
        "default_enabled": True,
        "anim_phase": "INHALE",
    },
    {
        "key": "hold",
        "label": "屏住",
        "default_duration": 4,
        "default_enabled": False,
        "anim_phase": "HOLD",
    },
    {
        "key": "exhale",
        "label": "呼气",
        "default_duration": 6,
        "default_enabled": True,
        "anim_phase": "EXHALE",
    },
]

# 默认配置
DEFAULT_POMODORO_MINUTES = 25
DEFAULT_BREATHING_CYCLES = 30
DEFAULT_SHOW_STATUSBAR_TIMER = True
DEFAULT_SHOW_CIRCULAR_TIMER = True
DEFAULT_POMODOROS_BEFORE_LONG_BREAK = 4  # 默认完成4个番茄钟后提示长休息
DEFAULT_LONG_BREAK_MINUTES = 15  # 默认长休息时间15分钟

# 状态栏显示相关常量
STATUSBAR_FILLED_TOMATO = "🍅"  # 已完成的番茄
STATUSBAR_EMPTY_TOMATO = "⭕"   # 未完成的番茄
STATUSBAR_DEFAULT_TEXT = f"{STATUSBAR_FILLED_TOMATO} --:--"
STATUSBAR_FORMAT = "{icon} {mins:02d}:{secs:02d} {progress}"  # 添加进度显示
