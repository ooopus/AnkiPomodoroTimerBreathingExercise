from abc import ABCMeta, abstractmethod

from aqt import QWidget


# Combine the metaclasses of QWidget and ABCMeta to resolve the conflict.
class QWidgetABCMeta(ABCMeta, type(QWidget)):
    pass


class BaseCircularTimer(QWidget, metaclass=QWidgetABCMeta):
    """
    圆形计时器的抽象基类。
    所有计时器样式都必须继承此类并实现抽象方法。
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumSize(50, 50)
        self._progress = 0.0
        self._remaining_time = "00:00"

    def set_progress(self, current: float, total: float) -> None:
        """
        设置计时器进度。

        Args:
            current: 当前值（例如剩余秒数）
            total: 总值
        """
        self._progress = current / total if total > 0 else 0
        self._remaining_time = self._format_time(current)
        self.update()

    @abstractmethod
    def update_theme_colors(self) -> None:
        """
        根据当前主题更新组件颜色。
        当Anki主题改变时应调用此方法。
        """
        pass

    def get_progress(self) -> float:
        """获取当前进度（0.0-1.0）"""
        return self._progress

    def get_remaining_time(self) -> str:
        """获取格式化的剩余时间字符串"""
        return self._remaining_time

    def _format_time(self, seconds: float) -> str:
        """格式化时间为 MM:SS 格式"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"


# 类型别名
type TimerClass = type[BaseCircularTimer]
