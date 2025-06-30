from aqt import QColor

# Define all potential colors here

# --- Light Mode Colors (Improved) ---
# 使用更柔和的灰色调，增加透明度以更好地融入背景
BG_COLOR_START_LIGHT = QColor(240, 240, 240, 220)
BG_COLOR_END_LIGHT = QColor(225, 225, 225, 230)

# 使用更鲜明且现代的蓝色调
PROGRESS_COLOR_START_LIGHT = QColor(45, 156, 219)
PROGRESS_COLOR_END_LIGHT = QColor(33, 120, 180)

# 使用深灰色以确保在浅色背景下的可读性
TEXT_COLOR_START_LIGHT = QColor(40, 40, 40)
TEXT_COLOR_END_LIGHT = QColor(60, 60, 60)

# 阴影颜色稍微调淡
SHADOW_COLOR_LIGHT = QColor(0, 0, 0, 35)


# --- Dark Mode Colors (Night Mode) ---
# 深色模式的颜色保持不变，因为它们通常效果不错
BG_COLOR_START_DARK = QColor(70, 70, 80, 200)
BG_COLOR_END_DARK = QColor(50, 50, 60, 220)

PROGRESS_COLOR_START_DARK = QColor(20, 180, 255)
PROGRESS_COLOR_END_DARK = QColor(10, 130, 220)

TEXT_COLOR_START_DARK = QColor(220, 220, 220)
TEXT_COLOR_END_DARK = QColor(240, 240, 240)

SHADOW_COLOR_DARK = QColor(0, 0, 0, 70)
