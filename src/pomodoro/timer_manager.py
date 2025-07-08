from collections.abc import Callable
from enum import Enum, auto

from aqt import QTimer, QWidget


class TimerState(Enum):
    """番茄钟计时器的状态枚举"""

    IDLE = auto()  # 空闲状态
    WORKING = auto()  # 工作状态
    LONG_BREAK = auto()  # 长休息
    MAX_BREAK_COUNTDOWN = auto()  # 最长休息时间倒计时


class TimerManager(QWidget):
    """负责管理番茄工作法的所有计时器（工作和休息）。"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.state = TimerState.IDLE
        self.remaining_seconds = 0
        self.total_seconds = 0

        # Callbacks
        self.on_tick: Callable[[], None] | None = None
        self.on_finish: Callable[[TimerState], None] | None = None

        # Main timer for both work and break
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self, minutes: float, state: TimerState):
        """启动计时器"""
        if minutes <= 0:
            return

        self.total_seconds = int(minutes * 60)
        self.remaining_seconds = self.total_seconds
        self.state = state
        self._timer.start(1000)  # 每秒触发一次
        if self.on_tick:
            self.on_tick()  # 立即触发一次以更新UI

    def stop(self):
        """停止计时器"""
        self._timer.stop()
        self.state = TimerState.IDLE
        if self.on_tick:
            self.on_tick()  # 更新UI到空闲状态

    def _tick(self):
        """处理计时器的每个“滴答”"""
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            if self.on_tick:
                self.on_tick()
        else:
            self._timer.stop()
            original_state = self.state
            self.state = TimerState.IDLE
            if self.on_finish:
                self.on_finish(original_state)  # 传递刚刚完成的状态
