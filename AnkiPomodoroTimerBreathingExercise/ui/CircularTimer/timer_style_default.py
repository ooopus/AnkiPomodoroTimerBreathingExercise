from typing import Optional

from aqt import (
    QBrush,
    QColor,
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
from .timer_base import BaseCircularTimer


class CircularTimer(BaseCircularTimer):
    """默认圆形计时器实现，使用渐变文本和进度边框"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # 初始化绘制工具
        self._bg_brush = QBrush()
        self._text_pen = QPen()
        self._text_font = QFont("Arial", 20, QFont.Weight.Bold)
        self._shadow_pen = QPen()

        # 定义边框和阴影属性
        self._border_width = 8
        self._shadow_offset = 2

        # 检测主题并设置颜色
        self.update_theme_colors()
        self._update_font_size()

    def set_progress(self, current: float, total: float) -> None:
        """设置计时器进度"""
        self._progress = current / total if total > 0 else 0
        self._remaining_time = self._format_time(current)
        self.update()

    def update_theme_colors(self) -> None:
        """根据当前的Anki主题更新所有颜色"""
        self._dark_mode = theme.theme_manager.night_mode
        if self._dark_mode:
            # Dark Mode Colors
            self._bg_start_color = BG_COLOR_START_DARK
            self._bg_end_color = BG_COLOR_END_DARK
            self._progress_start_color = PROGRESS_COLOR_START_DARK
            self._progress_end_color = PROGRESS_COLOR_END_DARK
            self._text_start_color = TEXT_COLOR_START_DARK
            self._text_end_color = TEXT_COLOR_END_DARK
            self._shadow_color = SHADOW_COLOR_DARK
            self._track_color = QColor(255, 255, 255, 40)
        else:
            # Light Mode Colors
            self._bg_start_color = BG_COLOR_START_LIGHT
            self._bg_end_color = BG_COLOR_END_LIGHT
            self._progress_start_color = PROGRESS_COLOR_START_LIGHT
            self._progress_end_color = PROGRESS_COLOR_END_LIGHT
            self._text_start_color = TEXT_COLOR_START_LIGHT
            self._text_end_color = TEXT_COLOR_END_LIGHT
            self._shadow_color = SHADOW_COLOR_LIGHT
            self._track_color = QColor(0, 0, 0, 20)

        # 更新阴影画笔颜色
        self._shadow_pen.setColor(self._shadow_color)
        self.update()

    def _update_font_size(self):
        """根据窗口大小动态调整字体大小"""
        inner_dim = min(self.width(), self.height()) - (self._border_width * 2)
        font_size = max(10, inner_dim * 0.25)
        self._text_font.setPointSizeF(font_size)

    def resizeEvent(self, event: Optional[QResizeEvent]) -> None:
        """窗口大小改变事件"""
        self._update_font_size()
        super().resizeEvent(event)

    def paintEvent(self, event: Optional[QPaintEvent]) -> None:
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        offset = self._border_width // 2
        rect = self.rect().adjusted(offset, offset, -offset, -offset)
        rectF = QRectF(rect)

        # 1. 绘制背景圆
        bg_gradient = QRadialGradient(QPointF(rect.center()), rect.width() / 2)
        bg_gradient.setColorAt(0, self._bg_start_color)
        bg_gradient.setColorAt(1, self._bg_end_color)
        self._bg_brush = QBrush(bg_gradient)
        painter.setBrush(self._bg_brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rectF.adjusted(offset, offset, -offset, -offset))

        # 2. 绘制进度条轨道
        painter.setBrush(Qt.BrushStyle.NoBrush)
        track_pen = QPen(
            self._track_color,
            self._border_width,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        )
        painter.setPen(track_pen)
        painter.drawArc(rectF, 0, 360 * 16)

        # 3. 绘制进度弧
        if self._progress > 0:
            progress_gradient = QLinearGradient(
                QPointF(rectF.topLeft()), QPointF(rectF.bottomRight())
            )
            progress_gradient.setColorAt(0, self._progress_start_color)
            progress_gradient.setColorAt(1, self._progress_end_color)

            progress_pen = QPen(
                QBrush(progress_gradient),
                self._border_width,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
            painter.setPen(progress_pen)

            start_angle = 90 * 16
            span_angle = -int(self._progress * 360 * 16)
            painter.drawArc(rectF, start_angle, span_angle)

        # 4. 绘制剩余时间文本
        text_rect = rectF.adjusted(
            self._border_width,
            self._border_width,
            -self._border_width,
            -self._border_width,
        )
        painter.setFont(self._text_font)

        # 4a. 绘制阴影文本
        shadow_rectF = QRectF(text_rect).translated(
            self._shadow_offset, self._shadow_offset
        )
        painter.setPen(self._shadow_pen)
        painter.drawText(
            shadow_rectF, Qt.AlignmentFlag.AlignCenter, self._remaining_time
        )

        # 4b. 使用渐变绘制主文本
        text_gradient = QLinearGradient(
            QPointF(text_rect.topLeft()), QPointF(text_rect.bottomLeft())
        )
        text_gradient.setColorAt(0, self._text_start_color)
        text_gradient.setColorAt(1, self._text_end_color)
        self._text_pen.setBrush(QBrush(text_gradient))
        painter.setPen(self._text_pen)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self._remaining_time)
