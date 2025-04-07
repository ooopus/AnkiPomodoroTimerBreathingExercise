"""常量定义"""

# 日志设置
DEBUG_MODE = False  # 设为True开启调试输出，False关闭

def log(message):
    """日志函数，仅在DEBUG_MODE=True时输出信息"""
    if DEBUG_MODE:
        print(f"[番茄钟] {message}")

# 状态栏格式
STATUSBAR_ICON = "🍅"
STATUSBAR_PAUSE_ICON = "⏸️"
STATUSBAR_FORMAT = "{icon} {mins:02d}:{secs:02d}"
STATUSBAR_PAUSED_FORMAT = "{icon} {pause_icon} {mins:02d}:{secs:02d}"
STATUSBAR_DEFAULT_TEXT = f"{STATUSBAR_ICON} 00:00"

# 可选的状态栏图标列表
AVAILABLE_STATUSBAR_ICONS = [
    # 食物和饮品类
    "🍅", "🍎", "🍊", "🍋", "🍏", "🍐", "🍓", "🥕", "🌶️", "🍈", "🍉", "🍇", "🍍", "🍒", 
    "🥦", "🍆", "🥑", "🥝", "🍑", "🍕", "🍔", "🍦", "🍧", "🍩", "🍪", "🍰", "🍫", "🥞",
    "🥐", "🥨", "🧀", "🍯", "🍭", "🍬", "🍡", "🥟", "🍚", "🦐", "🦀",
    
    # 自然和植物类
    "🌷", "🌲", "🪴", "🍀", "🌴", "🍄", "☘️", "🌼", "🌸", "🌻", "🌹", "🌵", "🌿", "🌱", 
    "🍃", "🍂", "🍁", "🌾", "🌺", "🥀", "🌳", "🌊",
    
    # 动物类
    "🐬", "🐟", "🐳", "🐋", "🐸", "🐢", "🐠", "🦋", "🐎", "🦒", "🐏", "🐃", "🐂", "🐗", 
    "🐒", "🦍", "🐶", "🐧", "🦜", "🦆", "🦅", "🕊️", "🦁", "🐯", "🐺", "🦊", "🐱", 
    "🐰", "🐨", "🐼", "🐻", "🐷", "🐮", "🐔", "🦢", "🐇", "🦘", "🐿️", "🦇", "🦉", "🦚",
    
    # 表情和心形
    "😊", "😃", "😄", "😁", "😅", "😂", "🤣", "🥲", "😇", "😉", "😌", "😍", "🥰", "😘",
    "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔", "❤️‍🔥", "❤️‍🩹", "❣️", "💕", 
    "💞", "💓", "💗", "💖", "💘", "💝", "💟", "♥️",
    
    # 活动和运动
    "🏃", "🧘", "🏄", "🏊", "🤽", "🧗", "🚴", "🚵", "🏋️", "⛹️", "🤸", "🤺", "🤾", "🏌️",
    "⚽", "🏀", "🏈", "⚾", "🎯", "🎮", "🎲", "🎭", "🎬", "🎨", "🎧",
    
    # 学习和工作
    "📚", "📝", "✏️", "🎓", "💻", "⌨️", "🖥️", "📱", "🔍", "💡", "🎯", "📊", "📈", "📉",
    "🧮", "🔬", "🔭", "📡", "🗂️", "📋", "✉️", "📧", "📨", "🖋️", "📎",
    
    # 天气和自然现象
    "☀️", "🌤️", "⛅", "☁️", "🌦️", "🌧️", "⛈️", "🌩️", "🌨️", "❄️", "☃️", "⚡", "🌈",
    "🌪️", "🌫️", "💧", "💦", "☔", "🌍","🌑", "🌕", "⭐", "🌟", "✨",
    
    # 交通工具
    "🚗", "🚕", "🚙", "🚌", "🚎", "🏎️", "🚓", "🚑", "🚒", "🚚", "🚛", "🚜", "🛵", "🏍️",
    "🚲", "🚂", "🚆", "✈️", "🛫", "🚀", "🛸", "🚁", "⛵", "🚢",
    
    # 音乐和艺术
    "🎵", "🎶", "🎹", "🎸", "🎺", "🎻", "🥁", "🎨", "🎭", "🎬", "🎧", "🎤", "🎙️",
    
    # 时间和计时
    "⏰", "⌚", "⏱️", "⏲️", "🕰️", "📅", "📆", "⌛","🔔", "🔊", "📢",
    
    # 其他符号和物品
    "🔑", "🔒", "🎈", "🎀", "🎁", "🎊", "🎉", "📌", "📍", "🔍", "🔎", "💭", "💫", "💤",
    "🔱", "⚜️", "🏆", "🥇", "🥈", "🥉", "💎", "🔮", "🎪", "🎯", "🎲", "🧩", "🪄"
    
]

# 默认番茄钟时长（分钟）
DEFAULT_POMODORO_MINUTES = 25

# 默认休息时长（分钟）
DEFAULT_REST_MINUTES = 5

# 默认显示状态栏计时器
DEFAULT_SHOW_STATUSBAR_TIMER = True

# 默认音效设置
DEFAULT_SOUND_EFFECT_ENABLED = False
DEFAULT_SOUND_EFFECT_FILE = "叮.mp3"

# 可用音效文件列表
AVAILABLE_SOUND_EFFECTS = ["叮.mp3", "钟声.mp3", "风铃.mp3", "翻书.mp3", "翻书_长.mp3"]

# 默认冥想训练列表
DEFAULT_MEDITATION_SESSIONS = [
    {
        "name": "20分钟躺平冥想重启大脑",
        "url": "https://www.bilibili.com/video/BV1nm4y1t7t5?spm_id_from=333.788.videopod.sections&vd_source=37882f434a2ecf27b36fd69af34eb9a4",
        "audio_path": "",
        "emoji": "🧘"
    },
    {
        "name": "10分钟回复脑力终结拖延症",
        "url": "https://www.bilibili.com/video/BV1yP411T77b?spm_id_from=333.788.videopod.sections&vd_source=37882f434a2ecf27b36fd69af34eb9a4",
        "audio_path": "",
        "emoji": "🧠"
    },
    {
        "name": "10分钟提升专注力放下焦虑",
        "url": "https://www.bilibili.com/video/BV16Z4y187za?spm_id_from=333.788.videopod.sections&vd_source=37882f434a2ecf27b36fd69af34eb9a4",
        "audio_path": "",
        "emoji": "😌"
    },
    {
        "name": "10分钟专注训练效率翻倍",
        "url": "https://www.bilibili.com/video/BV1Re4y1r7Y8?spm_id_from=333.788.videopod.sections&vd_source=37882f434a2ecf27b36fd69af34eb9a4",
        "audio_path": "",
        "emoji": "🧠"
    },
    {
        "name": "坚持不到5分钟你就能睡着！15分钟助眠冥想 进入深度睡眠｜失眠焦虑必备",
        "url": "https://www.bilibili.com/video/BV1Sw41187j4?spm_id_from=333.788.videopod.sections&vd_source=37882f434a2ecf27b36fd69af34eb9a4",
        "audio_path": "",
        "emoji": "😴"
    },
    {
        "name": "10分钟缓解一切负面情绪 肯定自我激活最佳状态！｜顺毛冥想",
        "url": "https://www.bilibili.com/video/BV1ip4y1N7pd?spm_id_from=333.788.videopod.sections&vd_source=37882f434a2ecf27b36fd69af34eb9a4",
        "audio_path": "",
        "emoji": "😌"
    },
    {
        "name": "从此告别熬夜，爱上清晨12min冥想+拉伸，一次高效一整天",
        "url": "https://www.bilibili.com/video/BV1tM411u7RS?spm_id_from=333.788.videopod.sections&vd_source=37882f434a2ecf27b36fd69af34eb9a4",
        "audio_path": "",
        "emoji": "⚡"
    },
    {
        "name": "睡前冥想引导 坚持不到5分钟就会睡着，摆脱精神内耗提高白天专注力",
        "url": "https://www.bilibili.com/video/BV13V4y177qs?spm_id_from=333.788.videopod.sections&vd_source=37882f434a2ecf27b36fd69af34eb9a4",
        "audio_path": "",
        "emoji": "😴"
    },
    {
        'name': '情绪不要"忍"13分钟排解负面情绪 自我肯定｜疗愈冥想',
        "url": "https://www.bilibili.com/video/BV1eZ421t78h?spm_id_from=333.788.videopod.sections&vd_source=37882f434a2ecf27b36fd69af34eb9a4",
        "audio_path": "",
        "emoji": "😌"
    },
    {
        "name": "放松解压、缓解焦虑8min 提高专注力开启最佳状态【考前必备】",
        "url": "https://www.bilibili.com/video/BV1gi421U7YY?spm_id_from=333.788.videopod.sections&vd_source=37882f434a2ecf27b36fd69af34eb9a4",
        "audio_path": "",
        "emoji": "😌"
    },
    {
        "name": "7分钟午休冥想，补足精力去除疲劳",
        "url": "https://www.bilibili.com/video/BV1jb42177Jq?spm_id_from=333.788.videopod.sections&vd_source=37882f434a2ecf27b36fd69af34eb9a4",
        "audio_path": "",
        "emoji": "⚡"
    }
]

# 打卡提醒相关常量
DEFAULT_REMINDER_TIME = "20:00"
REMINDER_NOTIFICATION_TITLE = "每日打卡提醒"
REMINDER_NOTIFICATION_MESSAGE = "别忘了完成今天的打卡任务哦！"

# 默认智能提醒设置
DEFAULT_SMART_TIMER_REMINDER = False
DEFAULT_SMART_TIMER_REMINDER_MINUTES = 15
