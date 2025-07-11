import time
from typing import override

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
    QTimer,
    QWidget,
    theme,
)

from ..constants import (
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
)
from ..core.base import BaseCircularTimer


class CircularTimer(BaseCircularTimer):
    """彩虹文字圆形计时器实现，带有动态彩虹文本和进度边框"""

    RAINBOW_CYCLE_DURATION_S = 6.0
    ANIMATION_UPDATE_INTERVAL_MS = 50  # ~20 FPS

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        # 初始化绘制工具
        self._text_pen = QPen()
        self._text_font = QFont("Arial", 20, QFont.Weight.Bold)
        self._shadow_pen = QPen()

        # 定义边框和阴影属性
        self._border_width = 8
        self._shadow_offset = 2

        # 检测主题并设置颜色
        self.update_theme_colors()
        self._update_font_size()

        # 启动动画计时器
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self.update)
        self._animation_timer.start(self.ANIMATION_UPDATE_INTERVAL_MS)

    @override
    def update_theme_colors(self) -> None:
        """根据当前的Anki主题更新所有颜色"""
        self._dark_mode = theme.theme_manager.night_mode
        if self._dark_mode:
            # Dark Mode Colors
            self._bg_start_color = BG_COLOR_START_DARK
            self._bg_end_color = BG_COLOR_END_DARK
            self._progress_start_color = PROGRESS_COLOR_START_DARK
            self._progress_end_color = PROGRESS_COLOR_END_DARK
            self._shadow_color = SHADOW_COLOR_DARK
            self._track_color = QColor(255, 255, 255, 40)
        else:
            # Light Mode Colors
            self._bg_start_color = BG_COLOR_START_LIGHT
            self._bg_end_color = BG_COLOR_END_LIGHT
            self._progress_start_color = PROGRESS_COLOR_START_LIGHT
            self._progress_end_color = PROGRESS_COLOR_END_LIGHT
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

    @override
    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        """窗口大小改变事件"""
        self._update_font_size()
        super().resizeEvent(a0)

    @override
    def paintEvent(self, a0: QPaintEvent | None) -> None:
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
        painter.setBrush(QBrush(bg_gradient))
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

        # 4b. 使用彩虹色绘制主文本
        current_time = time.time()
        hue = (
            current_time % self.RAINBOW_CYCLE_DURATION_S
        ) / self.RAINBOW_CYCLE_DURATION_S
        rainbow_color = QColor.fromHsvF(hue, 1.0, 1.0)
        self._text_pen.setColor(rainbow_color)
        painter.setPen(self._text_pen)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self._remaining_time)
