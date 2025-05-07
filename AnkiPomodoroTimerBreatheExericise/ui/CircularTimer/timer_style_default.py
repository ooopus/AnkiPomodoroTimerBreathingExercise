from aqt import (
    QBrush,
    QFont,
    QLinearGradient,
    QPainter,
    QPaintEvent,
    QPen,
    QPointF,
    QRadialGradient,
    QRectF,
    QResizeEvent,
    Qt,
    QWidget,
    theme,
)

from .constants import (
    BG_COLOR_END_DARK,
    BG_COLOR_END_LIGHT,
    BG_COLOR_START_DARK,
    BG_COLOR_START_LIGHT,
    PROGRESS_COLOR_END_DARK,
    PROGRESS_COLOR_END_LIGHT,
    PROGRESS_COLOR_START_DARK,
    PROGRESS_COLOR_START_LIGHT,
    SHADOW_COLOR_DARK,
    SHADOW_COLOR_LIGHT,
    TEXT_COLOR_END_DARK,
    TEXT_COLOR_END_LIGHT,
    TEXT_COLOR_START_DARK,
    TEXT_COLOR_START_LIGHT,
)


# --- 默认圆形计时器 ---
class CircularTimer(QWidget):
    """默认圆形计时器实现，使用渐变文本。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(50, 50)
        self._progress = 0.0
        self._remaining_time = "00:00"

        # --- 检测主题并选择颜色 ---
        self._dark_mode = theme.theme_manager.night_mode
        self._load_colors()

        # --- 预创建绘图资源 ---
        self._bg_pen = QPen()
        self._bg_pen.setCapStyle(Qt.PenCapStyle.FlatCap)

        self._progress_pen = QPen()
        self._progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        # 文本笔 - 颜色来自画刷渐变
        self._text_pen = QPen()
        self._shadow_pen = QPen(self._shadow_color)  # 阴影颜色根据主题固定
        self._shadow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        # 画刷（渐变稍后定义/更新）
        self._bg_brush = QBrush()
        self._progress_brush = QBrush()
        self._text_brush = QBrush()

        # 字体
        self._text_font = QFont()
        self._text_font.setBold(True)

        # 初始更新大小相关资源
        self._update_dynamic_resources()

    def _load_colors(self):
        """根据检测到的主题加载颜色变量。"""
        if self._dark_mode:
            self._bg_start_color = BG_COLOR_START_DARK
            self._bg_end_color = BG_COLOR_END_DARK
            self._progress_start_color = PROGRESS_COLOR_START_DARK
            self._progress_end_color = PROGRESS_COLOR_END_DARK
            self._text_start_color = TEXT_COLOR_START_DARK
            self._text_end_color = TEXT_COLOR_END_DARK
            self._shadow_color = SHADOW_COLOR_DARK
        else:
            self._bg_start_color = BG_COLOR_START_LIGHT
            self._bg_end_color = BG_COLOR_END_LIGHT
            self._progress_start_color = PROGRESS_COLOR_START_LIGHT
            self._progress_end_color = PROGRESS_COLOR_END_LIGHT
            self._text_start_color = TEXT_COLOR_START_LIGHT
            self._text_end_color = TEXT_COLOR_END_LIGHT
            self._shadow_color = SHADOW_COLOR_LIGHT

        # 直接更新笔颜色
        if hasattr(self, "_shadow_pen"):  # 检查笔是否存在（在初始化期间）
            self._shadow_pen.setColor(self._shadow_color)

    def set_progress(self, current_seconds, total_seconds):
        """设置计时器的进度。"""
        if total_seconds > 0:
            self._progress = max(0.0, min(1.0, 1.0 - (current_seconds / total_seconds)))
        else:
            self._progress = 0.0

        display_seconds = max(0, current_seconds)
        mins, secs = divmod(display_seconds, 60)
        new_time = f"{mins:02d}:{secs:02d}"

        if (
            self._progress != getattr(self, "_last_progress", -1)
            or self._remaining_time != new_time
        ):
            self._remaining_time = new_time
            self._last_progress = self._progress
            self.update()

    def _update_dynamic_resources(self):
        """更新依赖于小部件大小的资源。"""
        width = self.width()
        height = self.height()
        size = min(width, height)

        self._pen_width = max(2, int(size * 0.06))
        self._padding = self._pen_width / 2 + max(1, int(size * 0.04))
        self._shadow_offset = max(1, int(size * 0.02))

        self._bg_pen.setWidth(self._pen_width)
        self._progress_pen.setWidth(self._pen_width)

        self._text_pen.setWidth(1)
        self._shadow_pen.setWidth(1)

        font_size = max(6, int(size * 0.18))
        self._text_font.setPointSize(font_size)

    def update_theme(self):
        """更新计时器的主题。总是由Anki主题变化引起。"""
        self._dark_mode = theme.theme_manager.night_mode
        self._load_colors()
        self.update()

    def resizeEvent(self, event: QResizeEvent):
        """处理小部件调整大小。"""
        super().resizeEvent(event)
        self._update_dynamic_resources()

    def paintEvent(self, event: QPaintEvent):
        """使用主题适当的颜色绘制圆形计时器。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        center = QPointF(width / 2.0, height / 2.0)
        radius = min(width, height) / 2.0 - self._padding

        rect = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)

        if not rect.isValid() or radius <= 0:
            return

        # --- 1. 绘制背景 ---
        bg_gradient = QRadialGradient(center, radius + self._pen_width)
        bg_gradient.setColorAt(0.8, self._bg_start_color)
        bg_gradient.setColorAt(1.0, self._bg_end_color)
        self._bg_brush = QBrush(bg_gradient)

        self._bg_pen.setBrush(self._bg_brush)
        painter.setPen(self._bg_pen)
        painter.drawEllipse(rect)

        # --- 2. 绘制进度弧 ---
        if self._progress > 0:
            progress_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            progress_gradient.setColorAt(0, self._progress_start_color)
            progress_gradient.setColorAt(1, self._progress_end_color)
            self._progress_brush = QBrush(progress_gradient)

            self._progress_pen.setBrush(self._progress_brush)
            painter.setPen(self._progress_pen)

            start_angle = 90 * 16
            span_angle = -int(self._progress * 360 * 16)
            painter.drawArc(rect, start_angle, span_angle)

        # --- 3. 绘制剩余时间文本 ---
        painter.setFont(self._text_font)

        # 3a. 绘制阴影文本
        shadow_rect = rect.adjusted(
            self._shadow_offset,
            self._shadow_offset,
            self._shadow_offset,
            self._shadow_offset,
        )
        painter.setPen(self._shadow_pen)
        painter.drawText(
            shadow_rect, Qt.AlignmentFlag.AlignCenter, self._remaining_time
        )

        # 3b. 使用渐变绘制主文本
        text_gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        text_gradient.setColorAt(0, self._text_start_color)
        text_gradient.setColorAt(1, self._text_end_color)
        self._text_brush = QBrush(text_gradient)

        self._text_pen.setBrush(self._text_brush)
        painter.setPen(self._text_pen)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._remaining_time)
